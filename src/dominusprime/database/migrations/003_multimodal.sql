-- Multimodal Memory Database Schema
-- Version: 1.0.0
-- Description: Stores media items and multimodal memory metadata

-- Create media_items table
CREATE TABLE IF NOT EXISTS media_items (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'image', 'audio', 'video'
    original_path TEXT,
    storage_path TEXT NOT NULL,
    thumbnail_path TEXT,
    file_size INTEGER NOT NULL,
    duration REAL,  -- for audio/video in seconds
    width INTEGER,  -- for images/video
    height INTEGER,  -- for images/video
    created_at TIMESTAMP NOT NULL,
    session_id TEXT,
    conversation_context TEXT
);

CREATE INDEX IF NOT EXISTS idx_media_type ON media_items(type);
CREATE INDEX IF NOT EXISTS idx_media_session ON media_items(session_id);
CREATE INDEX IF NOT EXISTS idx_media_created ON media_items(created_at);

-- Create media_content table for extracted text and descriptions
CREATE TABLE IF NOT EXISTS media_content (
    media_id TEXT PRIMARY KEY,
    extracted_text TEXT,  -- OCR or transcription
    description TEXT,  -- AI-generated description
    tags TEXT,  -- JSON array of tags
    embedding_id TEXT,  -- Reference to vector embedding
    FOREIGN KEY (media_id) REFERENCES media_items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_content_embedding ON media_content(embedding_id);

-- Create media_associations table to link media with messages
CREATE TABLE IF NOT EXISTS media_associations (
    media_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    relevance_score REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (media_id, message_id),
    FOREIGN KEY (media_id) REFERENCES media_items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assoc_media ON media_associations(media_id);
CREATE INDEX IF NOT EXISTS idx_assoc_message ON media_associations(message_id);

-- Create embeddings_metadata table for vector search metadata
CREATE TABLE IF NOT EXISTS embeddings_metadata (
    embedding_id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    vector_dimensions INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_id) REFERENCES media_items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_embedding_media ON embeddings_metadata(media_id);
CREATE INDEX IF NOT EXISTS idx_embedding_model ON embeddings_metadata(embedding_model);

-- Create migration version table
CREATE TABLE IF NOT EXISTS schema_version (
    component TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO schema_version (component, version) VALUES ('multimodal', 1);
