# -*- coding: utf-8 -*-
"""Multimodal memory tools for storing and retrieving media with context."""
from pathlib import Path
from typing import Optional, List
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock


def create_multimodal_memory_tools(memory_system):
    """Create multimodal memory tool functions with bound memory system.
    
    Args:
        memory_system: MultimodalMemorySystem instance
        
    Returns:
        Dictionary of tool functions
    """
    
    async def store_media(
        media_path: str,
        context_text: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> ToolResponse:
        """
        Store media (image, video, audio, document) with contextual information.
        
        Use this tool to remember important media files like screenshots, diagrams,
        documents, or recordings for future reference.
        
        Args:
            media_path (`str`):
                Path to the media file to store.
            context_text (`str`, optional):
                Descriptive text about the media content and context.
            session_id (`str`, optional):
                Session ID to associate with this memory. Defaults to current session.
                
        Returns:
            `ToolResponse`:
                Confirmation with memory ID and storage details.
        """
        if memory_system is None:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Error: Multimodal memory system is not enabled.",
                    ),
                ],
            )
        
        try:
            media_file = Path(media_path)
            if not media_file.exists():
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"Error: Media file not found: {media_path}",
                        ),
                    ],
                )
            
            # Use current session if not specified
            if session_id is None:
                session_id = getattr(memory_system, 'current_session_id', 'default')
            
            # Store media
            memory_item = await memory_system.store_media(
                media_path=media_file,
                session_id=session_id,
                context_text=context_text
            )
            
            result_text = f"""Media stored successfully!

Memory ID: {memory_item.id}
Type: {memory_item.media_type.value}
Size: {memory_item.file_size / 1024:.2f} KB
Session: {memory_item.session_id}"""
            
            if context_text:
                result_text += f"\nContext: {context_text[:100]}..."
            
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=result_text,
                    ),
                ],
            )
            
        except Exception as e:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error storing media: {str(e)}",
                    ),
                ],
            )
    
    async def search_memories(
        query: str,
        media_types: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        top_k: int = 5,
    ) -> ToolResponse:
        """
        Search stored memories using text or semantic queries.
        
        Use this tool to find relevant media from past conversations, screenshots,
        documents, or recordings based on their content or context.
        
        Args:
            query (`str`):
                Search query describing what you're looking for.
            media_types (`List[str]`, optional):
                Filter by media types: ["image", "video", "audio", "document"].
            session_id (`str`, optional):
                Filter by specific session ID.
            top_k (`int`, optional):
                Maximum number of results to return. Defaults to 5.
                
        Returns:
            `ToolResponse`:
                Search results with memory details and relevance scores.
        """
        if memory_system is None:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Error: Multimodal memory system is not enabled.",
                    ),
                ],
            )
        
        try:
            # Convert media_types strings to MediaType enum if provided
            media_type_filters = None
            if media_types:
                from dominusprime.agents.memory.multimodal.models import MediaType
                media_type_filters = [MediaType(mt) for mt in media_types]
            
            # Search memories
            results = memory_system.search(
                query=query,
                media_types=media_type_filters,
                session_ids=[session_id] if session_id else None,
                top_k=top_k
            )
            
            if not results:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"No memories found matching: {query}",
                        ),
                    ],
                )
            
            result_text = f"Found {len(results)} relevant memories:\n\n"
            
            for i, result in enumerate(results, 1):
                result_text += f"{i}. [{result.media_type.value.upper()}] {result.id}\n"
                result_text += f"   Session: {result.session_id}\n"
                if hasattr(result, 'similarity_score'):
                    result_text += f"   Relevance: {result.similarity_score:.2f}\n"
                if result.metadata and 'description' in result.metadata:
                    desc = result.metadata['description'][:100]
                    result_text += f"   Context: {desc}...\n"
                result_text += "\n"
            
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=result_text,
                    ),
                ],
            )
            
        except Exception as e:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error searching memories: {str(e)}",
                    ),
                ],
            )
    
    async def get_memory(
        memory_id: str,
    ) -> ToolResponse:
        """
        Retrieve detailed information about a specific memory.
        
        Use this tool to get full details about a memory you found in search results.
        
        Args:
            memory_id (`str`):
                The unique ID of the memory to retrieve.
                
        Returns:
            `ToolResponse`:
                Complete memory details including metadata and file information.
        """
        if memory_system is None:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Error: Multimodal memory system is not enabled.",
                    ),
                ],
            )
        
        try:
            memory = memory_system.get_memory_by_id(memory_id)
            
            if memory is None:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"Memory not found: {memory_id}",
                        ),
                    ],
                )
            
            result_text = f"""Memory Details:

ID: {memory.id}
Type: {memory.media_type.value}
Session: {memory.session_id}
File: {memory.file_path.name}
Size: {memory.file_size / 1024:.2f} KB
Created: {memory.created_at}

Metadata:"""
            
            if memory.metadata:
                for key, value in memory.metadata.items():
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    result_text += f"\n  {key}: {value}"
            
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=result_text,
                    ),
                ],
            )
            
        except Exception as e:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error retrieving memory: {str(e)}",
                    ),
                ],
            )
    
    async def list_memories(
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> ToolResponse:
        """
        List recent memories from current or specified session.
        
        Use this tool to see what media has been stored in the current conversation.
        
        Args:
            session_id (`str`, optional):
                Session ID to list memories from. Defaults to current session.
            limit (`int`, optional):
                Maximum number of memories to list. Defaults to 10.
                
        Returns:
            `ToolResponse`:
                List of recent memories with basic information.
        """
        if memory_system is None:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Error: Multimodal memory system is not enabled.",
                    ),
                ],
            )
        
        try:
            # Use current session if not specified
            if session_id is None:
                session_id = getattr(memory_system, 'current_session_id', 'default')
            
            memories = memory_system.get_session_memories(session_id)
            
            if not memories:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"No memories found for session: {session_id}",
                        ),
                    ],
                )
            
            # Sort by creation time and limit
            memories = sorted(memories, key=lambda m: m.created_at, reverse=True)[:limit]
            
            result_text = f"Memories in session {session_id} ({len(memories)}):\n\n"
            
            for i, memory in enumerate(memories, 1):
                result_text += f"{i}. [{memory.media_type.value.upper()}] {memory.id}\n"
                result_text += f"   File: {memory.file_path.name}\n"
                if memory.metadata and 'description' in memory.metadata:
                    desc = memory.metadata['description'][:80]
                    result_text += f"   Context: {desc}...\n"
                result_text += "\n"
            
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=result_text,
                    ),
                ],
            )
            
        except Exception as e:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error listing memories: {str(e)}",
                    ),
                ],
            )
    
    async def delete_memory(
        memory_id: str,
    ) -> ToolResponse:
        """
        Delete a specific memory permanently.
        
        Use this tool to remove memories that are no longer needed.
        
        Args:
            memory_id (`str`):
                The unique ID of the memory to delete.
                
        Returns:
            `ToolResponse`:
                Confirmation of deletion.
        """
        if memory_system is None:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Error: Multimodal memory system is not enabled.",
                    ),
                ],
            )
        
        try:
            success = memory_system.delete_memory(memory_id)
            
            if success:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"Memory deleted successfully: {memory_id}",
                        ),
                    ],
                )
            else:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"Failed to delete memory: {memory_id}",
                        ),
                    ],
                )
            
        except Exception as e:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error deleting memory: {str(e)}",
                    ),
                ],
            )
    
    async def get_memory_stats() -> ToolResponse:
        """
        Get statistics about stored memories.
        
        Use this tool to check storage usage and memory counts.
        
        Returns:
            `ToolResponse`:
                Memory system statistics.
        """
        if memory_system is None:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Error: Multimodal memory system is not enabled.",
                    ),
                ],
            )
        
        try:
            stats = memory_system.get_statistics()
            
            result_text = """Memory System Statistics:

Total Memories: {total}
Storage Used: {used:.2f} GB / {total_gb:.2f} GB
Available: {available:.2f} GB

By Type:
  Images: {images}
  Videos: {videos}
  Audio: {audio}
  Documents: {documents}""".format(
                total=stats.get('total_memories', 0),
                used=stats.get('storage_used', 0) / (1024**3),
                total_gb=stats.get('storage_total', 0) / (1024**3),
                available=stats.get('storage_available', 0) / (1024**3),
                images=stats.get('type_counts', {}).get('image', 0),
                videos=stats.get('type_counts', {}).get('video', 0),
                audio=stats.get('type_counts', {}).get('audio', 0),
                documents=stats.get('type_counts', {}).get('document', 0),
            )
            
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=result_text,
                    ),
                ],
            )
            
        except Exception as e:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error getting statistics: {str(e)}",
                    ),
                ],
            )
    
    # Return all tools as a dictionary
    return {
        'store_media': store_media,
        'search_memories': search_memories,
        'get_memory': get_memory,
        'list_memories': list_memories,
        'delete_memory': delete_memory,
        'get_memory_stats': get_memory_stats,
    }
