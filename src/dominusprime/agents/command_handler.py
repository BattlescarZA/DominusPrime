# -*- coding: utf-8 -*-
"""Agent command handler for system commands.

This module handles system commands like /compact, /new, /clear, etc.
Also supports slash commands for quick skill loading (e.g., /python-debugging).
"""
import json
import logging
from typing import TYPE_CHECKING

from agentscope.agent._react_agent import _MemoryMark
from agentscope.message import Msg, TextBlock

if TYPE_CHECKING:
    from .memory import MemoryManager
    from reme.memory.file_based_copaw import CoPawInMemoryMemory

logger = logging.getLogger(__name__)


class ConversationCommandHandlerMixin:
    """Mixin for conversation (system) commands: /compact, /new, /clear, etc.

    Expects self to have: agent_name, memory, formatter, memory_manager,
    _enable_memory_manager.
    """

    # Supported conversation commands (unchanged set)
    SYSTEM_COMMANDS = frozenset(
        {
            "compact",
            "new",
            "clear",
            "history",
            "compact_str",
            "await_summary",
            "message",
            "memory",
        },
    )

    def is_conversation_command(self, query: str | None) -> bool:
        """Check if the query is a conversation system command.

        Args:
            query: User query string

        Returns:
            True if query is a system command
        """
        if not isinstance(query, str) or not query.startswith("/"):
            return False
        return query.strip().lstrip("/").split()[0] in self.SYSTEM_COMMANDS
    
    def is_skill_command(self, query: str | None) -> bool:
        """Check if the query is a skill slash command.
        
        Args:
            query: User query string
            
        Returns:
            True if query is a skill command (e.g., /python-debugging)
        """
        if not isinstance(query, str) or not query.startswith("/"):
            return False
        
        command = query.strip().lstrip("/").split()[0]
        
        # Not a system command, so might be a skill
        if command in self.SYSTEM_COMMANDS:
            return False
        
        # Check if skill exists
        try:
            from .tools.skills_tool import skills
            import asyncio
            
            result_str = asyncio.run(skills(action="view", name=command))
            result = json.loads(result_str)
            return result.get("success", False)
        except Exception:
            return False


