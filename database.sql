/*
==============================================================================
TRI-LAYER DATABASE ARCHITECTURE & SCHEMAS
==============================================================================

🏗️ ARCHITECTURE BLUEPRINT:
--------------------------
    [ Client / API ]
          │
          ├─ Read ────> [ Redis (Cache) ] ──(miss)──> [ PostgreSQL ]
          │
          ├─ Write ───> [ PostgreSQL ] ──(trigger)──> [ Outbox Table ]
          │
          └─ Search ──> [ Vector DB ] (Semantic Search -> Returns Postgres IDs)

    [ Sync Worker / Async Processor ]
          │
          ├─ 1. Polls `Outbox Table` in PostgreSQL
          ├─ 2. Calls AI Provider to generate Embeddings (if CREATE/UPDATE)
          ├─ 3. Upserts or Deletes from Vector DB
          ├─ 4. Invalidates/Updates Redis Cache
          └─ 5. Marks Outbox Event as 'COMPLETED'

🗄️ DATA MODELING OVERVIEW:
--------------------------
1. PostgreSQL (Source of Truth):
   - User profiles, RBAC, billing, relational structures.
   - Raw text/content of documents and chat history.
   - Connections managed by `PgBouncer` (transaction pooling mode) to prevent 
     connection exhaustion during high concurrency.

2. Redis (Ephemeral & Cache):
   - Fast-read document caching (Cache-aside with 1hr TTL).
   - Active user sessions & JWT blocklists.
   - Distributed Rate Limiting counters (e.g., tokens per minute).

3. Vector DB (Pinecone/Weaviate/Qdrant):
   - No raw application data (to prevent data drift).
   - Schema: `id` (hash of chunk), `values` (float[]), `metadata`: { "postgres_id": "uuid", "user_id": "uuid" }.
==============================================================================
*/

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. SOURCE OF TRUTH TABLES
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. THE OUTBOX TABLE (Synchronization Mechanism)
CREATE TABLE outbox_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    aggregate_type VARCHAR(50) NOT NULL, -- e.g., 'document'
    aggregate_id UUID NOT NULL,          -- The Postgres ID
    event_type VARCHAR(50) NOT NULL,     -- 'INSERT', 'UPDATE', 'DELETE'
    payload JSONB NOT NULL,              -- The raw data
    status VARCHAR(20) DEFAULT 'PENDING',-- 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. AUTOMATIC OUTBOX TRIGGERS (Guarantees Eventual Consistency)
CREATE OR REPLACE FUNCTION notify_outbox() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO outbox_events(aggregate_type, aggregate_id, event_type, payload)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO outbox_events(aggregate_type, aggregate_id, event_type, payload)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', row_to_json(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO outbox_events(aggregate_type, aggregate_id, event_type, payload)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD));
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_outbox_trigger
AFTER INSERT OR UPDATE OR DELETE ON documents
FOR EACH ROW EXECUTE FUNCTION notify_outbox();