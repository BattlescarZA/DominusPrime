#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example usage of the multimodal memory system.

Demonstrates:
- Storing images with context
- Searching by text
- Finding similar images
- Proactive memory delivery
"""
import asyncio
from pathlib import Path

from dominusprime.agents.memory.multimodal import MultimodalMemorySystem
from dominusprime.agents.memory.proactive import (
    ContextMonitor,
    RelevanceScorer,
    DeliveryManager,
)


async def main():
    """Run multimodal memory example."""
    
    # Initialize system
    print("Initializing multimodal memory system...")
    system = MultimodalMemorySystem(
        working_dir=Path("./test_memory"),
        max_storage_gb=1.0,
        use_clip=True,  # Use CLIP for embeddings
        enable_ocr=False,  # Enable if pytesseract installed
        enable_transcription=False,  # Enable for audio
    )
    
    # Example 1: Store an image
    print("\n1. Storing image with context...")
    
    # Assuming you have an image file
    image_path = Path("./example_image.jpg")
    if image_path.exists():
        memory_item = await system.store_media(
            media_path=image_path,
            session_id="session_001",
            context_text="Screenshot of Python debugging session showing stack trace",
        )
        
        print(f"   Stored: {memory_item.id}")
        print(f"   Type: {memory_item.media_type.value}")
        print(f"   Size: {memory_item.file_size} bytes")
    
    # Example 2: Search by text
    print("\n2. Searching for images...")
    
    results = system.search(
        query="python debugging error stack trace",
        top_k=5,
    )
    
    print(f"   Found {len(results)} results")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result.media_item.media_type.value} - Score: {result.similarity_score:.3f}")
        print(f"      Context: {result.media_item.context_text[:60]}...")
    
    # Example 3: Find similar images
    if image_path.exists():
        print("\n3. Finding similar images...")
        
        similar = system.search_similar(
            media_path=image_path,
            top_k=3,
        )
        
        print(f"   Found {len(similar)} similar images")
        for i, result in enumerate(similar, 1):
            print(f"   {i}. Score: {result.similarity_score:.3f}")
    
    # Example 4: Proactive memory delivery
    print("\n4. Proactive memory delivery...")
    
    monitor = ContextMonitor(window_size=5)
    scorer = RelevanceScorer()
    delivery = DeliveryManager(min_relevance=0.4)
    
    # Simulate conversation
    messages = [
        {"role": "user", "content": "I'm debugging a Python application"},
        {"role": "assistant", "content": "I can help with that"},
        {"role": "user", "content": "I'm getting an error with imports"},
    ]
    
    for msg in messages:
        context = monitor.analyze_message(msg)
    
    # Check if should deliver memories
    if delivery.should_deliver(context):
        query = monitor.get_search_query()
        print(f"   Search query: {query}")
        
        # Get candidates
        candidates = system.search(query, top_k=10)
        candidate_dicts = [r.media_item.to_dict() for r in candidates]
        
        # Select and deliver
        selected = delivery.select_memories(
            candidates=candidate_dicts,
            context=context,
            scorer=scorer,
            top_k=3,
        )
        
        message = delivery.deliver(selected)
        if message:
            print(f"\n{message}")
    
    # Example 5: Get statistics
    print("\n5. System statistics:")
    stats = system.get_stats()
    print(f"   Media items: {stats['media_items']}")
    print(f"   Embeddings: {stats['embeddings']}")
    print(f"   Storage used: {stats['storage']['total_mb']:.2f} MB")
    print(f"   Storage quota: {stats['storage']['quota_gb']:.2f} GB")
    
    print("\n✅ Example complete!")


if __name__ == "__main__":
    asyncio.run(main())
