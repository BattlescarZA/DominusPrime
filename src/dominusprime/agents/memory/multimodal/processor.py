# -*- coding: utf-8 -*-
"""Media processing for multimodal memory system."""

import asyncio
import hashlib
import mimetypes
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import MediaItem, MediaType, ProcessingStatus


class MediaProcessor:
    """Processes multimodal content for storage and analysis."""
    
    # Supported MIME types
    SUPPORTED_TYPES = {
        MediaType.IMAGE: [
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "image/bmp", "image/tiff", "image/svg+xml"
        ],
        MediaType.AUDIO: [
            "audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4",
            "audio/webm", "audio/flac", "audio/aac"
        ],
        MediaType.VIDEO: [
            "video/mp4", "video/webm", "video/ogg", "video/mpeg",
            "video/quicktime", "video/x-msvideo"
        ],
        MediaType.DOCUMENT: [
            "application/pdf", "text/plain", "text/markdown",
            "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ],
    }
    
    def __init__(self, storage_dir: Path):
        """Initialize media processor.
        
        Args:
            storage_dir: Directory to store processed media files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each media type
        for media_type in MediaType:
            (self.storage_dir / media_type.value).mkdir(exist_ok=True)
    
    def _determine_media_type(self, mime_type: str) -> Optional[MediaType]:
        """Determine media type from MIME type."""
        for media_type, mime_types in self.SUPPORTED_TYPES.items():
            if mime_type in mime_types:
                return media_type
        return None
    
    def _generate_id(self, file_path: str, content: bytes) -> str:
        """Generate unique ID for media item."""
        hasher = hashlib.sha256()
        hasher.update(file_path.encode())
        hasher.update(content)
        return hasher.hexdigest()[:16]
    
    async def process_file(
        self,
        file_path: str,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        user_context: Optional[str] = None,
    ) -> MediaItem:
        """Process a media file and create MediaItem.
        
        Args:
            file_path: Path to the media file
            session_id: Associated session ID
            conversation_id: Associated conversation ID
            user_context: Additional user context
            
        Returns:
            Processed MediaItem
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        content = await asyncio.to_thread(path.read_bytes)
        file_size = len(content)
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Determine media type
        media_type = self._determine_media_type(mime_type)
        if not media_type:
            raise ValueError(f"Unsupported media type: {mime_type}")
        
        # Generate unique ID
        item_id = self._generate_id(str(path), content)
        
        # Create storage path
        storage_path = self.storage_dir / media_type.value / f"{item_id}{path.suffix}"
        
        # Copy file to storage
        await asyncio.to_thread(storage_path.write_bytes, content)
        
        # Create MediaItem
        media_item = MediaItem(
            id=item_id,
            media_type=media_type,
            file_path=str(storage_path),
            original_filename=path.name,
            mime_type=mime_type,
            file_size=file_size,
            session_id=session_id,
            conversation_id=conversation_id,
            user_context=user_context,
        )
        
        # Extract metadata based on type
        try:
            if media_type == MediaType.IMAGE:
                await self._process_image(media_item, storage_path)
            elif media_type == MediaType.AUDIO:
                await self._process_audio(media_item, storage_path)
            elif media_type == MediaType.VIDEO:
                await self._process_video(media_item, storage_path)
            elif media_type == MediaType.DOCUMENT:
                await self._process_document(media_item, storage_path)
            
            media_item.status = ProcessingStatus.COMPLETED
            media_item.processed_at = datetime.utcnow()
        except Exception as e:
            media_item.status = ProcessingStatus.FAILED
            media_item.metadata["error"] = str(e)
        
        return media_item
    
    async def _process_image(self, item: MediaItem, path: Path) -> None:
        """Extract metadata from image."""
        try:
            # Try to import PIL (Pillow)
            from PIL import Image
            
            img = await asyncio.to_thread(Image.open, str(path))
            item.width = img.width
            item.height = img.height
            
            # Extract EXIF data if available
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                if exif:
                    item.metadata["exif"] = {k: str(v) for k, v in exif.items() if isinstance(k, int)}
            
            # Basic image info
            item.metadata["format"] = img.format
            item.metadata["mode"] = img.mode
            
        except ImportError:
            # PIL not available, store basic info
            item.metadata["note"] = "Install Pillow for advanced image processing"
    
    async def _process_audio(self, item: MediaItem, path: Path) -> None:
        """Extract metadata from audio."""
        try:
            # Try to import mutagen for audio metadata
            from mutagen import File as AudioFile
            
            audio = await asyncio.to_thread(AudioFile, str(path))
            if audio:
                item.duration = audio.info.length if hasattr(audio.info, 'length') else None
                
                # Extract tags
                if audio.tags:
                    item.metadata["tags"] = dict(audio.tags)
                    
                    # Extract common tags
                    if "title" in audio.tags:
                        item.metadata["title"] = str(audio.tags["title"][0])
                    if "artist" in audio.tags:
                        item.metadata["artist"] = str(audio.tags["artist"][0])
        
        except ImportError:
            item.metadata["note"] = "Install mutagen for audio metadata extraction"
    
    async def _process_video(self, item: MediaItem, path: Path) -> None:
        """Extract metadata from video."""
        try:
            # Try to import opencv for video processing
            import cv2
            
            cap = cv2.VideoCapture(str(path))
            if cap.isOpened():
                item.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                item.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                item.duration = frame_count / fps if fps > 0 else None
                
                item.metadata["fps"] = fps
                item.metadata["frame_count"] = frame_count
                
                cap.release()
        
        except ImportError:
            item.metadata["note"] = "Install opencv-python for video processing"
    
    async def _process_document(self, item: MediaItem, path: Path) -> None:
        """Extract text from documents."""
        if item.mime_type in ("text/plain", "text/markdown"):
            # Read text content directly
            content = await asyncio.to_thread(path.read_text, encoding="utf-8")
            item.detected_text = content[:10000]  # Limit to first 10k chars
            item.metadata["char_count"] = len(content)
        else:
            # PDF or Word documents would need additional libraries
            item.metadata["note"] = "Install PyPDF2 or python-docx for document text extraction"
    
    async def process_url(
        self,
        url: str,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        user_context: Optional[str] = None,
    ) -> MediaItem:
        """Download and process media from URL.
        
        Args:
            url: URL to media file
            session_id: Associated session ID
            conversation_id: Associated conversation ID
            user_context: Additional user context
            
        Returns:
            Processed MediaItem
        """
        # Download file
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download from {url}: {response.status}")
                
                content = await response.read()
                mime_type = response.headers.get("Content-Type", "application/octet-stream")
                
                # Determine file extension
                media_type = self._determine_media_type(mime_type)
                if not media_type:
                    raise ValueError(f"Unsupported media type: {mime_type}")
                
                # Generate ID and storage path
                item_id = self._generate_id(url, content)
                ext = mimetypes.guess_extension(mime_type) or ".bin"
                storage_path = self.storage_dir / media_type.value / f"{item_id}{ext}"
                
                # Save file
                await asyncio.to_thread(storage_path.write_bytes, content)
                
                # Process as regular file
                return await self.process_file(
                    str(storage_path),
                    session_id=session_id,
                    conversation_id=conversation_id,
                    user_context=user_context,
                )
    
    async def delete_media(self, media_item: MediaItem) -> bool:
        """Delete media file from storage.
        
        Args:
            media_item: MediaItem to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            path = Path(media_item.file_path)
            if path.exists():
                await asyncio.to_thread(path.unlink)
                return True
        except Exception:
            pass
        return False
