CREATE TABLE IF NOT EXISTS support_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_director_group BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS engineers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150),
    extension VARCHAR(20),
    mobile_phone VARCHAR(30),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_group_members (
    id SERIAL PRIMARY KEY,
    support_group_id INTEGER NOT NULL REFERENCES support_groups(id),
    engineer_id INTEGER NOT NULL REFERENCES engineers(id),
    role VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    UNIQUE (support_group_id, engineer_id)
);

CREATE TABLE IF NOT EXISTS alert_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    severity VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS escalation_policies (
    id SERIAL PRIMARY KEY,
    alert_type_id INTEGER NOT NULL REFERENCES alert_types(id),
    name VARCHAR(150) NOT NULL,
    retry_attempts INTEGER DEFAULT 3,
    retry_interval_seconds INTEGER DEFAULT 120,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS escalation_levels (
    id SERIAL PRIMARY KEY,
    escalation_policy_id INTEGER NOT NULL REFERENCES escalation_policies(id),
    level_order INTEGER NOT NULL,
    support_group_id INTEGER NOT NULL REFERENCES support_groups(id),
    selected_engineer_id INTEGER REFERENCES engineers(id),
    use_on_call_schedule BOOLEAN DEFAULT TRUE,
    on_call_priority_order INTEGER,
    call_extension BOOLEAN DEFAULT TRUE,
    call_mobile BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    UNIQUE (escalation_policy_id, level_order)
);

CREATE TABLE IF NOT EXISTS on_call_schedules (
    id SERIAL PRIMARY KEY,
    support_group_id INTEGER NOT NULL REFERENCES support_groups(id),
    engineer_id INTEGER NOT NULL REFERENCES engineers(id),
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    priority_order INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alert_events (
    id SERIAL PRIMARY KEY,
    alert_type_id INTEGER NOT NULL REFERENCES alert_types(id),
    title VARCHAR(200),
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS call_attempts (
    id SERIAL PRIMARY KEY,
    alert_event_id INTEGER NOT NULL REFERENCES alert_events(id),
    escalation_level_id INTEGER REFERENCES escalation_levels(id),
    engineer_id INTEGER REFERENCES engineers(id),
    attempt_number INTEGER NOT NULL,
    destination_type VARCHAR(30),
    destination_value VARCHAR(50),
    call_status VARCHAR(50),
    call_id VARCHAR(150),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);