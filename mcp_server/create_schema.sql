-- Create the agent_status_logs table
CREATE TABLE IF NOT EXISTS agent_status_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255),
    user_id VARCHAR(255),
    agent_name VARCHAR(100),
    status_type VARCHAR(50),
    message TEXT,
    metadata JSONB
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_agent_status_logs_timestamp 
ON agent_status_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_agent_status_logs_session_id 
ON agent_status_logs(session_id);

CREATE INDEX IF NOT EXISTS idx_agent_status_logs_agent_name 
ON agent_status_logs(agent_name);

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON TABLE agent_status_logs TO finadvisor_user;
GRANT USAGE, SELECT ON SEQUENCE agent_status_logs_id_seq TO finadvisor_user;
