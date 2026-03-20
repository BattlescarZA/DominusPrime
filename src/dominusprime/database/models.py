# -*- coding: utf-8 -*-
"""Database models and base classes."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json


class Base:
    """Base class for database models."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model from dictionary."""
        raise NotImplementedError


@dataclass
class Experience:
    """Experience model for distilled knowledge."""

    id: str
    type: str
    title: str
    description: str
    context: list[str]
    content: Dict[str, Any]
    confidence: float
    frequency: int
    success_rate: float
    created_at: datetime
    last_used: Optional[datetime]
    updated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "context": json.dumps(self.context),
            "content": json.dumps(self.content),
            "confidence": self.confidence,
            "frequency": self.frequency,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_row(cls, row):
        """Create Experience from database row."""
        return cls(
            id=row["id"],
            type=row["type"],
            title=row["title"],
            description=row["description"],
            context=json.loads(row["context"]),
            content=json.loads(row["content"]),
            confidence=row["confidence"],
            frequency=row["frequency"],
            success_rate=row["success_rate"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_used=datetime.fromisoformat(row["last_used"]) if row["last_used"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


@dataclass
class CommandExecution:
    """Command execution log model."""

    id: str
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    command: str
    risk_level: str
    approval_status: str
    exit_code: Optional[int]
    duration_ms: Optional[int]
    working_dir: str
    channel: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "command": self.command,
            "risk_level": self.risk_level,
            "approval_status": self.approval_status,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "working_dir": self.working_dir,
            "channel": self.channel,
        }

    @classmethod
    def from_row(cls, row):
        """Create CommandExecution from database row."""
        return cls(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            user_id=row["user_id"],
            session_id=row["session_id"],
            command=row["command"],
            risk_level=row["risk_level"],
            approval_status=row["approval_status"],
            exit_code=row["exit_code"],
            duration_ms=row["duration_ms"],
            working_dir=row["working_dir"],
            channel=row["channel"],
        )


@dataclass
class MediaItem:
    """Media item model for multimodal memory."""

    id: str
    type: str  # 'image', 'audio', 'video'
    original_path: str
    storage_path: str
    thumbnail_path: Optional[str]
    file_size: int
    duration: Optional[float]  # for audio/video
    width: Optional[int]  # for images/video
    height: Optional[int]
    created_at: datetime
    session_id: Optional[str]
    conversation_context: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "original_path": self.original_path,
            "storage_path": self.storage_path,
            "thumbnail_path": self.thumbnail_path,
            "file_size": self.file_size,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "created_at": self.created_at.isoformat(),
            "session_id": self.session_id,
            "conversation_context": self.conversation_context,
        }

    @classmethod
    def from_row(cls, row):
        """Create MediaItem from database row."""
        return cls(
            id=row["id"],
            type=row["type"],
            original_path=row["original_path"],
            storage_path=row["storage_path"],
            thumbnail_path=row["thumbnail_path"],
            file_size=row["file_size"],
            duration=row["duration"],
            width=row["width"],
            height=row["height"],
            created_at=datetime.fromisoformat(row["created_at"]),
            session_id=row["session_id"],
            conversation_context=row["conversation_context"],
        )
