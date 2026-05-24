"""
Unified Observability & Instrumentation Module
==============================================
Provides OpenTelemetry (OTel) instrumentation for tracing and metrics.

Grafana Query Cheat Sheet (PromQL & LogQL):
-------------------------------------------
1. CPU & Memory Usage (Infrastructure)
   - CPU Usage: 
     PromQL: 100 - (avg by (cpu) (rate(system_cpu_time_seconds_total{state="idle"}[5m])) * 100)
   - Memory Utilization %: 
     PromQL: (system_memory_usage_bytes{state="used"} / system_memory_usage_bytes{state="total"}) * 100

2. Agent Runtime (Latency)
   - p95 Agent Execution Duration:
     PromQL: histogram_quantile(0.95, sum(rate(agent_execution_duration_bucket[5m])) by (le, agent_name, agent_step))
   - Average Execution Time:
     PromQL: rate(agent_execution_duration_sum[5m]) / rate(agent_execution_duration_count[5m])

3. Request Speed (Latency)
   - p99 HTTP Request Latency:
     PromQL: histogram_quantile(0.99, sum(rate(http_server_request_latency_bucket[5m])) by (le, http_route))
   - HTTP Error Rate %:
     PromQL: sum(rate(http_server_request_latency_count{http_status_code=~"5.."}[5m])) / sum(rate(http_server_request_latency_count[5m])) * 100

4. Deployment Status
   - Active Replicas Tracking:
     PromQL: deployment_status_active_replicas
   - Container Restart Loops (assuming cAdvisor/Kube metrics):
     PromQL: rate(kube_pod_container_status_restarts_total[5m]) > 0

5. Structured Logs (Grafana Loki)
   - View Error Logs for a specific Agent:
     LogQL: {service_name="bug-fixer-backend"} |= "error" | json | agent_name=`code_agent`
   - Rate of errors per minute by step:
     LogQL: sum by (agent_step) (rate({service_name="bug-fixer-backend"} |= "error" [1m]))
"""

import importlib
import time
import logging
from functools import wraps
from typing import Any, Callable

try:
    opentelemetry = importlib.import_module("opentelemetry")
    trace = opentelemetry.trace
    metrics = opentelemetry.metrics
    resources = importlib.import_module("opentelemetry.sdk.resources")
    Resource = resources.Resource
    SERVICE_NAME = resources.SERVICE_NAME
    TracerProvider = importlib.import_module("opentelemetry.sdk.trace").TracerProvider
    MeterProvider = importlib.import_module("opentelemetry.sdk.metrics").MeterProvider
    OTLPSpanExporter = importlib.import_module("opentelemetry.exporter.otlp.proto.grpc.trace_exporter").OTLPSpanExporter
    OTLPMetricExporter = importlib.import_module("opentelemetry.exporter.otlp.proto.grpc.metric_exporter").OTLPMetricExporter
    BatchSpanProcessor = importlib.import_module("opentelemetry.sdk.trace.export").BatchSpanProcessor
    PeriodicExportingMetricReader = importlib.import_module("opentelemetry.sdk.metrics.export").PeriodicExportingMetricReader
    LoggingInstrumentor = importlib.import_module("opentelemetry.instrumentation.logging").LoggingInstrumentor
except ImportError:
    class DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_attribute(self, *args, **kwargs):
            pass

        def record_exception(self, *args, **kwargs):
            pass

        def start_as_current_span(self, *args, **kwargs):
            return self

    class DummyTracer:
        def set_tracer_provider(self, provider):
            pass

        def get_tracer(self, *args, **kwargs):
            return DummySpan()

    class DummyMetric:
        def record(self, *args, **kwargs):
            pass

    class DummyMeter:
        def set_meter_provider(self, provider):
            pass

        def get_meter(self, *args, **kwargs):
            return self

        def create_histogram(self, *args, **kwargs):
            return DummyMetric()

        def create_up_down_counter(self, *args, **kwargs):
            return DummyMetric()

    class DummyResource:
        @staticmethod
        def create(*args, **kwargs):
            return {}

    class DummyProvider:
        def __init__(self, *args, **kwargs):
            pass

        def add_span_processor(self, *args, **kwargs):
            pass

    class DummyExporter:
        def __init__(self, *args, **kwargs):
            pass

    class DummySpanProcessor:
        def __init__(self, *args, **kwargs):
            pass

    class DummyMetricReader:
        def __init__(self, *args, **kwargs):
            pass

    class LoggingInstrumentor:
        def instrument(self, *args, **kwargs):
            pass

    trace = DummyTracer()
    metrics = DummyMeter()
    Resource = DummyResource
    SERVICE_NAME = "service.name"
    TracerProvider = DummyProvider
    MeterProvider = DummyProvider
    OTLPSpanExporter = DummyExporter
    OTLPMetricExporter = DummyExporter
    BatchSpanProcessor = DummySpanProcessor
    PeriodicExportingMetricReader = DummyMetricReader

# ----------------------------------------------------------------------------
# 1. OTel Resource & Provider Initialization
# ----------------------------------------------------------------------------

resource = Resource.create({
    SERVICE_NAME: "bug-fixer-backend",
    "service.version": "1.0.0",
    "environment": "production"
})

# Trace Setup
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

# Metrics Setup
meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint="http://localhost:4317")
    )]
)
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Inject Trace Context into standard Python logs
LoggingInstrumentor().instrument(set_logging_format=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----------------------------------------------------------------------------
# 2. Custom Metrics Definitions
# ----------------------------------------------------------------------------

request_latency_histogram = meter.create_histogram(
    name="http.server.request.latency",
    description="Measures the latency of HTTP requests",
    unit="ms"
)

agent_runtime_histogram = meter.create_histogram(
    name="agent.execution.duration",
    description="Measures the execution duration of autonomous agents",
    unit="s"
)

deployment_status_gauge = meter.create_up_down_counter(
    name="deployment.status.active_replicas",
    description="Tracks live infrastructure deployment states",
    unit="1"
)

# ----------------------------------------------------------------------------
# 3. Instrumentation Wrappers (Decorators)
# ----------------------------------------------------------------------------

def track_request_speed(method: str, route: str) -> Callable:
    """Decorator to track HTTP/gRPC request latency."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            status_code = 200
            try:
                return func(*args, **kwargs)
            except Exception as e:
                status_code = 500
                logger.error(f"Request failed: {e}", extra={"http_route": route})
                raise
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                request_latency_histogram.record(
                    duration_ms, 
                    {"http.method": method, "http.route": route, "http.status_code": status_code}
                )
        return wrapper
    return decorator

def track_agent_runtime(agent_name: str, step_name: str) -> Callable:
    """Decorator to trace and track AI Agent execution duration and lifecycle."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(f"{agent_name}.{step_name}") as span:
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("agent.status", "success")
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_attribute("agent.status", "failed")
                    raise
                finally:
                    duration_s = time.perf_counter() - start_time
                    agent_runtime_histogram.record(
                        duration_s, 
                        {"agent_name": agent_name, "agent_step": step_name}
                    )
        return wrapper
    return decorator