# -*- coding: utf-8 -*-
"""Hook for automatic multimodal memory capture and proactive delivery."""
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from agentscope.message import Msg

logger = logging.getLogger(__name__)


class MultimodalMemoryHook:
    """Hook for integrating multimodal memory into agent conversations."""
    
    def __init__(
        self,
        memory_system,
        enable_auto_capture: bool = True,
        enable_proactive: bool = True,
        session_id: Optional[str] = None,
    ):
        """Initialize the multimodal memory hook.
        
        Args:
            memory_system: MultimodalMemorySystem instance
            enable_auto_capture: Whether to automatically capture media from messages
            enable_proactive: Whether to enable proactive memory delivery
            session_id: Session ID for memory association
        """
        self.memory_system = memory_system
        self.enable_auto_capture = enable_auto_capture
        self.enable_proactive = enable_proactive
        self.session_id = session_id or "default"
        
        # Set session ID on memory system
        if hasattr(memory_system, 'current_session_id'):
            memory_system.current_session_id = self.session_id
    
    async def before_agent_reply(
        self,
        message: Msg,
        agent_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Hook called before agent generates a reply.
        
        This hook:
        1. Captures any media attached to user messages
        2. Checks for proactive memory delivery opportunities
        
        Args:
            message: The current message being processed
            agent_state: Current agent state dictionary
            
        Returns:
            Updated agent state with memory context
        """
        if self.memory_system is None:
            return agent_state
        
        try:
            # Auto-capture media from message
            if self.enable_auto_capture:
                await self._auto_capture_media(message)
            
            # Check for proactive delivery
            if self.enable_proactive:
                proactive_memories = await self._get_proactive_memories(message)
                if proactive_memories:
                    agent_state['proactive_memories'] = proactive_memories
            
        except Exception as e:
            logger.error(f"Error in multimodal memory hook: {e}", exc_info=True)
        
        return agent_state
    
    async def _auto_capture_media(self, message: Msg):
        """Automatically capture media from message attachments.
        
        Args:
            message: Message to scan for media
        """
        # Check if message has content with media attachments
        if not hasattr(message, 'content'):
            return
        
        content = message.content
        if isinstance(content, str):
            return
        
        # Handle different content formats
        if isinstance(content, list):
            for item in content:
                await self._process_content_item(item, message)
        elif isinstance(content, dict):
            await self._process_content_item(content, message)
    
    async def _process_content_item(self, item: Any, message: Msg):
        """Process a single content item for media.
        
        Args:
            item: Content item to process
            message: Parent message for context
        """
        if not isinstance(item, dict):
            return
        
        # Check for different media types
        media_path = None
        media_type = item.get('type', '')
        
        # Image content
        if media_type == 'image' or 'image_url' in item:
            if 'url' in item:
                media_path = item['url']
            elif 'image_url' in item:
                media_path = item['image_url'].get('url')
        
        # File attachments
        elif media_type == 'file' or 'file_path' in item:
            media_path = item.get('file_path') or item.get('path')
        
        if media_path:
            # Extract context from message
            context_text = self._extract_context(message)
            
            try:
                # Store the media
                await self.memory_system.store_media(
                    media_path=Path(media_path),
                    session_id=self.session_id,
                    context_text=context_text
                )
                logger.info(f"Auto-captured media: {media_path}")
            except Exception as e:
                logger.warning(f"Failed to auto-capture media {media_path}: {e}")
    
    def _extract_context(self, message: Msg) -> str:
        """Extract context text from message.
        
        Args:
            message: Message to extract context from
            
        Returns:
            Context description string
        """
        context_parts = []
        
        # Add message role
        if hasattr(message, 'role'):
            context_parts.append(f"From: {message.role}")
        
        # Add text content
        if hasattr(message, 'content'):
            if isinstance(message.content, str):
                context_parts.append(message.content[:200])
            elif isinstance(message.content, list):
                for item in message.content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text = item.get('text', '')
                        if text:
                            context_parts.append(text[:200])
                            break
        
        return " - ".join(context_parts) if context_parts else "Captured from conversation"
    
    async def _get_proactive_memories(self, message: Msg) -> Optional[list]:
        """Get proactive memory suggestions based on message context.
        
        Args:
            message: Current message to analyze
            
        Returns:
            List of proactive memories or None
        """
        if not hasattr(self.memory_system, 'get_proactive_memories'):
            return None
        
        try:
            # Convert message to dict format expected by memory system
            message_dict = {
                'role': getattr(message, 'role', 'user'),
                'content': getattr(message, 'content', '')
            }
            
            memories = self.memory_system.get_proactive_memories(
                message=message_dict,
                max_memories=3
            )
            
            return memories if memories else None
            
        except Exception as e:
            logger.warning(f"Error getting proactive memories: {e}")
            return None
    
    async def after_agent_reply(
        self,
        message: Msg,
        response: Any,
        agent_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Hook called after agent generates a reply.
        
        Args:
            message: The message that was processed
            response: The agent's response
            agent_state: Current agent state
            
        Returns:
            Updated agent state
        """
        # Currently no post-processing needed
        # Could add response analysis or memory updates here
        return agent_state
    
    async def on_session_end(self):
        """Hook called when session ends.
        
        Performs cleanup and final memory operations.
        """
        if self.memory_system is None:
            return
        
        try:
            # Could add session summary or cleanup here
            logger.info(f"Multimodal memory session ended: {self.session_id}")
        except Exception as e:
            logger.error(f"Error in session end hook: {e}", exc_info=True)
    
    def set_session_id(self, session_id: str):
        """Update the session ID for memory operations.
        
        Args:
            session_id: New session ID
        """
        self.session_id = session_id
        if hasattr(self.memory_system, 'current_session_id'):
            self.memory_system.current_session_id = session_id
    
    def enable_features(
        self,
        auto_capture: Optional[bool] = None,
        proactive: Optional[bool] = None,
    ):
        """Enable or disable hook features.
        
        Args:
            auto_capture: Enable/disable automatic media capture
            proactive: Enable/disable proactive delivery
        """
        if auto_capture is not None:
            self.enable_auto_capture = auto_capture
        if proactive is not None:
            self.enable_proactive = proactive


def create_multimodal_memory_hook(
    memory_system,
    enable_auto_capture: bool = True,
    enable_proactive: bool = True,
    session_id: Optional[str] = None,
) -> MultimodalMemoryHook:
    """Factory function to create a multimodal memory hook.
    
    Args:
        memory_system: MultimodalMemorySystem instance
        enable_auto_capture: Whether to auto-capture media
        enable_proactive: Whether to enable proactive delivery
        session_id: Session ID for memories
        
    Returns:
        Configured MultimodalMemoryHook instance
    """
    return MultimodalMemoryHook(
        memory_system=memory_system,
        enable_auto_capture=enable_auto_capture,
        enable_proactive=enable_proactive,
        session_id=session_id,
    )
