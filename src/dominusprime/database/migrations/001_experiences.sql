-- Experience Distillation Database Schema
-- Version: 1.0.0
-- Description: Stores extracted experiences and learned skills

-- Create experiences table
CREATE TABLE IF NOT EXISTS experiences (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'task_workflow', 'problem_solution', 'preference', 'domain_knowledge'
    title TEXT NOT NULL,
    description TEXT,
    context TEXT,  -- JSON array of context keywords
    content TEXT,  -- JSON object with experience details
    confidence REAL NOT NULL DEFAULT 0.0,
    frequency INTEGER DEFAULT 1,
    success_rate REAL DEFAULT 1.0,
    created_at TIMESTAMP NOT NULL,
    last_used TIMESTAMP,
    updated_at TIMESTAMP NOT NULL
);

-- Create indices for efficient querying
CREATE INDEX IF NOT EXISTS idx_exp_type ON experiences(type);
CREATE INDEX IF NOT EXISTS idx_exp_confidence ON experiences(confidence);
CREATE INDEX IF NOT EXISTS idx_exp_frequency ON experiences(frequency);
CREATE INDEX IF NOT EXISTS idx_exp_created ON experiences(created_at);
CREATE INDEX IF NOT EXISTS idx_exp_updated ON experiences(updated_at);

-- Create experience_relations table for linking related experiences
CREATE TABLE IF NOT EXISTS experience_relations (
    from_exp_id TEXT NOT NULL,
    to_exp_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,  -- 'similar', 'prerequisite', 'alternative'
    strength REAL NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (from_exp_id, to_exp_id),
    FOREIGN KEY (from_exp_id) REFERENCES experiences(id) ON DELETE CASCADE,
    FOREIGN KEY (to_exp_id) REFERENCES experiences(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rel_from ON experience_relations(from_exp_id);
CREATE INDEX IF NOT EXISTS idx_rel_to ON experience_relations(to_exp_id);
CREATE INDEX IF NOT EXISTS idx_rel_type ON experience_relations(relation_type);

-- Create generated_skills table
CREATE TABLE IF NOT EXISTS generated_skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    file_path TEXT NOT NULL,
    source_experience_ids TEXT,  -- JSON array of experience IDs
    confidence REAL NOT NULL DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    last_used TIMESTAMP,
    updated_at TIMESTAMP NOT NULL,
    enabled BOOLEAN DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_skill_name ON generated_skills(name);
CREATE INDEX IF NOT EXISTS idx_skill_enabled ON generated_skills(enabled);
CREATE INDEX IF NOT EXISTS idx_skill_usage ON generated_skills(usage_count);

-- Create migration version table
CREATE TABLE IF NOT EXISTS schema_version (
    component TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO schema_version (component, version) VALUES ('experiences', 1);
