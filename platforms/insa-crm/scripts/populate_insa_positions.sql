-- Populate INSA Ingeniería Positions with Real Data from Bitrix24
-- Date: November 6, 2025
-- Based on: 31 employees from bitrix24_graphiti_episodes.json

BEGIN;

-- ============================================================================
-- EXECUTIVE LEVEL POSITIONS
-- ============================================================================

INSERT INTO positions (position_code, position_title, department, level, responsibilities, required_skills, reports_to_position_id, metadata) VALUES
('CEO_001', 'CEO / Founder', 'Executive', 'Executive',
 'Strategic direction, major partnerships, board decisions, company vision',
 ARRAY['Leadership', 'Strategic Planning', 'Business Development', 'Oil & Gas Industry'],
 NULL,  -- Reports to board/self
 '{"crm_priority": "high", "decision_authority": "ultimate"}'::jsonb),

('OPS_DIR_001', 'Operations Director', 'Executive', 'Executive',
 'Overall operations management, sales oversight, cross-department coordination',
 ARRAY['Operations Management', 'Sales Strategy', 'Team Leadership'],
 1,  -- Reports to CEO
 '{"crm_priority": "high", "decision_authority": "high"}'::jsonb);


-- ============================================================================
-- COMMERCIAL / SALES TEAM
-- ============================================================================

INSERT INTO positions (position_code, position_title, department, level, responsibilities, required_skills, reports_to_position_id, metadata) VALUES
('SALES_MGR_001', 'Sales Manager', 'Commercial', 'Manager',
 'Lead sales team, close major deals, sales strategy, team performance',
 ARRAY['Sales Management', 'Negotiation', 'Oil & Gas Sales', 'CRM Systems'],
 2,  -- Reports to Operations Director
 '{"crm_priority": "critical", "lead_assignment": true, "quote_approval": true}'::jsonb),

('COMM_SPEC_001', 'Commercial Specialist', 'Commercial', 'Specialist',
 'Client relationships, proposal preparation, commercial negotiations',
 ARRAY['Client Relations', 'Proposal Writing', 'Commercial Awareness'],
 3,  -- Reports to Sales Manager
 '{"crm_priority": "high", "lead_assignment": true}'::jsonb),

('COMM_SUPPORT_001', 'Commercial Support', 'Commercial', 'Specialist',
 'Quote preparation, client follow-ups, sales support',
 ARRAY['Quote Preparation', 'Client Communication', 'CRM Data Entry'],
 3,  -- Reports to Sales Manager
 '{"crm_priority": "high", "quote_generation": true}'::jsonb),

('MARKETING_MGR_001', 'Marketing Manager', 'Commercial', 'Manager',
 'Marketing campaigns, lead generation, brand management',
 ARRAY['Digital Marketing', 'Campaign Management', 'Content Creation'],
 2,  -- Reports to Operations Director
 '{"crm_priority": "medium", "lead_generation": true}'::jsonb);


-- ============================================================================
-- ENGINEERING TEAM
-- ============================================================================

INSERT INTO positions (position_code, position_title, department, level, responsibilities, required_skills, reports_to_position_id, metadata) VALUES
('LEAD_MECH_ENG_001', 'Lead Mechanical Engineer', 'Engineering', 'Manager',
 'P&ID design, equipment sizing, mechanical calculations, design standards',
 ARRAY['Mechanical Engineering', 'P&ID Design', 'Equipment Sizing', 'Oil & Gas Standards'],
 2,  -- Reports to Operations Director
 '{"crm_priority": "high", "technical_review": true, "quote_support": true}'::jsonb),

('ELEC_SPEC_SR_001', 'Electrical Specialist (Senior)', 'Engineering', 'Specialist',
 'Electrical design, panel layouts, power calculations',
 ARRAY['Electrical Engineering', 'Panel Design', 'Power Systems', 'AutoCAD Electrical'],
 7,  -- Reports to Lead Mechanical Engineer
 '{"crm_priority": "medium", "technical_support": true}'::jsonb),

('ELEC_TECH_001', 'Electrical Technician', 'Engineering', 'Technician',
 'Field installation, electrical testing, troubleshooting',
 ARRAY['Electrical Installation', 'Testing', 'Troubleshooting'],
 8,  -- Reports to Electrical Specialist
 '{"crm_priority": "low", "field_work": true}'::jsonb),

