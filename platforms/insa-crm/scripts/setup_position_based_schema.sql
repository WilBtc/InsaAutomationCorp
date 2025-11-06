-- Position-Based CRM Schema for INSA Ingeniería
-- Date: November 6, 2025
-- Purpose: Transform CRM from people-centric to position-centric architecture

-- ============================================================================
-- 1. POSITIONS TABLE - The Permanent Organizational Roles
-- ============================================================================
CREATE TABLE IF NOT EXISTS positions (
    position_id SERIAL PRIMARY KEY,
    position_code VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'SALES_MGR_001'
    position_title VARCHAR(200) NOT NULL,        -- e.g., 'Sales Manager'
    department VARCHAR(100) NOT NULL,             -- e.g., 'Commercial', 'Engineering', 'Support'
    level VARCHAR(50),                            -- 'Executive', 'Manager', 'Specialist', 'Technician', 'Assistant'
    responsibilities TEXT,                        -- What this position is responsible for
    required_skills TEXT[],                       -- Skills needed for this position
    reports_to_position_id INTEGER REFERENCES positions(position_id),  -- Organizational hierarchy
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb           -- Flexible additional data
);

COMMENT ON TABLE positions IS 'Permanent organizational positions/roles at INSA Ingeniería';
COMMENT ON COLUMN positions.position_code IS 'Unique identifier for position (stable across personnel changes)';
COMMENT ON COLUMN positions.reports_to_position_id IS 'Organizational hierarchy - which position this reports to';

-- Index for hierarchy queries
CREATE INDEX IF NOT EXISTS idx_positions_reports_to ON positions(reports_to_position_id);
CREATE INDEX IF NOT EXISTS idx_positions_department ON positions(department);


