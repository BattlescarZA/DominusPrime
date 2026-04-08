# -*- coding: utf-8 -*-
"""
Media processor for multimodal memory.

Handles extraction of metadata, text (OCR), and transcriptions from media files.
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

from .models import MediaType

logger = logging.getLogger(__name__)


class MediaProcessor:
    """
    Processes different types of media to extract metadata and content.
    
    Capabilities:
    - Extract image EXIF data and dimensions
    - Extract video metadata (duration, resolution, frames)
    - OCR text from images
    - Transcribe audio
    """
    
    def __init__(
        self,
        enable_ocr: bool = False,
        enable_transcription: bool = False,
    ):
        """
        Initialize media processor.
        
        Args:
            enable_ocr: Enable text extraction from images
            enable_transcription: Enable audio transcription
        """
        self.enable_ocr = enable_ocr
        self.enable_transcription = enable_transcription
        
        # Lazy import of heavy dependencies
        self._pil_image = None
        self._cv2 = None
        self._pytesseract = None
    
    def process_media(
        self,
        file_path: Path,
        media_type: MediaType,
    ) -> Dict:
        """
        Process media file and extract metadata.
        
        Args:
            file_path: Path to media file
            media_type: Type of media
            
        Returns:
            Dictionary with extracted metadata
        """
        if media_type == MediaType.IMAGE:
            return self.process_image(file_path)
        elif media_type == MediaType.VIDEO:
            return self.process_video(file_path)
        elif media_type == MediaType.AUDIO:
            return self.process_audio(file_path)
        else:
            return self._get_basic_metadata(file_path)
    
    def process_image(self, file_path: Path) -> Dict:
        """
        Process image file.
        
        Extracts:
        - Dimensions (width, height)
        - Format
        - EXIF data
        - OCR text (if enabled)
        """
        try:
            from PIL import Image
            self._pil_image = Image
        except ImportError:
            logger.warning("Pillow not installed, limited image processing")
            return self._get_basic_metadata(file_path)
        
        metadata = self._get_basic_metadata(file_path)
        
        try:
            with Image.open(file_path) as img:
                metadata.update({
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                })
                
                # Extract EXIF if available
                exif = img.getexif()
                if exif:
                    metadata["exif"] = dict(exif)
                
                # OCR text extraction
                if self.enable_ocr:
                    metadata["ocr_text"] = self._extract_text_ocr(file_path)
        
        except Exception as e:
            logger.error(f"Failed to process image {file_path}: {e}")
        
        return metadata
    
    def process_video(self, file_path: Path) -> Dict:
        """
        Process video file.
        
        Extracts:
        - Duration
        - Resolution (width, height)
        - Frame rate
        - Codec
        """
        try:
            import cv2
            self._cv2 = cv2
        except ImportError:
            logger.warning("OpenCV not installed, limited video processing")
            return self._get_basic_metadata(file_path)
        
        metadata = self._get_basic_metadata(file_path)
        
        try:
            cap = cv2.VideoCapture(str(file_path))
            
            if cap.isOpened():
                metadata.update({
                    "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    "fps": cap.get(cv2.CAP_PROP_FPS),
                    "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                    "duration_seconds": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
                        if cap.get(cv2.CAP_PROP_FPS) > 0 else 0,
                })
            
            cap.release()
        
        except Exception as e:
            logger.error(f"Failed to process video {file_path}: {e}")
        
        return metadata
    
    def process_audio(self, file_path: Path) -> Dict:
        """
        Process audio file.
        
        Extracts:
        - Duration
        - Sample rate
        - Channels
        - Transcription (if enabled)
        """
        metadata = self._get_basic_metadata(file_path)
        
        try:
            # Try to get audio info using wave for WAV files
            if file_path.suffix.lower() == '.wav':
                import wave
                with wave.open(str(file_path), 'rb') as wav:
                    metadata.update({
                        "channels": wav.getnchannels(),
                        "sample_rate": wav.getframerate(),
                        "duration_seconds": wav.getnframes() / wav.getframerate(),
                    })
            
            # Transcription
            if self.enable_transcription:
                metadata["transcription"] = self._transcribe_audio(file_path)
        
        except Exception as e:
            logger.error(f"Failed to process audio {file_path}: {e}")
        
        return metadata
    
    def _get_basic_metadata(self, file_path: Path) -> Dict:
        """Get basic file metadata."""
        stat = file_path.stat()
        return {
            "file_size": stat.st_size,
            "format": file_path.suffix.lstrip('.').lower(),
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
        }
    
    def _extract_text_ocr(self, image_path: Path) -> Optional[str]:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            with Image.open(image_path) as img:
                text = pytesseract.image_to_string(img)
                return text.strip() if text else None
        
        except ImportError:
            logger.warning("pytesseract not installed, skipping OCR")
            return None
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return None
    
    def _transcribe_audio(self, audio_path: Path) -> Optional[str]:
        """Transcribe audio using Whisper."""
        try:
            # Note: This is a placeholder for Whisper integration
            # Full implementation would use openai.whisper or whisper-api
            logger.info("Audio transcription not yet implemented")
            return None
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def extract_video_frame(
        self,
        video_path: Path,
        frame_number: int = 0,
    ) -> Optional[Path]:
        """
        Extract a specific frame from video.
        
        Args:
            video_path: Path to video file
            frame_number: Frame to extract (0 for first frame)
            
        Returns:
            Path to extracted frame image
        """
        try:
            import cv2
            import tempfile
            
            cap = cv2.VideoCapture(str(video_path))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Save frame to temporary file
                temp_file = Path(tempfile.mktemp(suffix='.jpg'))
                cv2.imwrite(str(temp_file), frame)
                return temp_file
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to extract frame: {e}")
            return None


__all__ = ["MediaProcessor"]