('INSTR_SPEC_LEAD_001', 'Instrumentation Specialist (Lead)', 'Engineering', 'Specialist',
 'Instrumentation design, calibration procedures, instrument selection',
 ARRAY['Instrumentation', 'Calibration', 'Process Control', 'Fieldbus Protocols'],
 7,  -- Reports to Lead Mechanical Engineer
 '{"crm_priority": "high", "technical_support": true, "quote_support": true}'::jsonb),

('INSTR_TECH_001', 'Instrumentation Technician 1', 'Engineering', 'Technician',
 'Field instrumentation installation, calibration, maintenance',
 ARRAY['Instrument Installation', 'Calibration', 'Field Work'],
 10,  -- Reports to Instrumentation Specialist
 '{"crm_priority": "low", "field_work": true}'::jsonb),

('INSTR_TECH_002', 'Instrumentation Technician 2', 'Engineering', 'Technician',
 'Field instrumentation installation, calibration, maintenance',
 ARRAY['Instrument Installation', 'Calibration', 'Field Work'],
 10,  -- Reports to Instrumentation Specialist
 '{"crm_priority": "low", "field_work": true}'::jsonb),

('INSTR_TECH_003', 'Instrumentation Technician 3', 'Engineering', 'Technician',
 'Field instrumentation installation, calibration, maintenance',
 ARRAY['Instrument Installation', 'Calibration', 'Field Work'],
 10,  -- Reports to Instrumentation Specialist
 '{"crm_priority": "low", "field_work": true}'::jsonb),

('APP_SPEC_SR_001', 'Applications Specialist (Senior)', 'Engineering', 'Specialist',
 'Software applications, HMI design, SCADA configuration',
 ARRAY['PLC Programming', 'HMI Design', 'SCADA', 'Industrial Software'],
 7,  -- Reports to Lead Mechanical Engineer
 '{"crm_priority": "medium", "technical_support": true}'::jsonb),

('APP_SUPPORT_001', 'Applications Support', 'Engineering', 'Specialist',
 'Application troubleshooting, software support',
 ARRAY['Software Troubleshooting', 'Technical Support', 'PLC Basics'],
 14,  -- Reports to Applications Specialist
 '{"crm_priority": "low", "support_tickets": true}'::jsonb),

('DESIGN_ENG_001', 'Design Engineer', 'Engineering', 'Specialist',
 'CAD design, 3D modeling, technical drawings',
 ARRAY['AutoCAD', '3D Modeling', 'Technical Drawing', 'CadQuery'],
 7,  -- Reports to Lead Mechanical Engineer
 '{"crm_priority": "medium", "cad_generation": true}'::jsonb);


-- ============================================================================
-- SUPPORT FUNCTIONS
-- ============================================================================

INSERT INTO positions (position_code, position_title, department, level, responsibilities, required_skills, reports_to_position_id, metadata) VALUES
('ADMIN_MGR_001', 'Administration Manager', 'Administration', 'Manager',
 'Administrative operations, HR, policies, contracts',
 ARRAY['Administration', 'HR Management', 'Policy Development'],
 2,  -- Reports to Operations Director
 '{"crm_priority": "low", "contract_management": true}'::jsonb),

('PURCHASING_MGR_001', 'Purchasing Manager', 'Administration', 'Manager',
 'Procurement, vendor management, purchasing strategy',
 ARRAY['Procurement', 'Vendor Management', 'Negotiation', 'Supply Chain'],
 17,  -- Reports to Administration Manager
 '{"crm_priority": "medium", "vendor_database": true, "quote_support": true}'::jsonb),

('HSEQ_MGR_001', 'HSEQ Manager', 'HSEQ', 'Manager',
 'Health, safety, environment, quality systems, compliance',
 ARRAY['HSEQ Standards', 'ISO Certification', 'Safety Audits', 'Risk Assessment'],
 2,  -- Reports to Operations Director
 '{"crm_priority": "medium", "compliance_required": true}'::jsonb),