class CommandHandler(ConversationCommandHandlerMixin):
    """Handler for system commands (uses ConversationCommandHandlerMixin)."""

    def __init__(
        self,
        agent_name: str,
        memory: "DominusPrimeInMemoryMemory",
        memory_manager: "MemoryManager | None" = None,
        enable_memory_manager: bool = True,
    ):
        """Initialize command handler.

        Args:
            agent_name: Name of the agent for message creation
            memory: Agent's CoPawInMemoryMemory instance
            memory_manager: Optional memory manager instance
            enable_memory_manager: Whether memory manager is enabled
        """
        self.agent_name = agent_name
        self.memory = memory
        self.memory_manager = memory_manager
        self._enable_memory_manager = enable_memory_manager

    def is_command(self, query: str | None) -> bool:
        """Check if the query is any command (system or skill)."""
        return self.is_conversation_command(query) or self.is_skill_command(query)

    async def _make_system_msg(self, text: str) -> Msg:
        """Create a system response message.

        Args:
            text: Message text content

        Returns:
            System message
        """
        return Msg(
            name=self.agent_name,
            role="assistant",
            content=[TextBlock(type="text", text=text)],
        )

    def _has_memory_manager(self) -> bool:
        """Check if memory manager is available."""
        return self._enable_memory_manager and self.memory_manager is not None

    async def _process_compact(
        self,
        messages: list[Msg],
        _args: str = "",
    ) -> Msg:
        """Process /compact command."""
        if not messages:
            return await self._make_system_msg(
                "**No messages to compact.**\n\n"
                "- Current memory is empty\n"
                "- No action taken",
            )
        if not self._has_memory_manager():
            return await self._make_system_msg(
                "**Memory Manager Disabled**\n\n"
                "- Memory compaction is not available\n"
                "- Enable memory manager to use this feature",
            )

        self.memory_manager.add_async_summary_task(messages=messages)
        compact_content = await self.memory_manager.compact_memory(
            messages=messages,
            previous_summary=self.memory.get_compressed_summary(),
        )
        await self.memory.update_compressed_summary(compact_content)
        updated_count = await self.memory.mark_messages_compressed(messages)
        logger.info(
            f"Marked {updated_count} messages as compacted "
            f"with:\n{compact_content}",
        )
        return await self._make_system_msg(
            f"**Compact Complete!**\n\n"
            f"- Messages compacted: {updated_count}\n"
            f"**Compressed Summary:**\n{compact_content}\n"
            f"- Summary task started in background\n",
        )

    async def _process_new(self, messages: list[Msg], _args: str = "") -> Msg:
        """Process /new command."""
        if not messages:
            self.memory.clear_compressed_summary()
            return await self._make_system_msg(
                "**No messages to summarize.**\n\n"
                "- Current memory is empty\n"
                "- Compressed summary is clear\n"
                "- No action taken",
            )
        if not self._has_memory_manager():
            return await self._make_system_msg(
                "**Memory Manager Disabled**\n\n"
                "- Cannot start new conversation with summary\n"
                "- Enable memory manager to use this feature",
            )

        self.memory_manager.add_async_summary_task(messages=messages)
        self.memory.clear_compressed_summary()
        updated_count = await self.memory.mark_messages_compressed(messages)
        logger.info(f"Marked {updated_count} messages as compacted")
        return await self._make_system_msg(
            "**New Conversation Started!**\n\n"
            "- Summary task started in background\n"
            "- Ready for new conversation",
        )

    async def _process_clear(
        self,
        _messages: list[Msg],
        _args: str = "",
    ) -> Msg:
        """Process /clear command."""
        self.memory.clear_content()
        self.memory.clear_compressed_summary()
        return await self._make_system_msg(
            "**History Cleared!**\n\n"
            "- Compressed summary reset\n"
            "- Memory is now empty",
        )

    async def _process_compact_str(
        self,
        _messages: list[Msg],
        _args: str = "",
    ) -> Msg:
        """Process /compact_str command to show compressed summary."""
        summary = self.memory.get_compressed_summary()
        if not summary:
            return await self._make_system_msg(
                "**No Compressed Summary**\n\n"
                "- No summary has been generated yet\n"
                "- Use /compact or wait for auto-compaction",
            )
        return await self._make_system_msg(
            f"**Compressed Summary**\n\n{summary}",
        )

    async def _process_history(
        self,
        _messages: list[Msg],
        _args: str = "",
    ) -> Msg:
        """Process /history command."""
        history_str = await self.memory.get_history_str()
        return await self._make_system_msg(history_str)

    async def _process_await_summary(
        self,
        _messages: list[Msg],
        _args: str = "",
    ) -> Msg:
        """Process /await_summary command to wait for all summary tasks."""
        if not self._has_memory_manager():
            return await self._make_system_msg(
                "**Memory Manager Disabled**\n\n"
                "- Cannot await summary tasks\n"
                "- Enable memory manager to use this feature",
            )

        task_count = len(self.memory_manager.summary_tasks)
        if task_count == 0:
            return await self._make_system_msg(
                "**No Summary Tasks**\n\n"
                "- No pending summary tasks to wait for",
            )

        result = await self.memory_manager.await_summary_tasks()
        return await self._make_system_msg(
            f"**Summary Tasks Complete**\n\n"
            f"- Waited for {task_count} summary task(s)\n"
            f"- {result}"
            f"- All tasks have finished",
        )

    async def _process_message(
        self,
        messages: list[Msg],
        args: str = "",
    ) -> Msg:
        """Process /message x command to show the nth message.

        Args:
            messages: List of messages in memory
            args: Command arguments (message index)

        Returns:
            System message with the requested message content
        """
        if not args:
            return await self._make_system_msg(
                "**Usage: /message <index>**\n\n"
                "- Example: /message 1 (show first message)\n"
                f"- Available messages: 1 to {len(messages)}",
            )

        try:
            index = int(args.strip())
        except ValueError:
            return await self._make_system_msg(
                f"**Invalid Index: '{args}'**\n\n"
                "- Index must be a number\n"
                "- Example: /message 1",
            )

        if not messages:
            return await self._make_system_msg(
                "**No Messages Available**\n\n- Current memory is empty",
            )

        if index < 1 or index > len(messages):
            return await self._make_system_msg(
                f"**Index Out of Range: {index}**\n\n"
                f"- Available range: 1 to {len(messages)}\n"
                f"- Example: /message 1",
            )

        msg = messages[index - 1]
        return await self._make_system_msg(
            f"**Message {index}/{len(messages)}**\n\n"
            f"- **Timestamp:** {msg.timestamp}\n"
            f"- **Name:** {msg.name}\n"
            f"- **Role:** {msg.role}\n"
            f"- **Content:**\n{msg.content}",
        )
    
    async def _process_skill(self, skill_name: str) -> Msg:
        """Process skill slash command (e.g., /python-debugging).
        
        Args:
            skill_name: Name of the skill to load
            
        Returns:
            System message with skill content
        """
        try:
            from .tools.skills_tool import skills
            
            # View the skill
            result_str = await skills(action="view", name=skill_name)
            result = json.loads(result_str)
            
            if not result.get("success"):
                return await self._make_system_msg(
                    f"**Skill Not Found: {skill_name}**\n\n"
                    f"- The skill '{skill_name}' does not exist\n"
                    f"- Use `await skills(action=\"list\")` to see available skills\n"
                    f"- Or search: `await skills(action=\"search\", query=\"{skill_name}\")`"
                )
            
            # Extract skill information
            skill_content = result.get("body", "")
            frontmatter = result.get("frontmatter", {})
            description = frontmatter.get("description", "No description")
            category = result.get("category", "uncategorized")
            
            # Build response
            response_parts = [
                f"**✓ Skill Loaded: {skill_name}**",
                f"",
                f"**Category**: {category}",
                f"**Description**: {description}",
                f"",
                f"---",
                f"",
                skill_content,
            ]
            
            # Include supporting files info if available
            if result.get("supporting_files"):
                files = result["supporting_files"]
                response_parts.extend([
                    f"",
                    f"---",
                    f"",
                    f"**Supporting Files** ({len(files)}):",
                ])
                for file in files:
                    response_parts.append(f"- `{file['path']}` ({file['size']} bytes)")
            
            return await self._make_system_msg("\n".join(response_parts))
            
        except Exception as e:
            logger.error(f"Error loading skill '{skill_name}': {e}", exc_info=True)
            return await self._make_system_msg(
                f"**Error Loading Skill**\n\n"
                f"- Failed to load skill '{skill_name}'\n"
                f"- Error: {e}\n"
                f"- Check logs for details"
            )
    
    async def _process_memory(self, messages: list[Msg], args: str = "") -> Msg:
        """Process /memory command.
        
        Args:
            messages: Current conversation messages (unused for memory)
            args: Arguments like "search query", "list", "stats", "clear"
            
        Returns:
            System message with memory information
        """
        # Check if multimodal memory system exists
        multimodal_memory = getattr(self, 'multimodal_memory', None)
        if multimodal_memory is None:
            return await self._make_system_msg(
                "**Multimodal Memory Not Enabled**\n\n"
                "The multimodal memory system is not available in this session."
            )
        
        # Parse subcommand
        parts = args.strip().split(" ", maxsplit=1)
        subcommand = parts[0].lower() if parts else "help"
        subargs = parts[1] if len(parts) > 1 else ""
        
        try:
            if subcommand == "search":
                # Search memories
                if not subargs:
                    return await self._make_system_msg(
                        "**Usage**: `/memory search <query>`\n\n"
                        "Example: `/memory search python debugging`"
                    )
                
                results = multimodal_memory.search(query=subargs, top_k=5)
                
                if not results:
                    return await self._make_system_msg(
                        f"**No memories found** matching: `{subargs}`"
                    )
                
                response_parts = [f"**Found {len(results)} memories** matching: `{subargs}`\n"]
                for i, result in enumerate(results, 1):
                    response_parts.append(f"\n**{i}. [{result.media_type.value.upper()}] {result.id}**")
                    response_parts.append(f"- Session: `{result.session_id}`")
                    if hasattr(result, 'similarity_score'):
                        response_parts.append(f"- Relevance: {result.similarity_score:.2f}")
                    if result.metadata and 'description' in result.metadata:
                        desc = result.metadata['description'][:100]
                        response_parts.append(f"- Context: {desc}...")
                
                return await self._make_system_msg("\n".join(response_parts))
            
            elif subcommand == "list":
                # List memories from current session
                session_id = subargs or getattr(multimodal_memory, 'current_session_id', 'default')
                memories = multimodal_memory.get_session_memories(session_id)
                
                if not memories:
                    return await self._make_system_msg(
                        f"**No memories** in session: `{session_id}`"
                    )
                
                # Sort by creation time
                memories = sorted(memories, key=lambda m: m.created_at, reverse=True)[:10]
                
                response_parts = [f"**Memories in session `{session_id}`** ({len(memories)}):\n"]
                for i, memory in enumerate(memories, 1):
                    response_parts.append(f"\n**{i}. [{memory.media_type.value.upper()}] {memory.id}**")
                    response_parts.append(f"- File: `{memory.file_path.name}`")
                    if memory.metadata and 'description' in memory.metadata:
                        desc = memory.metadata['description'][:80]
                        response_parts.append(f"- Context: {desc}...")
                
                return await self._make_system_msg("\n".join(response_parts))
            
            elif subcommand == "stats":
                # Show memory statistics
                stats = multimodal_memory.get_statistics()
                
                response_text = f"""**Memory System Statistics**

**Total Memories**: {stats.get('total_memories', 0)}
**Storage Used**: {stats.get('storage_used', 0) / (1024**3):.2f} GB / {stats.get('storage_total', 0) / (1024**3):.2f} GB
**Available**: {stats.get('storage_available', 0) / (1024**3):.2f} GB

**By Type**:
- Images: {stats.get('type_counts', {}).get('image', 0)}
- Videos: {stats.get('type_counts', {}).get('video', 0)}
- Audio: {stats.get('type_counts', {}).get('audio', 0)}
- Documents: {stats.get('type_counts', {}).get('document', 0)}"""
                
                return await self._make_system_msg(response_text)
            
            elif subcommand == "clear":
                # Clear memories from current session
                session_id = subargs or getattr(multimodal_memory, 'current_session_id', 'default')
                multimodal_memory.clear_session(session_id)
                
                return await self._make_system_msg(
                    f"**Cleared all memories** from session: `{session_id}`"
                )
            
            elif subcommand == "help" or subcommand == "":
                # Show help
                return await self._make_system_msg(
                    "**Multimodal Memory Commands**\n\n"
                    "**Search**: `/memory search <query>` - Search stored memories\n"
                    "**List**: `/memory list [session]` - List memories (default: current session)\n"
                    "**Stats**: `/memory stats` - Show memory statistics\n"
                    "**Clear**: `/memory clear [session]` - Clear memories from session\n\n"
                    "You can also use tools:\n"
                    "- `await store_media(media_path, context_text)`\n"
                    "- `await search_memories(query, top_k=5)`\n"
                    "- `await list_memories(session_id)`\n"
                    "- `await get_memory_stats()`"
                )
            
            else:
                return await self._make_system_msg(
                    f"**Unknown memory command**: `{subcommand}`\n\n"
                    "Use `/memory help` to see available commands."
                )
        
        except Exception as e:
            logger.error(f"Error processing memory command: {e}", exc_info=True)
            return await self._make_system_msg(
                f"**Error**: {e}\n\n"
                "Check logs for details."
            )
    
    async def handle_skill_command(self, query: str) -> Msg:
        """Process skill slash command.
        
        Args:
            query: Skill command string (e.g., "/python-debugging")
            
        Returns:
            System response message with skill content
        """
        skill_name = query.strip().lstrip("/").split()[0]
        logger.info(f"Processing skill command: {skill_name}")
        return await self._process_skill(skill_name)

    async def handle_conversation_command(self, query: str) -> Msg:
        """Process conversation system commands.

        Args:
            query: Command string (e.g., "/compact", "/new", "/message 5")

        Returns:
            System response message

        Raises:
            RuntimeError: If command is not recognized
        """
        messages = await self.memory.get_memory(
            exclude_mark=_MemoryMark.COMPRESSED,
            prepend_summary=False,
        )
        # Parse command and arguments
        parts = query.strip().lstrip("/").split(" ", maxsplit=1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        logger.info(f"Processing command: {command}, args: {args}")

        handler = getattr(self, f"_process_{command}", None)
        if handler is None:
            raise RuntimeError(f"Unknown command: {query}")
        return await handler(messages, args)

    async def handle_command(self, query: str) -> Msg:
        """Process commands (system or skill).
        
        Args:
            query: Command string
            
        Returns:
            System response message
        """
        # Check if it's a system command first
        if self.is_conversation_command(query):
            return await self.handle_conversation_command(query)
        # Otherwise try as skill command
        elif self.is_skill_command(query):
            return await self.handle_skill_command(query)
        else:
            # Unknown command
            command = query.strip().lstrip("/").split()[0]
            return await self._make_system_msg(
                f"**Unknown Command: /{command}**\n\n"
                f"**System Commands**: /compact, /new, /clear, /history, /message\n"
                f"**Skill Commands**: /skill-name (e.g., /python-debugging)\n\n"
                f"Use `await skills(action=\"list\")` to see available skills."
            )
