"""
Analytics Engine Core - High Throughput Telemetry System
========================================================
Implements:
1. Universal Event Schema (Pydantic)
2. Non-blocking Ingestion Controller (FastAPI)
3. Stream Aggregation Worker
4. Dashboard Query Service
"""

import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
import redis.asyncio as aioredis
from redis.exceptions import ResponseError

# Simulated Database Connection Pool (e.g., asyncpg for TimescaleDB)
from typing import Protocol
class AsyncDBPool(Protocol):
    async def execute_many(self, query: str, values: list) -> None: ...
    async def fetch(self, query: str, *args) -> list: ...

logger = logging.getLogger("analytics_engine")


# ============================================================================
# 1. UNIVERSAL EVENT SCHEMA
# ============================================================================

class EventDomain(str, Enum):
    AI_USAGE = "ai_usage"
    DEPLOYMENT = "deployment"
    USER_ACTIVITY = "user_activity"
    SYSTEM_PERF = "system_performance"
    API_REQUESTS = "api_requests"

class TelemetryEvent(BaseModel):
    """
    Strict Universal Schema defining what a standard incoming tracking event must look like.
    """
    model_config = ConfigDict(extra="forbid")

    event_id: UUID = Field(default_factory=uuid4, description="Unique identifier for idempotency")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    domain: EventDomain = Field(..., description="The high-level category of the event")
    event_name: str = Field(..., description="Specific event action (e.g., 'model_generation_failed')")
    
    # Contextual identifiers
    user_id: Optional[str] = Field(None, description="ID of the user performing the action")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    session_id: Optional[str] = Field(None, description="Current user session ID")
    
    # Flexible metadata for specific domains
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Key-value pairs of event context")
    
    # Numeric value for fast aggregations (e.g., latency ms, tokens used)
    metric_value: float = Field(default=1.0, description="Numeric value to aggregate")


# ============================================================================
# 2. THE INGESTION CONTROLLER
# ============================================================================

router = APIRouter(prefix="/api/v1/telemetry", tags=["Analytics"])

