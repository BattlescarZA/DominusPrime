# -*- coding: utf-8 -*-
"""Multimodal embedding generation."""

import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path

from .models import MediaItem, MediaEmbedding, MediaType


class MultimodalEmbedder:
    """Generates embeddings for multimodal content."""
    
    def __init__(
        self,
        visual_model: Optional[str] = None,
        text_model: Optional[str] = None,
        audio_model: Optional[str] = None,
    ):
        """Initialize multimodal embedder.
        
        Args:
            visual_model: Model name for visual embeddings (CLIP, etc.)
            text_model: Model name for text embeddings
            audio_model: Model name for audio embeddings
        """
        self.visual_model = visual_model or "clip-vit-base-patch32"
        self.text_model = text_model or "sentence-transformers/all-MiniLM-L6-v2"
        self.audio_model = audio_model or "panns-cnn14"
        
        self._visual_encoder = None
        self._text_encoder = None
        self._audio_encoder = None
    
    async def _load_visual_encoder(self):
        """Lazy load visual encoder."""
        if self._visual_encoder is None:
            try:
                # Try to import transformers and load CLIP
                from transformers import CLIPProcessor, CLIPModel
                
                self._visual_encoder = {
                    "model": await asyncio.to_thread(CLIPModel.from_pretrained, self.visual_model),
                    "processor": await asyncio.to_thread(CLIPProcessor.from_pretrained, self.visual_model),
                }
            except ImportError:
                # Fallback: return dummy encoder
                self._visual_encoder = None
    
    async def _load_text_encoder(self):
        """Lazy load text encoder."""
        if self._text_encoder is None:
            try:
                # Try to import sentence-transformers
                from sentence_transformers import SentenceTransformer
                
                self._text_encoder = await asyncio.to_thread(
                    SentenceTransformer, self.text_model
                )
            except ImportError:
                self._text_encoder = None
    
    async def _load_audio_encoder(self):
        """Lazy load audio encoder."""
        if self._audio_encoder is None:
            # Audio encoding would require specialized libraries
            # For now, return None (to be implemented)
            self._audio_encoder = None
    
    async def embed_image(self, media_item: MediaItem) -> MediaEmbedding:
        """Generate visual embedding for image.
        
        Args:
            media_item: MediaItem containing image
            
        Returns:
            MediaEmbedding with visual features
        """
        await self._load_visual_encoder()
        
        if self._visual_encoder is None:
            # Fallback: create zero embedding
            return MediaEmbedding(
                media_item_id=media_item.id,
                embedding_type="visual",
                vector=[0.0] * 512,  # Standard CLIP dimension
                model_name="none",
                dimension=512,
                metadata={"error": "Visual encoder not available. Install transformers."},
            )
        
        try:
            from PIL import Image
            import torch
            
            # Load image
            image = await asyncio.to_thread(Image.open, media_item.file_path)
            
            # Process and encode
            inputs = self._visual_encoder["processor"](
                images=image, return_tensors="pt"
            )
            
            with torch.no_grad():
                outputs = self._visual_encoder["model"].get_image_features(**inputs)
                embedding = outputs[0].cpu().numpy().tolist()
            
            return MediaEmbedding(
                media_item_id=media_item.id,
                embedding_type="visual",
                vector=embedding,
                model_name=self.visual_model,
                dimension=len(embedding),
            )
        
        except Exception as e:
            # Return zero embedding on error
            return MediaEmbedding(
                media_item_id=media_item.id,
                embedding_type="visual",
                vector=[0.0] * 512,
                model_name="error",
                dimension=512,
                metadata={"error": str(e)},
            )
    
    async def embed_text(self, text: str, media_item_id: str) -> MediaEmbedding:
        """Generate text embedding.
        
        Args:
            text: Text content to embed
            media_item_id: Associated media item ID
            
        Returns:
            MediaEmbedding with text features
        """
        await self._load_text_encoder()
        
        if self._text_encoder is None:
            # Fallback: simple hash-based embedding
            vector = [hash(text[i:i+10]) % 100 / 100.0 for i in range(0, min(len(text), 384), 10)]
            vector.extend([0.0] * (384 - len(vector)))  # Pad to 384
            
            return MediaEmbedding(
                media_item_id=media_item_id,
                embedding_type="text",
                vector=vector,
                model_name="hash",
                dimension=384,
                metadata={"error": "Text encoder not available. Install sentence-transformers."},
            )
        
        try:
            # Generate embedding
            embedding = await asyncio.to_thread(
                self._text_encoder.encode, text, convert_to_numpy=True
            )
            
            return MediaEmbedding(
                media_item_id=media_item_id,
                embedding_type="text",
                vector=embedding.tolist(),
                model_name=self.text_model,
                dimension=len(embedding),
            )
        
        except Exception as e:
            # Return zero embedding on error
            return MediaEmbedding(
                media_item_id=media_item_id,
                embedding_type="text",
                vector=[0.0] * 384,
                model_name="error",
                dimension=384,
                metadata={"error": str(e)},
            )
    
    async def embed_audio(self, media_item: MediaItem) -> MediaEmbedding:
        """Generate audio embedding.
        
        Args:
            media_item: MediaItem containing audio
            
        Returns:
            MediaEmbedding with audio features
        """
        # Audio embedding not yet implemented
        # Would require specialized audio processing libraries
        return MediaEmbedding(
            media_item_id=media_item.id,
            embedding_type="audio",
            vector=[0.0] * 512,
            model_name="not_implemented",
            dimension=512,
            metadata={"note": "Audio embedding not yet implemented"},
        )
    
    async def embed_media(self, media_item: MediaItem) -> List[MediaEmbedding]:
        """Generate all appropriate embeddings for media item.
        
        Args:
            media_item: MediaItem to embed
            
        Returns:
            List of MediaEmbedding objects
        """
        embeddings = []
        
        # Visual embedding for images
        if media_item.media_type == MediaType.IMAGE:
            visual_emb = await self.embed_image(media_item)
            embeddings.append(visual_emb)
        
        # Audio embedding for audio/video
        if media_item.media_type in (MediaType.AUDIO, MediaType.VIDEO):
            audio_emb = await self.embed_audio(media_item)
            embeddings.append(audio_emb)
        
        # Text embedding for description or detected text
        if media_item.description or media_item.detected_text:
            text_content = media_item.description or media_item.detected_text or ""
            text_emb = await self.embed_text(text_content, media_item.id)
            embeddings.append(text_emb)
        
        # Text embedding for documents
        if media_item.media_type == MediaType.DOCUMENT and media_item.detected_text:
            text_emb = await self.embed_text(media_item.detected_text, media_item.id)
            embeddings.append(text_emb)
        
        return embeddings
    
    async def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        if len(embedding1) != len(embedding2):
            return 0.0
        
        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return max(0.0, min(1.0, (similarity + 1) / 2))  # Normalize to [0, 1]