('LOGISTICS_COORD_001', 'Logistics Coordinator', 'Logistics', 'Specialist',
 'Shipping, inventory, customs, logistics coordination',
 ARRAY['Logistics', 'Inventory Management', 'Customs', 'Shipping'],
 17,  -- Reports to Administration Manager
 '{"crm_priority": "low", "project_delivery": true}'::jsonb),

('GENERATION_MGR_001', 'Generation Manager', 'Engineering', 'Manager',
 'Power generation projects, generator specifications',
 ARRAY['Power Generation', 'Generator Systems', 'Project Management'],
 7,  -- Reports to Lead Mechanical Engineer
 '{"crm_priority": "medium", "specialized_projects": true}'::jsonb);


-- ============================================================================
-- JUNIOR / ASSISTANT ROLES
-- ============================================================================

INSERT INTO positions (position_code, position_title, department, level, responsibilities, required_skills, reports_to_position_id, metadata) VALUES
('ASST_ENG_001', 'Assistant Engineer 1', 'Engineering', 'Assistant',
 'Engineering support, calculations, documentation',
 ARRAY['Engineering Fundamentals', 'Technical Documentation', 'Calculation Support'],
 7,  -- Reports to Lead Mechanical Engineer
 '{"crm_priority": "low", "learning_position": true}'::jsonb),

('ASST_ENG_002', 'Assistant Engineer 2', 'Engineering', 'Assistant',
 'Engineering support, calculations, documentation',
 ARRAY['Engineering Fundamentals', 'Technical Documentation', 'Calculation Support'],
 7,  -- Reports to Lead Mechanical Engineer
 '{"crm_priority": "low", "learning_position": true}'::jsonb),

('ASST_ENG_003', 'Assistant Engineer 3', 'Engineering', 'Assistant',
 'Engineering support, calculations, documentation',
 ARRAY['Engineering Fundamentals', 'Technical Documentation', 'Calculation Support'],
 7,  -- Reports to Lead Mechanical Engineer
 '{"crm_priority": "low", "learning_position": true}'::jsonb),

('ASST_ENG_004', 'Assistant Engineer 4', 'Engineering', 'Assistant',
 'Engineering support, calculations, documentation',
 ARRAY['Engineering Fundamentals', 'Technical Documentation', 'Calculation Support'],
 7,  -- Reports to Lead Mechanical Engineer
 '{"crm_priority": "low", "learning_position": true}'::jsonb),

('ADMIN_ASST_001', 'Administrative Assistant', 'Administration', 'Assistant',
 'Administrative support, documentation, scheduling',
 ARRAY['Office Administration', 'Scheduling', 'Documentation'],
 17,  -- Reports to Administration Manager
 '{"crm_priority": "low", "support_role": true}'::jsonb),

('FIELD_TECH_001', 'Field Technician', 'Engineering', 'Technician',
 'Field installation, maintenance, technical support',
 ARRAY['Field Work', 'Installation', 'Maintenance'],
 7,  -- Reports to Lead Mechanical Engineer
 '{"crm_priority": "low", "field_work": true}'::jsonb);


-- ============================================================================
-- NOW ASSIGN CURRENT BITRIX24 USERS TO POSITIONS
-- ============================================================================

-- Executive Level
INSERT INTO position_assignments (position_id, bitrix24_user_id, user_name, user_email, start_date, is_current) VALUES
(1, '27', 'Wil Aroca', 'w.aroca@insaing.com', '2020-01-01', true),  -- CEO
(2, '1', 'Juan Carlos Casas', 'j.casas@insaing.com', '2020-01-01', true);  -- Operations Director

-- Commercial Team
INSERT INTO position_assignments (position_id, bitrix24_user_id, user_name, user_email, start_date, is_current) VALUES
(3, '1', 'Juan Carlos Casas', 'j.casas@insaing.com', '2020-01-01', true),  -- Sales Manager (same person as OpsDir)
(4, '43', 'Alexandra Guzmán', 'comercial@insaing.com', '2021-01-01', true),  -- Commercial Specialist
(5, '1021', 'Gina Garzón', 'soporte.comercial@insaing.com', '2022-01-01', true),  -- Commercial Support
(6, '41', 'Samuel Casas', 'marketing@insaing.com', '2021-06-01', true);  -- Marketing Manager

