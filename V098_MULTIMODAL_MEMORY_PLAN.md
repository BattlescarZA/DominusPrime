# v0.9.8 Multimodal Memory Implementation Plan

**Start Date:** April 8, 2026  
**Target:** Weeks 5-8 (4 weeks total)  
**Status:** 🚀 Starting

---

## Overview

Implementing multimodal memory fusion and context-aware proactive delivery for DominusPrime, enabling the agent to remember and retrieve images, videos, and audio alongside text.

## Architecture Summary

### Phase 3: Multimodal Memory (Weeks 5-6)

**Goal:** Enable storage, indexing, and retrieval of images, videos, and audio

**Components:**
1. **Media Processor** - Handle different media types
2. **Content Embedder** - Generate vector embeddings for media
3. **Multimodal Index** - FAISS-based similarity search
4. **Retrieval Engine** - Cross-modal search capabilities

### Phase 4: Proactive Delivery (Weeks 7-8)

**Goal:** Automatically surface relevant memories based on conversation context

**Components:**
1. **Context Monitor** - Analyze conversation flow
2. **Relevance Scorer** - Score memory relevance
3. **Delivery Manager** - Decide when/what to surface
4. **Agent Integration** - Hook into existing system

---

## Week 5: Media Processing & Embedding

### Day 1-2: Foundation
- [x] Create implementation plan
- [ ] Set up directory structure
- [ ] Define data models and schemas
- [ ] Configure dependencies

### Day 3-4: Media Processor
- [ ] Image processor (resize, thumbnail, metadata extraction)
- [ ] Video processor (frame extraction, thumbnail)
- [ ] Audio processor (waveform, metadata)
- [ ] File storage manager

### Day 5-7: Content Embedder
- [ ] CLIP integration for images
- [ ] Whisper integration for audio
- [ ] Video frame embedding
- [ ] Embedding storage and indexing

---

## Week 6: Retrieval & Search

### Day 1-2: Multimodal Index
- [ ] FAISS vector store setup
- [ ] Index creation and management
- [ ] Batch embedding operations
- [ ] Index persistence

### Day 3-4: Retrieval Engine
- [ ] Text-to-media search
- [ ] Media-to-media search
- [ ] Cross-modal search
- [ ] Temporal and contextual filters

### Day 5-7: Integration Testing
- [ ] Unit tests for all components
- [ ] Integration with existing memory system
- [ ] Performance benchmarks
- [ ] Storage quota management

---

## Week 7-8: Proactive Delivery

### Week 7: Context Analysis
- [ ] Context monitor implementation
- [ ] Trigger detection system
- [ ] Relevance scoring algorithm
- [ ] Timing optimization

### Week 8: Delivery & Polish
- [ ] Delivery manager
- [ ] Agent integration hooks
- [ ] Comprehensive testing
- [ ] Documentation

---

## Technical Stack

### New Dependencies

```toml
[project.optional-dependencies]
multimodal = [
    "faiss-cpu>=1.7.4",       # Vector similarity search
    "pillow>=10.0.0",         # Image processing
    "opencv-python>=4.8.0",   # Video processing
    "pytesseract>=0.3.10",    # OCR (optional)
    "transformers>=4.30.0",   # For CLIP
    "torch>=2.0.0",           # PyTorch for embeddings
]
```

### Directory Structure

```
src/dominusprime/agents/memory/
├── multimodal/
│   ├── __init__.py
│   ├── models.py              # Data models
│   ├── processor.py           # Media processor
│   ├── embedder.py            # Content embedder
│   ├── index.py               # FAISS index manager
│   ├── retrieval.py           # Retrieval engine
│   └── storage.py             # File storage manager
├── proactive/
│   ├── __init__.py
│   ├── monitor.py             # Context monitor
│   ├── scorer.py              # Relevance scorer
│   ├── delivery.py            # Delivery manager
│   └── triggers.py            # Trigger detection
└── __init__.py
```

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS media_memory (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    media_type TEXT NOT NULL,  -- 'image', 'video', 'audio'
    file_path TEXT NOT NULL,
    thumbnail_path TEXT,
    file_size INTEGER,
    duration_seconds REAL,
    width INTEGER,
    height INTEGER,
    format TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context_text TEXT,
    auto_description TEXT,
    ocr_text TEXT,
    transcription TEXT,
    embedding_id TEXT,
    metadata JSON
);

CREATE TABLE IF NOT EXISTS media_embeddings (
    id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL,
    embedding_type TEXT NOT NULL,  -- 'clip', 'whisper', 'frame'
    embedding BLOB NOT NULL,
    model_version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_id) REFERENCES media_memory(id)
);

CREATE INDEX idx_media_session ON media_memory(session_id);
CREATE INDEX idx_media_type ON media_memory(media_type);
CREATE INDEX idx_media_created ON media_memory(created_at);
```

---

## Key Features

### 1. Media Processing
- **Images**: Resize, thumbnail, EXIF extraction, OCR
- **Videos**: Frame extraction, thumbnail, duration, resolution
- **Audio**: Transcription, duration, waveform visualization

### 2. Embedding Generation
- **CLIP** for images (vision-language model)
- **Whisper** for audio transcription
- **Video frames** embedded using CLIP

### 3. Search Capabilities
- Text query → Find matching images/videos
- Image query → Find similar images
- Cross-modal → Query with image, get related text
- Temporal → Find media from specific time periods
- Contextual → Find media from specific conversations

### 4. Proactive Delivery
- Detect when conversation context matches past media
- Surface relevant screenshots/images automatically
- Suggest visual references during technical discussions
- Recall past media when discussing similar topics

---

## Success Metrics

### Performance
- **Embedding speed**: < 1s per image
- **Search latency**: < 100ms for top-5 results
- **Storage efficiency**: < 50MB per 100 images
- **Index rebuild**: < 5s for 1000 items

### Quality
- **Search precision**: > 80% for text-to-image
- **Retrieval recall**: > 90% for known items
- **Proactive relevance**: > 70% user acceptance rate

### Scale
- **Max media items**: 10,000 per user
- **Storage quota**: 10GB default (configurable)
- **Concurrent searches**: 10+ simultaneous

---

## Implementation Order

1. **Week 5.1**: Data models, storage, basic image processor
2. **Week 5.2**: CLIP integration, embedding generation
3. **Week 6.1**: FAISS index, basic search
4. **Week 6.2**: Advanced retrieval, integration
5. **Week 7**: Context monitoring and relevance scoring
6. **Week 8**: Proactive delivery and polish

---

## Next Steps

Starting with **Week 5 Day 1-2: Foundation**
- Create directory structure
- Define data models
- Set up base classes