-- ============================================================================
-- 2. POSITION_ASSIGNMENTS - Who Currently Holds Each Position
-- ============================================================================
CREATE TABLE IF NOT EXISTS position_assignments (
    assignment_id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(position_id) ON DELETE CASCADE,
    bitrix24_user_id VARCHAR(50),                -- From Bitrix24 CRM
    user_name VARCHAR(200) NOT NULL,
    user_email VARCHAR(200),
    start_date DATE NOT NULL,
    end_date DATE,                                -- NULL if current assignment
    is_current BOOLEAN DEFAULT true,
    assignment_type VARCHAR(50) DEFAULT 'permanent',  -- 'permanent', 'temporary', 'acting', 'interim'
    handover_notes TEXT,                          -- Notes from previous holder
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE position_assignments IS 'Historical record of who held each position when';
COMMENT ON COLUMN position_assignments.is_current IS 'True for current position holder, false for historical';
COMMENT ON COLUMN position_assignments.handover_notes IS 'Knowledge transfer notes from previous holder';

-- Critical index: Fast "who is the current Sales Manager?" queries
CREATE INDEX IF NOT EXISTS idx_current_assignments ON position_assignments(position_id, is_current) WHERE is_current = true;
CREATE INDEX IF NOT EXISTS idx_assignments_user ON position_assignments(bitrix24_user_id);
CREATE INDEX IF NOT EXISTS idx_assignments_dates ON position_assignments(start_date, end_date);

-- Constraint: Only one current holder per position
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_current_per_position ON position_assignments(position_id) WHERE is_current = true;


-- ============================================================================
-- 3. POSITION_MEMORY - Each Position's Accumulated Knowledge
-- ============================================================================
CREATE TABLE IF NOT EXISTS position_memory (
    memory_id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(position_id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL,            -- 'lead', 'deal', 'client', 'procedure', 'note', 'playbook', 'lesson_learned'
    memory_category VARCHAR(100),                -- 'sales', 'technical', 'administrative', 'client_relationship'
    memory_title VARCHAR(500) NOT NULL,
    memory_content TEXT NOT NULL,                -- Rich text content (markdown supported)
    importance INTEGER DEFAULT 5,                -- 1-10 scale (10 = critical knowledge)
    created_by_assignment_id INTEGER REFERENCES position_assignments(assignment_id),
    created_by_name VARCHAR(200),                -- Denormalized for quick display
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_accessed_at TIMESTAMP,                  -- Track memory usage
    access_count INTEGER DEFAULT 0,              -- How often this memory is referenced
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],         -- Searchable tags
    related_leads INTEGER[],                     -- Lead IDs related to this memory
    related_deals INTEGER[],                     -- Deal IDs related to this memory
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE position_memory IS 'Knowledge base accumulated by each position over time';
COMMENT ON COLUMN position_memory.importance IS 'Priority 1-10 for onboarding new position holders';
COMMENT ON COLUMN position_memory.access_count IS 'Track frequently accessed knowledge';

-- Full-text search on position memory
CREATE INDEX IF NOT EXISTS idx_position_memory_search ON position_memory USING gin(to_tsvector('english', memory_content));
CREATE INDEX IF NOT EXISTS idx_position_memory_title ON position_memory USING gin(to_tsvector('english', memory_title));
CREATE INDEX IF NOT EXISTS idx_position_memory_tags ON position_memory USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_position_memory_position ON position_memory(position_id);
CREATE INDEX IF NOT EXISTS idx_position_memory_type ON position_memory(memory_type);


-- ============================================================================
-- 4. POSITION_CHROMADB_COLLECTIONS - RAG Memory per Position
-- ============================================================================
CREATE TABLE IF NOT EXISTS position_chromadb_collections (
    collection_id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(position_id) ON DELETE CASCADE,
    collection_name VARCHAR(200) UNIQUE NOT NULL,  -- e.g., 'position_sales_mgr_001_memory'
    vector_count INTEGER DEFAULT 0,
    last_sync_at TIMESTAMP,                        -- Last ChromaDB sync
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE position_chromadb_collections IS 'ChromaDB collections for position-specific RAG memory';
COMMENT ON COLUMN position_chromadb_collections.collection_name IS 'Unique ChromaDB collection name for this position';

CREATE INDEX IF NOT EXISTS idx_chromadb_position ON position_chromadb_collections(position_id);


-- ============================================================================
-- 5. POSITION_LEAD_OWNERSHIP - Leads Owned by Positions (not individuals)
-- ============================================================================
CREATE TABLE IF NOT EXISTS position_lead_ownership (
    ownership_id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL,                     -- Reference to leads table (will create later)
    position_id INTEGER REFERENCES positions(position_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by_position_id INTEGER REFERENCES positions(position_id),  -- Which position made the assignment
    assigned_by_name VARCHAR(200),                -- Denormalized for display
    status VARCHAR(50) DEFAULT 'active',          -- 'active', 'transferred', 'closed', 'won', 'lost'
    transfer_reason TEXT,                         -- Why ownership changed
    notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE position_lead_ownership IS 'Leads are owned by positions, not individuals';
COMMENT ON COLUMN position_lead_ownership.assigned_by_position_id IS 'Which position assigned this lead (may be manager)';

CREATE INDEX IF NOT EXISTS idx_lead_ownership_lead ON position_lead_ownership(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_ownership_position ON position_lead_ownership(position_id, status);
CREATE INDEX IF NOT EXISTS idx_lead_ownership_active ON position_lead_ownership(position_id) WHERE status = 'active';


-- ============================================================================
-- 6. POSITION_HANDOVERS - Track Position Transitions
-- ============================================================================
CREATE TABLE IF NOT EXISTS position_handovers (
    handover_id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(position_id) ON DELETE CASCADE,
    outgoing_assignment_id INTEGER REFERENCES position_assignments(assignment_id),
    incoming_assignment_id INTEGER REFERENCES position_assignments(assignment_id),
    handover_date DATE NOT NULL,
    handover_type VARCHAR(50) DEFAULT 'standard',  -- 'standard', 'emergency', 'temporary', 'promotion'
    handover_notes TEXT,                           -- Knowledge transfer from outgoing holder
    leads_transferred INTEGER DEFAULT 0,
    deals_transferred INTEGER DEFAULT 0,
    procedures_documented INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',          -- 'pending', 'in_progress', 'completed', 'archived'
    completion_percentage INTEGER DEFAULT 0,        -- 0-100% handover completion
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE position_handovers IS 'Track knowledge transfer when position holder changes';
COMMENT ON COLUMN position_handovers.completion_percentage IS 'Percentage of handover checklist completed';

CREATE INDEX IF NOT EXISTS idx_handovers_position ON position_handovers(position_id);
CREATE INDEX IF NOT EXISTS idx_handovers_status ON position_handovers(status);
CREATE INDEX IF NOT EXISTS idx_handovers_date ON position_handovers(handover_date);


-- ============================================================================
-- 7. POSITION_METRICS - Performance Tracking per Position
-- ============================================================================
CREATE TABLE IF NOT EXISTS position_metrics (
    metric_id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(position_id) ON DELETE CASCADE,
    assignment_id INTEGER REFERENCES position_assignments(assignment_id),  -- Specific holder (for comparison)
    metric_type VARCHAR(100) NOT NULL,            -- 'leads_converted', 'deals_closed', 'avg_deal_value', 'response_time'
    metric_value NUMERIC,
    metric_period VARCHAR(50),                    -- 'daily', 'weekly', 'monthly', 'quarterly', 'yearly', 'all_time'
    period_start DATE,
    period_end DATE,
    recorded_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE position_metrics IS 'Track position performance over time across different holders';
COMMENT ON COLUMN position_metrics.assignment_id IS 'NULL for position-level metrics, specific for holder metrics';

CREATE INDEX IF NOT EXISTS idx_metrics_position ON position_metrics(position_id, metric_type, period_start);
CREATE INDEX IF NOT EXISTS idx_metrics_assignment ON position_metrics(assignment_id);


-- ============================================================================
-- 8. POSITION_PROCEDURES - Standard Operating Procedures per Position
-- ============================================================================
CREATE TABLE IF NOT EXISTS position_procedures (
    procedure_id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(position_id) ON DELETE CASCADE,
    procedure_code VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'SALES_MGR_QUOTE_APPROVAL'
    procedure_title VARCHAR(500) NOT NULL,
    procedure_description TEXT,
    procedure_steps JSONB,                        -- Array of steps with details
    required_for_onboarding BOOLEAN DEFAULT false,
    importance INTEGER DEFAULT 5,                 -- 1-10 priority
    frequency VARCHAR(50),                        -- 'daily', 'weekly', 'as_needed', 'per_lead'
    estimated_time_minutes INTEGER,
    related_systems TEXT[],                       -- ['Bitrix24', 'ERPNext', 'Email']
    version INTEGER DEFAULT 1,
    created_by_assignment_id INTEGER REFERENCES position_assignments(assignment_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_reviewed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE position_procedures IS 'Standard operating procedures specific to each position';
COMMENT ON COLUMN position_procedures.required_for_onboarding IS 'Must be reviewed during position handover';

CREATE INDEX IF NOT EXISTS idx_procedures_position ON position_procedures(position_id);
CREATE INDEX IF NOT EXISTS idx_procedures_onboarding ON position_procedures(position_id, required_for_onboarding) WHERE required_for_onboarding = true;


-- ============================================================================
-- TRIGGERS for automatic timestamp updates
-- ============================================================================

-- Generic trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all tables with updated_at
CREATE TRIGGER trigger_positions_updated_at BEFORE UPDATE ON positions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_position_assignments_updated_at BEFORE UPDATE ON position_assignments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_position_memory_updated_at BEFORE UPDATE ON position_memory FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_position_chromadb_collections_updated_at BEFORE UPDATE ON position_chromadb_collections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_position_handovers_updated_at BEFORE UPDATE ON position_handovers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_position_procedures_updated_at BEFORE UPDATE ON position_procedures FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- VIEWS for common queries
-- ============================================================================

-- View: Current position holders (most commonly queried)
CREATE OR REPLACE VIEW current_position_holders AS
SELECT
    p.position_id,
    p.position_code,
    p.position_title,
    p.department,
    p.level,
    pa.assignment_id,
    pa.bitrix24_user_id,
    pa.user_name,
    pa.user_email,
    pa.start_date,
    pa.assignment_type
FROM positions p
LEFT JOIN position_assignments pa ON p.position_id = pa.position_id AND pa.is_current = true
WHERE p.is_active = true;

COMMENT ON VIEW current_position_holders IS 'Quick lookup for who currently holds each position';


-- View: Position ownership summary
CREATE OR REPLACE VIEW position_lead_summary AS
SELECT
    p.position_id,
    p.position_code,
    p.position_title,
    COUNT(CASE WHEN plo.status = 'active' THEN 1 END) as active_leads,
    COUNT(CASE WHEN plo.status = 'won' THEN 1 END) as won_leads,
    COUNT(CASE WHEN plo.status = 'lost' THEN 1 END) as lost_leads,
    COUNT(*) as total_leads
FROM positions p
LEFT JOIN position_lead_ownership plo ON p.position_id = plo.position_id
WHERE p.is_active = true
GROUP BY p.position_id, p.position_code, p.position_title;

COMMENT ON VIEW position_lead_summary IS 'Lead statistics per position';


-- ============================================================================
-- GRANTS (adjust user as needed)
-- ============================================================================
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO insa_crm_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO insa_crm_user;


-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ POSITION-BASED SCHEMA CREATED';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables created: 8';
    RAISE NOTICE '  1. positions';
    RAISE NOTICE '  2. position_assignments';
    RAISE NOTICE '  3. position_memory';
    RAISE NOTICE '  4. position_chromadb_collections';
    RAISE NOTICE '  5. position_lead_ownership';
    RAISE NOTICE '  6. position_handovers';
    RAISE NOTICE '  7. position_metrics';
    RAISE NOTICE '  8. position_procedures';
    RAISE NOTICE '';
    RAISE NOTICE 'Views created: 2';
    RAISE NOTICE '  1. current_position_holders';
    RAISE NOTICE '  2. position_lead_summary';
    RAISE NOTICE '';
    RAISE NOTICE 'Next step: Run populate_insa_positions.sql';
    RAISE NOTICE '========================================';
END $$;