-- Engineering Team
INSERT INTO position_assignments (position_id, bitrix24_user_id, user_name, user_email, start_date, is_current) VALUES
-- Lead Mech Eng - To be assigned (TBD)
(8, '626', 'Cesar Steven Hernandez Granados', 'electrico2@insaing.com', '2022-01-01', true),  -- Electrical Specialist Sr
(9, '1133', 'Cristian Molano', 'tecnico.electrico3@insaing.com', '2023-01-01', true),  -- Electrical Technician
(10, '1063', 'Andres Felipe Arevalo', 'especialista.aplicaciones@insaing.com', '2022-06-01', true),  -- Instrumentation Specialist Lead
(11, '1085', 'Sebastian Pachon Sanchez', 'tecnico_instrumentista1@insaing.com', '2023-01-01', true),  -- Instrumentation Tech 1
(12, '1121', 'Ronald Madero', 'instrumentista2@insaing.com', '2023-06-01', true),  -- Instrumentation Tech 2
(13, '1129', 'Edisson Franco', 'instrumentista3@insaing.com', '2024-01-01', true),  -- Instrumentation Tech 3
(14, '1099', 'Esteban Siabato Ruiz', 'soporte.aplicaciones@insaing.com', '2023-01-01', true),  -- Applications Specialist Sr
(15, '1123', 'Julieth Sandoval', 'soporte_de_aplicaciones@insaing.com', '2023-06-01', true),  -- Applications Support
(16, '51', 'Ivan Jurado', 'ivan.jurado@insaing.com', '2021-01-01', true);  -- Design Engineer

-- Support Functions
INSERT INTO position_assignments (position_id, bitrix24_user_id, user_name, user_email, start_date, is_current) VALUES
(17, '11', 'Vanessa Ovalle', 'administracion@insaing.com', '2020-01-01', true),  -- Administration Manager
(18, '13', 'Natalia Ibáñez Rodriguez', 'compras@insaing.com', '2020-06-01', true),  -- Purchasing Manager
(19, '47', 'Andrea Valentina Álvarez Gutierrez', 'hseq@insaing.com', '2021-01-01', true),  -- HSEQ Manager
(20, '815', 'Andres Goméz', 'logistica@insaing.com', '2022-01-01', true),  -- Logistics Coordinator
(21, '843', 'Darwin Pereira', 'generacion@insaing.com', '2022-06-01', true);  -- Generation Manager

-- Junior / Assistant Roles
INSERT INTO position_assignments (position_id, bitrix24_user_id, user_name, user_email, start_date, is_current) VALUES
(22, '3', 'Leonardo Casas', 'leonardo.casas@insaing.com', '2021-01-01', true),  -- Assistant Engineer 1
(23, '871', 'Arturo Hernandez', 'arturo.hernandez@insaing.com', '2022-01-01', true),  -- Assistant Engineer 2
(24, '895', 'Manuel Perez', 'manuel.perez@insaing.com', '2022-06-01', true),  -- Assistant Engineer 3
(25, '969', 'Arturo Sarmiento', 'arturo.sarmiento@insaing.com', '2023-01-01', true),  -- Assistant Engineer 4
(26, '997', 'Susana Méndez Durán', 's.mendez@insaing.com', '2023-01-01', true),  -- Administrative Assistant
(27, '765', 'Anggi Rojas', 'anggi.rojas@insaing.com', '2022-01-01', true);  -- Field Technician


-- ============================================================================
-- CREATE CHROMADB COLLECTION ENTRIES for KEY POSITIONS
-- ============================================================================

-- Create RAG collections for positions that need memory
INSERT INTO position_chromadb_collections (position_id, collection_name) VALUES
(1, 'position_ceo_001_memory'),
(2, 'position_ops_dir_001_memory'),
(3, 'position_sales_mgr_001_memory'),
(4, 'position_comm_spec_001_memory'),
(6, 'position_marketing_mgr_001_memory'),
(7, 'position_lead_mech_eng_001_memory'),
(10, 'position_instr_spec_lead_001_memory'),
(14, 'position_app_spec_sr_001_memory'),
(18, 'position_purchasing_mgr_001_memory'),
(19, 'position_hseq_mgr_001_memory');


-- ============================================================================
-- SAMPLE POSITION MEMORY ENTRIES
-- ============================================================================

