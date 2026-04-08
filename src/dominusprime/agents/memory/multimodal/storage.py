# -*- coding: utf-8 -*-
"""
File storage manager for multimodal memory.

Handles storing, organizing, and managing media files on disk.
"""
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Optional, Tuple

from .models import MediaType

logger = logging.getLogger(__name__)


class MediaStorageManager:
    """
    Manages file storage for multimedia content.
    
    Organizes files by type and session, handles deduplication,
    enforces storage quotas.
    """
    
    def __init__(
        self,
        storage_dir: Path,
        max_storage_gb: float = 10.0,
        create_thumbnails: bool = True,
    ):
        """
        Initialize storage manager.
        
        Args:
            storage_dir: Root directory for media storage
            max_storage_gb: Maximum storage in GB
            create_thumbnails: Whether to create thumbnails
        """
        self.storage_dir = Path(storage_dir)
        self.max_storage_bytes = int(max_storage_gb * 1024 * 1024 * 1024)
        self.create_thumbnails = create_thumbnails
        
        # Create directory structure
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._create_directories()
        
        logger.info(f"Media storage initialized at {self.storage_dir}")
    
    def _create_directories(self) -> None:
        """Create organized directory structure."""
        for media_type in MediaType:
            (self.storage_dir / media_type.value).mkdir(exist_ok=True)
            (self.storage_dir / media_type.value / "thumbnails").mkdir(exist_ok=True)
    
    def store_media(
        self,
        source_path: Path,
        media_type: MediaType,
        session_id: str,
        media_id: str,
    ) -> Tuple[Path, Optional[Path]]:
        """
        Store media file.
        
        Args:
            source_path: Path to source file
            media_type: Type of media
            session_id: Session ID
            media_id: Unique media ID
            
        Returns:
            Tuple of (stored_path, thumbnail_path)
        """
        # Check storage quota
        if not self._check_quota(source_path.stat().st_size):
            raise RuntimeError(f"Storage quota exceeded ({self.max_storage_bytes} bytes)")
        
        # Determine destination
        file_extension = source_path.suffix
        destination = self._get_storage_path(media_type, session_id, media_id, file_extension)
        
        # Copy file
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        
        logger.info(f"Stored {media_type.value}: {destination}")
        
        # Create thumbnail if applicable
        thumbnail_path = None
        if self.create_thumbnails and media_type in [MediaType.IMAGE, MediaType.VIDEO]:
            thumbnail_path = self._create_thumbnail(destination, media_type, session_id, media_id)
        
        return destination, thumbnail_path
    
    def _get_storage_path(
        self,
        media_type: MediaType,
        session_id: str,
        media_id: str,
        extension: str,
    ) -> Path:
        """Get storage path for media file."""
        # Organize by type/session/id
        return (
            self.storage_dir
            / media_type.value
            / session_id[:8]  # First 8 chars of session for organization
            / f"{media_id}{extension}"
        )
    
    def _create_thumbnail(
        self,
        source_path: Path,
        media_type: MediaType,
        session_id: str,
        media_id: str,
    ) -> Optional[Path]:
        """Create thumbnail for media."""
        try:
            from PIL import Image
        except ImportError:
            logger.warning("Pillow not installed, skipping thumbnail")
            return None
        
        thumbnail_path = (
            self.storage_dir
            / media_type.value
            / "thumbnails"
            / session_id[:8]
            / f"{media_id}_thumb.jpg"
        )
        
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if media_type == MediaType.IMAGE:
                # Create image thumbnail
                with Image.open(source_path) as img:
                    img.thumbnail((256, 256))
                    img.save(thumbnail_path, "JPEG", quality=85)
            
            elif media_type == MediaType.VIDEO:
                # Extract first frame for video thumbnail
                try:
                    import cv2
                    cap = cv2.VideoCapture(str(source_path))
                    ret, frame = cap.read()
                    if ret:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(frame_rgb)
                        img.thumbnail((256, 256))
                        img.save(thumbnail_path, "JPEG", quality=85)
                    cap.release()
                except ImportError:
                    logger.warning("OpenCV not installed, skipping video thumbnail")
                    return None
            
            logger.debug(f"Created thumbnail: {thumbnail_path}")
            return thumbnail_path
        
        except Exception as e:
            logger.error(f"Failed to create thumbnail: {e}")
            return None
    
    def _check_quota(self, new_file_size: int) -> bool:
        """Check if adding new file would exceed quota."""
        current_usage = self._get_storage_usage()
        return (current_usage + new_file_size) <= self.max_storage_bytes
    
    def _get_storage_usage(self) -> int:
        """Get current storage usage in bytes."""
        total = 0
        for file_path in self.storage_dir.rglob("*"):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for deduplication."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def delete_media(self, media_path: Path, thumbnail_path: Optional[Path] = None) -> None:
        """Delete media file and thumbnail."""
        try:
            if media_path.exists():
                media_path.unlink()
                logger.info(f"Deleted media: {media_path}")
            
            if thumbnail_path and thumbnail_path.exists():
                thumbnail_path.unlink()
                logger.debug(f"Deleted thumbnail: {thumbnail_path}")
        
        except Exception as e:
            logger.error(f"Failed to delete media: {e}")
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics."""
        usage = self._get_storage_usage()
        
        return {
            "total_bytes": usage,
            "total_mb": usage / (1024 * 1024),
            "total_gb": usage / (1024 * 1024 * 1024),
            "quota_bytes": self.max_storage_bytes,
            "quota_gb": self.max_storage_bytes / (1024 * 1024 * 1024),
            "usage_percent": (usage / self.max_storage_bytes) * 100 if self.max_storage_bytes > 0 else 0,
        }


__all__ = ["MediaStorageManager"]
