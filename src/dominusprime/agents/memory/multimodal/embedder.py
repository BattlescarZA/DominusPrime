# -*- coding: utf-8 -*-
"""
Content embedder for multimodal memory.

Generates vector embeddings for images, videos, and audio using CLIP and other models.
"""
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np

from .models import EmbeddingType, MediaType

logger = logging.getLogger(__name__)


class ContentEmbedder:
    """
    Generates embeddings for different media types.
    
    Uses:
    - CLIP for images (vision-language model)
    - CLIP for video frames
    - Text embedding models for descriptions
    """
    
    def __init__(
        self,
        model_name: str = "clip-vit-base-patch32",
        device: str = "cpu",
    ):
        """
        Initialize content embedder.
        
        Args:
            model_name: Name of CLIP model to use
            device: Device to run on ('cpu' or 'cuda')
        """
        self.model_name = model_name
        self.device = device
        
        # Lazy load models
        self._clip_model = None
        self._clip_processor = None
        self._tokenizer = None
        
        logger.info(f"ContentEmbedder initialized with {model_name}")
    
    def _load_clip(self):
        """Lazy load CLIP model."""
        if self._clip_model is not None:
            return
        
        try:
            from transformers import CLIPModel, CLIPProcessor
            
            self._clip_model = CLIPModel.from_pretrained(f"openai/{self.model_name}")
            self._clip_processor = CLIPProcessor.from_pretrained(f"openai/{self.model_name}")
            
            # Move to device
            self._clip_model = self._clip_model.to(self.device)
            self._clip_model.eval()
            
            logger.info(f"Loaded CLIP model: {self.model_name}")
        
        except ImportError:
            logger.error("transformers not installed. Install with: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise
    
    def embed_image(self, image_path: Path) -> np.ndarray:
        """
        Generate embedding for an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Embedding vector as numpy array
        """
        self._load_clip()
        
        try:
            from PIL import Image
            import torch
            
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")
            inputs = self._clip_processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate embedding
            with torch.no_grad():
                image_features = self._clip_model.get_image_features(**inputs)
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy
            embedding = image_features.cpu().numpy().flatten()
            
            logger.debug(f"Generated image embedding: shape={embedding.shape}")
            return embedding
        
        except Exception as e:
            logger.error(f"Failed to embed image {image_path}: {e}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for text using CLIP.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        self._load_clip()
        
        try:
            import torch
            
            # Preprocess text
            inputs = self._clip_processor(text=[text], return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate embedding
            with torch.no_grad():
                text_features = self._clip_model.get_text_features(**inputs)
                # Normalize
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy
            embedding = text_features.cpu().numpy().flatten()
            
            logger.debug(f"Generated text embedding: shape={embedding.shape}")
            return embedding
        
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise
    
    def embed_video_frame(self, frame_path: Path) -> np.ndarray:
        """
        Generate embedding for a video frame.
        
        Uses same method as image embedding.
        
        Args:
            frame_path: Path to extracted frame image
            
        Returns:
            Embedding vector as numpy array
        """
        return self.embed_image(frame_path)
    
    def embed_batch_images(self, image_paths: List[Path]) -> np.ndarray:
        """
        Generate embeddings for multiple images in batch.
        
        More efficient than calling embed_image repeatedly.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            Array of embeddings, shape (n_images, embedding_dim)
        """
        self._load_clip()
        
        try:
            from PIL import Image
            import torch
            
            # Load all images
            images = [Image.open(p).convert("RGB") for p in image_paths]
            
            # Batch preprocess
            inputs = self._clip_processor(images=images, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate embeddings
            with torch.no_grad():
                image_features = self._clip_model.get_image_features(**inputs)
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy
            embeddings = image_features.cpu().numpy()
            
            logger.debug(f"Generated batch embeddings: shape={embeddings.shape}")
            return embeddings
        
        except Exception as e:
            logger.error(f"Failed to batch embed images: {e}")
            raise
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Normalize
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2)
        
        # Clip to [0, 1] range
        return float(np.clip(similarity, 0, 1))
    
    def get_embedding_dim(self) -> int:
        """Get dimensionality of embeddings."""
        self._load_clip()
        return self._clip_model.config.projection_dim


class SimpleEmbedder:
    """
    Fallback embedder when CLIP is not available.
    
    Uses basic image features (histograms, etc.)
    """
    
    def __init__(self):
        logger.warning("Using SimpleEmbedder - limited functionality")
    
    def embed_image(self, image_path: Path) -> np.ndarray:
        """Generate simple histogram-based embedding."""
        try:
            from PIL import Image
            
            img = Image.open(image_path).convert("RGB")
            img = img.resize((256, 256))  # Standardize size
            
            # Compute color histogram
            hist_r = np.histogram(np.array(img)[:,:,0], bins=32, range=(0,256))[0]
            hist_g = np.histogram(np.array(img)[:,:,1], bins=32, range=(0,256))[0]
            hist_b = np.histogram(np.array(img)[:,:,2], bins=32, range=(0,256))[0]
            
            # Concatenate and normalize
            embedding = np.concatenate([hist_r, hist_g, hist_b])
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding.astype(np.float32)
        
        except Exception as e:
            logger.error(f"Failed to embed with SimpleEmbedder: {e}")
            # Return random embedding as last resort
            return np.random.randn(96).astype(np.float32)
    
    def embed_text(self, text: str) -> np.ndarray:
        """Simple text embedding (character frequency)."""
        # Very basic - just for fallback
        embedding = np.zeros(96, dtype=np.float32)
        for char in text.lower()[:96]:
            idx = ord(char) % 96
            embedding[idx] += 1
        
        if np.linalg.norm(embedding) > 0:
            embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    def get_embedding_dim(self) -> int:
        return 96


def get_embedder(use_clip: bool = True, **kwargs) -> ContentEmbedder:
    """
    Factory function to get appropriate embedder.
    
    Args:
        use_clip: Whether to use CLIP (requires transformers + torch)
        **kwargs: Arguments for ContentEmbedder
        
    Returns:
        ContentEmbedder or SimpleEmbedder instance
    """
    if use_clip:
        try:
            return ContentEmbedder(**kwargs)
        except Exception as e:
            logger.warning(f"Failed to initialize CLIP embedder: {e}")
            logger.warning("Falling back to SimpleEmbedder")
            return SimpleEmbedder()
    else:
        return SimpleEmbedder()


__all__ = ["ContentEmbedder", "SimpleEmbedder", "get_embedder"]
