-- Security Database Schema
-- Version: 1.0.0
-- Description: Stores security logs, permissions, and audit trails

-- Create command_executions table
CREATE TABLE IF NOT EXISTS command_executions (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    user_id TEXT,
    session_id TEXT,
    command TEXT NOT NULL,
    risk_level TEXT NOT NULL,  -- 'safe', 'low', 'medium', 'high', 'critical'
    approval_status TEXT,  -- 'approved', 'denied', 'auto_approved', 'bypassed'
    exit_code INTEGER,
    duration_ms INTEGER,
    working_dir TEXT,
    channel TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cmd_timestamp ON command_executions(timestamp);
CREATE INDEX IF NOT EXISTS idx_cmd_user ON command_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_cmd_session ON command_executions(session_id);
CREATE INDEX IF NOT EXISTS idx_cmd_risk ON command_executions(risk_level);
CREATE INDEX IF NOT EXISTS idx_cmd_approval ON command_executions(approval_status);

-- Create approval_patterns table
CREATE TABLE IF NOT EXISTS approval_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    command_pattern TEXT NOT NULL,
    decision TEXT NOT NULL,  -- 'always_allow', 'always_deny'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    use_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pattern_user ON approval_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_pattern_decision ON approval_patterns(decision);
CREATE UNIQUE INDEX IF NOT EXISTS idx_pattern_unique ON approval_patterns(user_id, command_pattern);

-- Create tool_permissions table
CREATE TABLE IF NOT EXISTS tool_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    permission_level TEXT NOT NULL,  -- 'denied', 'prompt', 'session', 'always'
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    granted_by TEXT,
    UNIQUE(user_id, tool_name)
);

CREATE INDEX IF NOT EXISTS idx_perm_user ON tool_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_perm_tool ON tool_permissions(tool_name);
CREATE INDEX IF NOT EXISTS idx_perm_level ON tool_permissions(permission_level);

-- Create tool_usage_log table
CREATE TABLE IF NOT EXISTS tool_usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT,
    tool_name TEXT NOT NULL,
    tool_category TEXT,
    risk_level TEXT,
    success BOOLEAN,
    error TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usage_user ON tool_usage_log(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_tool ON tool_usage_log(tool_name);
CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON tool_usage_log(timestamp);

-- Create rate_limits table
CREATE TABLE IF NOT EXISTS rate_limits (
    user_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    window_start TIMESTAMP NOT NULL,
    execution_count INTEGER DEFAULT 1,
    PRIMARY KEY (user_id, tool_name, window_start)
);

CREATE INDEX IF NOT EXISTS idx_rate_window ON rate_limits(window_start);

-- Create security_events table for audit trail
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,  -- 'security_level_changed', 'permission_granted', 'command_blocked', etc.
    user_id TEXT,
    details TEXT,  -- JSON object with event details
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_event_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_event_user ON security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_event_timestamp ON security_events(timestamp);

-- Create migration version table
CREATE TABLE IF NOT EXISTS schema_version (
    component TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO schema_version (component, version) VALUES ('security', 1);