# Dependency: A shared Redis connection pool
redis_client = aioredis.Redis(host='localhost', port=6379, decode_responses=True)
TELEMETRY_STREAM = "stream:telemetry:events"

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry(
    event: TelemetryEvent, 
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Highly optimized non-blocking API endpoint.
    Pushes incoming payload directly to Redis Streams to ensure <5ms latency.
    """
    try:
        # Serialize safely with Pydantic
        payload = {"data": event.model_dump_json()}
        
        # Fire to stream asynchronously
        await redis_client.xadd(
            name=TELEMETRY_STREAM,
            fields=payload,
            maxlen=1000000, # Cap stream size to prevent OOM
            approximate=True
        )
        return {"status": "queued", "event_id": str(event.event_id)}
        
    except Exception as e:
        logger.error(f"Failed to queue telemetry: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal ingestion error")


# ============================================================================
# 3. THE AGGREGATION WORKER
# ============================================================================

class AnalyticsAggregationWorker:
    """
    Background process that consumes the event stream, batches data,
    updates real-time fast-read caches, and flushes to the Time-Series DB.
    """
    def __init__(self, redis_conn: aioredis.Redis, tsdb_pool: AsyncDBPool):
        self.redis = redis_conn
        self.tsdb = tsdb_pool
        self.group_name = "analytics_aggregator"
        self.consumer_name = f"worker_{uuid4().hex[:8]}"

    async def setup_stream(self):
        try:
            await self.redis.xgroup_create(TELEMETRY_STREAM, self.group_name, id="0", mkstream=True)
        except ResponseError as e:
            if "BUSYGROUP" not in str(e): # Group already exists
                raise

    async def run_loop(self):
        """Continuous processing loop."""
        await self.setup_stream()
        logger.info(f"Started Aggregation Worker: {self.consumer_name}")
        
        while True:
            try:
                # Pull up to 500 events, waiting max 1000ms
                messages = await self.redis.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={TELEMETRY_STREAM: ">"},
                    count=500,
                    block=1000
                )
                
                if not messages:
                    continue
                
                events_to_process = []
                message_ids = []
                
                for stream_name, records in messages:
                    for message_id, record in records:
                        event_data = TelemetryEvent.model_validate_json(record["data"])
                        events_to_process.append(event_data)
                        message_ids.append(message_id)
                
                await self._process_batch(events_to_process)
                
                # Acknowledge messages
                if message_ids:
                    await self.redis.xack(TELEMETRY_STREAM, self.group_name, *message_ids)
                    
            except Exception as e:
                logger.error(f"Worker iteration error: {str(e)}")
                await asyncio.sleep(1) # Backoff

    async def _process_batch(self, events: List[TelemetryEvent]):
        """Handles dual-write to Cache and TSDB."""
        tsdb_rows = []
        pipeline = self.redis.pipeline()
        
        for event in events:
            # 1. Prepare TSDB row (e.g., for TimescaleDB)
            tsdb_rows.append((
                event.event_id, event.timestamp, event.domain.value, 
                event.event_name, event.user_id, json.dumps(event.metadata), 
                event.metric_value
            ))
            
            # 2. Update Real-time Cache
            # Truncate timestamp to current minute for bucketed counters
            minute_bucket = event.timestamp.replace(second=0, microsecond=0).isoformat()
            
            if event.domain == EventDomain.API_REQUESTS:
                # E.g., Increment API status codes per minute
                status_code = event.metadata.get("status_code", "unknown")
                cache_key = f"realtime:api_requests:{minute_bucket}:status:{status_code}"
                pipeline.incrbyfloat(cache_key, event.metric_value)
                pipeline.expire(cache_key, 3600) # Keep live data for 1 hour
                
            elif event.domain == EventDomain.AI_USAGE and event.event_name == "token_consumption":
                # E.g., Sum tokens per minute
                cache_key = f"realtime:ai_tokens:{minute_bucket}"
                pipeline.incrbyfloat(cache_key, event.metric_value)
                pipeline.expire(cache_key, 3600)

        # Execute Redis pipeline natively
        await pipeline.execute()
        
        # Execute TSDB batch insert
        if tsdb_rows:
            insert_query = """
                INSERT INTO analytics_events 
                (id, time, domain, event_name, user_id, metadata, metric_value) 
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            await self.tsdb.execute_many(insert_query, tsdb_rows)


# ============================================================================
# 4. DASHBOARD QUERY SERVICE
# ============================================================================

class DashboardQueryService:
    """
    Service handling read operations for the Admin Dashboard.
    Prioritizes fast Redis lookups for current real-time monitoring.
    """
    def __init__(self, redis_conn: aioredis.Redis, tsdb_pool: AsyncDBPool):
        self.redis = redis_conn
        self.tsdb = tsdb_pool

    async def get_api_error_rates(self, last_minutes: int = 15) -> Dict[str, float]:
        """
        Calculates the API error rate (4xx and 5xx vs Total) for the last N minutes.
        Utilizes the fast-read minute buckets populated by the Aggregation Worker.
        """
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        
        total_requests = 0.0
        error_requests = 0.0
        
        # Fetch bucket data in parallel for the time window
        for i in range(last_minutes):
            bucket_time = (now - timedelta(minutes=i)).isoformat()
            
            # Pattern matching for error vs success buckets
            # Note: In production, explicitly checking keys or using HASHes per minute is safer.
            for status_class in ["2", "3", "4", "5"]:
                key = f"realtime:api_requests:{bucket_time}:status:{status_class}xx" 
                # Mock lookup - assuming status codes were grouped to classes (e.g. 5xx) in worker
                val = await self.redis.get(key)
                if val:
                    count = float(val)
                    total_requests += count
                    if status_class in ["4", "5"]:
                        error_requests += count

        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0.0
        return {
            "time_window_minutes": last_minutes,
            "total_requests": total_requests,
            "error_requests": error_requests,
            "error_rate_percentage": round(error_rate, 2)
        }