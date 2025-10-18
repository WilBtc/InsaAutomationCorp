-- Migration 008: Communication System Tables (Simplified - No Foreign Keys)
-- Phase 8: Customer Communication Agent

-- Drop existing tables if they exist
DROP TABLE IF EXISTS message_analytics CASCADE;
DROP TABLE IF EXISTS communication_preferences CASCADE;
DROP TABLE IF EXISTS communication_templates CASCADE;
DROP TABLE IF EXISTS call_transcripts CASCADE;
DROP TABLE IF EXISTS communication_campaigns CASCADE;
DROP TABLE IF EXISTS communication_logs CASCADE;

-- Communication logs (all channels)
CREATE TABLE communication_logs (
    id SERIAL PRIMARY KEY,
    channel VARCHAR(20) NOT NULL,  -- email, phone, sms, whatsapp
    recipient VARCHAR(255) NOT NULL,
    message_id VARCHAR(255),
    subject VARCHAR(500),
    content TEXT,
    status VARCHAR(50) NOT NULL,  -- sent, delivered, failed, opened, clicked
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,  -- Additional tracking data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_communication_logs_recipient ON communication_logs(recipient);
CREATE INDEX idx_communication_logs_message_id ON communication_logs(message_id);
CREATE INDEX idx_communication_logs_status ON communication_logs(status);
CREATE INDEX idx_communication_logs_sent_at ON communication_logs(sent_at);

-- Communication campaigns (multi-channel sequences)
CREATE TABLE communication_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(255) UNIQUE NOT NULL,
    lead_id INTEGER,  -- No foreign key
    quote_id VARCHAR(100),
    channels JSONB NOT NULL,  -- ["email", "sms", "phone"]
    scheduled_messages JSONB NOT NULL,  -- Array of scheduled messages
    status VARCHAR(50) DEFAULT 'active',  -- active, paused, completed, cancelled
    total_messages INTEGER DEFAULT 0,
    sent_messages INTEGER DEFAULT 0,
    opened_messages INTEGER DEFAULT 0,
    clicked_messages INTEGER DEFAULT 0,
    conversion_event VARCHAR(100),  -- quote_accepted, meeting_scheduled, etc
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_campaigns_lead_id ON communication_campaigns(lead_id);
CREATE INDEX idx_campaigns_quote_id ON communication_campaigns(quote_id);
CREATE INDEX idx_campaigns_status ON communication_campaigns(status);

-- Phone call transcripts (from Vapi.ai)
CREATE TABLE call_transcripts (
    id SERIAL PRIMARY KEY,
    call_id VARCHAR(255) UNIQUE NOT NULL,
    lead_id INTEGER,  -- No foreign key
    phone_number VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL,  -- inbound, outbound
    purpose VARCHAR(100),  -- quote_follow_up, meeting_scheduling, etc
    transcript TEXT,
    duration_seconds INTEGER,
    sentiment VARCHAR(50),  -- positive, neutral, negative
    action_items JSONB,  -- Extracted action items
    recording_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'completed',  -- initiated, in_progress, completed, failed
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_call_transcripts_lead_id ON call_transcripts(lead_id);
CREATE INDEX idx_call_transcripts_phone ON call_transcripts(phone_number);
CREATE INDEX idx_call_transcripts_sentiment ON call_transcripts(sentiment);

-- Communication templates
CREATE TABLE communication_templates (
    id SERIAL PRIMARY KEY,
    template_id VARCHAR(100) UNIQUE NOT NULL,
    channel VARCHAR(20) NOT NULL,  -- email, sms, phone
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500),  -- For email
    content_html TEXT,  -- For email
    content_text TEXT,  -- For SMS or plain text
    variables JSONB,  -- Template variables: {"customer_name": "string", "quote_total": "number"}
    category VARCHAR(100),  -- quote_follow_up, meeting_reminder, etc
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_channel ON communication_templates(channel);
CREATE INDEX idx_templates_category ON communication_templates(category);

-- Communication preferences (customer opt-in/opt-out)
CREATE TABLE communication_preferences (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER UNIQUE,  -- No foreign key
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT true,
    phone_enabled BOOLEAN DEFAULT true,
    whatsapp_enabled BOOLEAN DEFAULT false,
    preferred_channel VARCHAR(20) DEFAULT 'email',
    preferred_time VARCHAR(50),  -- "9am-5pm EST"
    do_not_contact BOOLEAN DEFAULT false,
    unsubscribed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_preferences_lead_id ON communication_preferences(lead_id);

-- Message analytics (A/B testing, performance)
CREATE TABLE message_analytics (
    id SERIAL PRIMARY KEY,
    template_id VARCHAR(100),
    variant VARCHAR(50),  -- A, B, C for A/B testing
    channel VARCHAR(20) NOT NULL,
    sent_count INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    conversion_count INTEGER DEFAULT 0,
    bounce_count INTEGER DEFAULT 0,
    unsubscribe_count INTEGER DEFAULT 0,
    avg_time_to_open_seconds INTEGER,
    avg_time_to_click_seconds INTEGER,
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(template_id, variant, channel, date)
);

CREATE INDEX idx_analytics_template ON message_analytics(template_id);
CREATE INDEX idx_analytics_date ON message_analytics(date);

-- Insert default templates
INSERT INTO communication_templates (template_id, channel, name, subject, content_html, content_text, category, variables) VALUES
('quote_email_v1', 'email', 'Quote Email - Professional', 'Your Custom Quote - {{quote_id}}',
'<h1>Your Quote is Ready!</h1><p>Dear {{customer_name}},</p><p>Total: ${{quote_total}}</p>',
'Dear {{customer_name}}, Your quote {{quote_id}} for ${{quote_total}} is ready.',
'quote_follow_up',
'{"customer_name": "string", "quote_id": "string", "quote_total": "number"}'::jsonb
),
('sms_reminder_v1', 'sms', 'Quote Reminder SMS', NULL,
NULL,
'Hi {{customer_name}}! Following up on quote {{quote_id}}. Questions? Call us at {{phone_number}}. -INSA',
'quote_follow_up',
'{"customer_name": "string", "quote_id": "string", "phone_number": "string"}'::jsonb
);

-- Display summary
SELECT 'Communication tables created successfully!' AS status;
SELECT COUNT(*) AS template_count FROM communication_templates;