-- Sales Manager position memory examples
INSERT INTO position_memory (position_id, memory_type, memory_category, memory_title, memory_content, importance, created_by_assignment_id, tags) VALUES
(3, 'playbook', 'sales', 'Petrobras Sales Approach',
 'Petrobras requires formal technical proposals with detailed engineering calculations. Decision cycle is typically 3-6 months. Key decision makers are in procurement engineering. Always include free training in quotes - this is a major differentiator.',
 9, 3, ARRAY['petrobras', 'sales_strategy', 'oil_gas']),

(3, 'playbook', 'sales', 'Quote Follow-up Best Practices',
 'Follow up within 48 hours of sending quote. Second follow-up at 1 week. If no response after 2 weeks, escalate to phone call. Most deals close between quote revision 2 and 3. Key: always ask "what would make this a yes?"',
 8, 3, ARRAY['follow_up', 'closing', 'sales_process']);

-- HSEQ Manager position memory
INSERT INTO position_memory (position_id, memory_type, memory_category, memory_title, memory_content, importance, created_by_assignment_id, tags) VALUES
(19, 'procedure', 'safety', 'Client Site Safety Requirements Checklist',
 'Before any fieldwork: 1) Verify client HSE induction completed, 2) Confirm PPE availability, 3) Review site-specific hazards, 4) Complete INSA work permit, 5) Notify client 24h before arrival.',
 10, 19, ARRAY['safety', 'fieldwork', 'compliance']);


-- ============================================================================
-- SAMPLE POSITION PROCEDURES
-- ============================================================================

INSERT INTO position_procedures (position_id, procedure_code, procedure_title, procedure_description, procedure_steps, required_for_onboarding, importance, frequency) VALUES
(3, 'SALES_MGR_LEAD_QUALIFICATION', 'Lead Qualification Process',
 'Standard process for qualifying new leads in INSA CRM',
 '[
   {"step": 1, "action": "Review lead source and contact info", "system": "Bitrix24"},
   {"step": 2, "action": "Check company size and industry fit", "system": "INSA CRM"},
   {"step": 3, "action": "Assign lead score (0-100)", "system": "INSA CRM AI"},
   {"step": 4, "action": "If score > 70, assign to specialist", "system": "INSA CRM"},
   {"step": 5, "action": "If score < 40, send to nurture campaign", "system": "Mautic"}
 ]'::jsonb,
 true, 9, 'per_lead'),

(3, 'SALES_MGR_QUOTE_APPROVAL', 'Quote Approval Workflow',
 'Approve quotes before sending to clients',
 '[
   {"step": 1, "action": "Review technical accuracy with Lead Engineer", "system": "Email"},
   {"step": 2, "action": "Verify pricing with Purchasing Manager", "system": "ERPNext"},
   {"step": 3, "action": "Check margin > 25%", "system": "INSA CRM"},
   {"step": 4, "action": "Approve and send", "system": "Bitrix24"}
 ]'::jsonb,
 true, 10, 'per_quote');


COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Show all positions with current holders
SELECT
    p.position_code,
    p.position_title,
    p.department,
    pa.user_name,
    pa.user_email
FROM positions p
LEFT JOIN position_assignments pa ON p.position_id = pa.position_id AND pa.is_current = true
ORDER BY p.department, p.level DESC, p.position_code;

-- Show organizational hierarchy (simplified)
SELECT
    p1.position_title as position,
    p2.position_title as reports_to,
    pa.user_name as current_holder
FROM positions p1
LEFT JOIN positions p2 ON p1.reports_to_position_id = p2.position_id
LEFT JOIN position_assignments pa ON p1.position_id = pa.position_id AND pa.is_current = true
WHERE p1.is_active = true
ORDER BY p1.department, p1.level DESC;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ INSA POSITIONS POPULATED';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total positions created: 27';
    RAISE NOTICE 'Current assignments: 26 (1 TBD)';
    RAISE NOTICE 'ChromaDB collections: 10';
    RAISE NOTICE 'Position memory entries: 3';
    RAISE NOTICE 'Position procedures: 2';
    RAISE NOTICE '';
    RAISE NOTICE 'Ready for position-based CRM operation!';
    RAISE NOTICE '========================================';
END $$;
