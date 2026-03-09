# -*- coding: utf-8 -*-
"""DominusPrime Agent - Main agent implementation.

This module provides the main DominusPrimeAgent class built on ReActAgent,
with integrated tools, skills, and memory management.
"""
import asyncio
import logging
import os
from typing import Any, List, Literal, Optional, Type

from agentscope.agent import ReActAgent
from agentscope.mcp import HttpStatefulClient, StdIOStatefulClient
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.tool import Toolkit
from anyio import ClosedResourceError
from pydantic import BaseModel

from .command_handler import CommandHandler
from .hooks import BootstrapHook, MemoryCompactionHook
from .model_factory import create_model_and_formatter
from .multi_agent import (
    AgentOrchestrator,
    AgentPool,
    TaskComplexityAnalyzer,
    TaskDecomposer,
    TaskComplexity,
)
from .prompt import build_system_prompt_from_working_dir
from .skills_manager import (
    ensure_skills_initialized,
    get_working_skills_dir,
    list_available_skills,
)
from .tools import (
    browser_use,
    desktop_screenshot,
    edit_file,
    execute_shell_command,
    get_current_time,
    read_file,
    send_file_to_user,
    write_file,
    create_memory_search_tool,
)
from .utils import process_file_and_media_blocks_in_message
from ..agents.memory import MemoryManager
from ..config import load_config
from ..constant import (
    MEMORY_COMPACT_KEEP_RECENT,
    MEMORY_COMPACT_RATIO,
    WORKING_DIR,
)

logger = logging.getLogger(__name__)

# Valid namesake strategies for tool registration
NamesakeStrategy = Literal["override", "skip", "raise", "rename"]


def normalize_reasoning_tool_choice(
    tool_choice: Literal["auto", "none", "required"] | None,
    has_tools: bool,
) -> Literal["auto", "none", "required"] | None:
    """Normalize tool_choice for reasoning to reduce provider variance."""
    if tool_choice is None and has_tools:
        return "auto"
    return tool_choice


class DominusPrimeAgent(ReActAgent):
    """DominusPrime Agent with integrated tools, skills, and memory management.

    This agent extends ReActAgent with:
    - Built-in tools (shell, file operations, browser, etc.)
    - Dynamic skill loading from working directory
    - Memory management with auto-compaction
    - Bootstrap guidance for first-time setup
    - System command handling (/compact, /new, etc.)
    """

    def __init__(
        self,
        env_context: Optional[str] = None,
        enable_memory_manager: bool = True,
        mcp_clients: Optional[List[Any]] = None,
        memory_manager: MemoryManager | None = None,
        max_iters: int = 50,
        max_input_length: int = 128 * 1024,  # 128K = 131072 tokens
        namesake_strategy: NamesakeStrategy = "skip",
        multi_agent_config: Optional[Any] = None,
    ):
        """Initialize DominusPrimeAgent.

        Args:
            env_context: Optional environment context to prepend to
                system prompt
            enable_memory_manager: Whether to enable memory manager
            mcp_clients: Optional list of MCP clients for tool
                integration
            memory_manager: Optional memory manager instance
            max_iters: Maximum number of reasoning-acting iterations
                (default: 50)
            max_input_length: Maximum input length in tokens for model
                context window (default: 128K = 131072)
            namesake_strategy: Strategy to handle namesake tool functions.
                Options: "override", "skip", "raise", "rename"
                (default: "skip")
            multi_agent_config: Optional multi-agent configuration
        """
        self._env_context = env_context
        self._max_input_length = max_input_length
        self._mcp_clients = mcp_clients or []
        self._namesake_strategy = namesake_strategy
        self._multi_agent_config = multi_agent_config

        # Memory compaction threshold: configurable ratio of max_input_length
        self._memory_compact_threshold = int(
            max_input_length * MEMORY_COMPACT_RATIO,
        )

        # Initialize toolkit with built-in tools
        toolkit = self._create_toolkit(namesake_strategy=namesake_strategy)

        # Load and register skills
        self._register_skills(toolkit)

        # Build system prompt
        sys_prompt = self._build_sys_prompt()

        # Create model and formatter using factory method
        model, formatter = create_model_and_formatter()

        # Initialize parent ReActAgent
        super().__init__(
            name="Friday",
            model=model,
            sys_prompt=sys_prompt,
            toolkit=toolkit,
            memory=InMemoryMemory(),
            formatter=formatter,
            max_iters=max_iters,
        )

        # Setup memory manager
        self._setup_memory_manager(
            enable_memory_manager,
            memory_manager,
            namesake_strategy,
        )

        # Setup command handler
        self.command_handler = CommandHandler(
            agent_name=self.name,
            memory=self.memory,
            memory_manager=self.memory_manager,
            enable_memory_manager=self._enable_memory_manager,
        )

        # Setup multi-agent system
        self._setup_multi_agent_system()

        # Register hooks
        self._register_hooks()

    def _create_toolkit(
        self,
        namesake_strategy: NamesakeStrategy = "skip",
    ) -> Toolkit:
        """Create and populate toolkit with built-in tools.

        Args:
            namesake_strategy: Strategy to handle namesake tool functions.
                Options: "override", "skip", "raise", "rename"
                (default: "skip")

        Returns:
            Configured toolkit instance
        """
        toolkit = Toolkit()

        # Register built-in tools
        toolkit.register_tool_function(
            execute_shell_command,
            namesake_strategy=namesake_strategy,
        )
        toolkit.register_tool_function(
            read_file,
            namesake_strategy=namesake_strategy,
        )
        toolkit.register_tool_function(
            write_file,
            namesake_strategy=namesake_strategy,
        )
        toolkit.register_tool_function(
            edit_file,
            namesake_strategy=namesake_strategy,
        )
        toolkit.register_tool_function(
            browser_use,
            namesake_strategy=namesake_strategy,
        )
        toolkit.register_tool_function(
            desktop_screenshot,
            namesake_strategy=namesake_strategy,
        )
        toolkit.register_tool_function(
            send_file_to_user,
            namesake_strategy=namesake_strategy,
        )
        toolkit.register_tool_function(
            get_current_time,
            namesake_strategy=namesake_strategy,
        )

        return toolkit

    def _register_skills(self, toolkit: Toolkit) -> None:
        """Load and register skills from working directory.

        Args:
            toolkit: Toolkit to register skills to
        """
        # Check skills initialization
        ensure_skills_initialized()

        working_skills_dir = get_working_skills_dir()
        available_skills = list_available_skills()

        for skill_name in available_skills:
            skill_dir = working_skills_dir / skill_name
            if skill_dir.exists():
                try:
                    toolkit.register_agent_skill(str(skill_dir))
                    logger.debug("Registered skill: %s", skill_name)
                except Exception as e:
                    logger.error(
                        "Failed to register skill '%s': %s",
                        skill_name,
                        e,
                    )

    def _build_sys_prompt(self) -> str:
        """Build system prompt from working dir files and env context.

        Returns:
            Complete system prompt string
        """
        sys_prompt = build_system_prompt_from_working_dir()
        if self._env_context is not None:
            sys_prompt = self._env_context + "\n\n" + sys_prompt
        return sys_prompt

    def _setup_memory_manager(
        self,
        enable_memory_manager: bool,
        memory_manager: MemoryManager | None,
        namesake_strategy: NamesakeStrategy,
    ) -> None:
        """Setup memory manager and register memory search tool if enabled.

        Args:
            enable_memory_manager: Whether to enable memory manager
            memory_manager: Optional memory manager instance
            namesake_strategy: Strategy to handle namesake tool functions
        """
        # Check env var: if ENABLE_MEMORY_MANAGER=false, disable memory manager
        env_enable_mm = os.getenv("ENABLE_MEMORY_MANAGER", "")
        if env_enable_mm.lower() == "false":
            enable_memory_manager = False

        self._enable_memory_manager: bool = enable_memory_manager
        self.memory_manager = memory_manager

        # Register memory_search tool if enabled and available
        if self._enable_memory_manager and self.memory_manager is not None:
            # update memory manager
            self.memory_manager.chat_model = self.model
            self.memory_manager.formatter = self.formatter
            memory_toolkit = Toolkit()
            memory_toolkit.register_tool_function(
                read_file,
                namesake_strategy=self._namesake_strategy,
            )
            memory_toolkit.register_tool_function(
                write_file,
                namesake_strategy=self._namesake_strategy,
            )
            memory_toolkit.register_tool_function(
                edit_file,
                namesake_strategy=self._namesake_strategy,
            )
            self.memory_manager.toolkit = memory_toolkit
            self.memory_manager.update_config_params()

            self.memory = self.memory_manager.get_in_memory_memory()

            # Register memory_search as a tool function
            self.toolkit.register_tool_function(
                create_memory_search_tool(self.memory_manager),
                namesake_strategy=namesake_strategy,
            )
            logger.debug("Registered memory_search tool")

    def _setup_multi_agent_system(self) -> None:
        """Setup multi-agent system components if enabled."""
        self.complexity_analyzer: Optional[TaskComplexityAnalyzer] = None
        self.task_decomposer: Optional[TaskDecomposer] = None
        self.orchestrator: Optional[AgentOrchestrator] = None
        
        # Check if multi-agent is enabled via config
        if self._multi_agent_config is None:
            config = load_config()
            self._multi_agent_config = config.agents.running.multi_agent
        
        if not self._multi_agent_config.enabled:
            logger.debug("Multi-agent system disabled")
            return
        
        logger.info("Initializing multi-agent system")
        
        # Initialize complexity analyzer
        self.complexity_analyzer = TaskComplexityAnalyzer()
        
        # Initialize task decomposer with model
        self.task_decomposer = TaskDecomposer(
            model=self.model,
            complexity_analyzer=self.complexity_analyzer,
        )
        
        # Initialize agent pool
        agent_pool = AgentPool(
            max_concurrent=self._multi_agent_config.max_concurrent_agents,
        )
        
        # Initialize orchestrator
        self.orchestrator = AgentOrchestrator(
            agent_pool=agent_pool,
            enable_parallel=self._multi_agent_config.enable_parallel_execution,
        )
        
        logger.info(
            "Multi-agent system initialized (threshold: %s, max_concurrent: %d)",
            self._multi_agent_config.complexity_threshold,
            self._multi_agent_config.max_concurrent_agents,
        )

    def _register_hooks(self) -> None:
        """Register pre-reasoning hooks for bootstrap and memory compaction."""
        # Bootstrap hook - checks BOOTSTRAP.md on first interaction
        config = load_config()
        bootstrap_hook = BootstrapHook(
            working_dir=WORKING_DIR,
            language=config.agents.language,
        )
        self.register_instance_hook(
            hook_type="pre_reasoning",
            hook_name="bootstrap_hook",
            hook=bootstrap_hook.__call__,
        )
        logger.debug("Registered bootstrap hook")

        # Memory compaction hook - auto-compact when context is full
        if self._enable_memory_manager and self.memory_manager is not None:
            memory_compact_hook = MemoryCompactionHook(
                memory_manager=self.memory_manager,
                memory_compact_threshold=self._memory_compact_threshold,
                keep_recent=MEMORY_COMPACT_KEEP_RECENT,
            )
            self.register_instance_hook(
                hook_type="pre_reasoning",
                hook_name="memory_compact_hook",
                hook=memory_compact_hook.__call__,
            )
            logger.debug("Registered memory compaction hook")

    def rebuild_sys_prompt(self) -> None:
        """Rebuild and replace the system prompt.

        Useful after load_session_state to ensure the prompt reflects
        the latest AGENTS.md / SOUL.md / PROFILE.md on disk.

        Updates both self._sys_prompt and the first system-role
        message stored in self.memory.content (if one exists).
        """
        self._sys_prompt = self._build_sys_prompt()

        for msg, _marks in self.memory.content:
            if msg.role == "system":
                msg.content = self.sys_prompt
            break

    async def register_mcp_clients(
        self,
        namesake_strategy: NamesakeStrategy = "skip",
    ) -> None:
        """Register MCP clients on this agent's toolkit after construction.

        Args:
            namesake_strategy: Strategy to handle namesake tool functions.
                Options: "override", "skip", "raise", "rename"
                (default: "skip")
        """
        for i, client in enumerate(self._mcp_clients):
            client_name = getattr(client, "name", repr(client))
            try:
                await self.toolkit.register_mcp_client(
                    client,
                    namesake_strategy=namesake_strategy,
                )
            except (ClosedResourceError, asyncio.CancelledError) as error:
                if self._should_propagate_cancelled_error(error):
                    raise
                logger.warning(
                    "MCP client '%s' session interrupted while listing tools; "
                    "trying recovery",
                    client_name,
                )
                recovered_client = await self._recover_mcp_client(client)
                if recovered_client is not None:
                    self._mcp_clients[i] = recovered_client
                    try:
                        await self.toolkit.register_mcp_client(
                            recovered_client,
                            namesake_strategy=namesake_strategy,
                        )
                        continue
                    except asyncio.CancelledError as recover_error:
                        if self._should_propagate_cancelled_error(
                            recover_error,
                        ):
                            raise
                        logger.warning(
                            "MCP client '%s' registration cancelled after "
                            "recovery, skipping",
                            client_name,
                        )
                    except Exception as e:  # pylint: disable=broad-except
                        logger.warning(
                            "MCP client '%s' still unavailable after "
                            "recovery, skipping: %s",
                            client_name,
                            e,
                        )
                else:
                    logger.warning(
                        "MCP client '%s' recovery failed, skipping",
                        client_name,
                    )
            except Exception as e:  # pylint: disable=broad-except
                logger.exception(
                    "Unexpected error registering MCP client '%s': %s",
                    client_name,
                    e,
                )
                raise

    async def _recover_mcp_client(self, client: Any) -> Any | None:
        """Recover MCP client from broken session and return healthy client."""
        if await self._reconnect_mcp_client(client):
            return client

        rebuilt_client = self._rebuild_mcp_client(client)
        if rebuilt_client is None:
            return None

        if await self._reconnect_mcp_client(rebuilt_client):
            return self._reuse_shared_client_reference(
                original_client=client,
                rebuilt_client=rebuilt_client,
            )

        return None

    @staticmethod
    def _reuse_shared_client_reference(
        original_client: Any,
        rebuilt_client: Any,
    ) -> Any:
        """Keep manager-shared client reference stable after rebuild."""
        original_dict = getattr(original_client, "__dict__", None)
        rebuilt_dict = getattr(rebuilt_client, "__dict__", None)
        if isinstance(original_dict, dict) and isinstance(rebuilt_dict, dict):
            original_dict.update(rebuilt_dict)
            return original_client
        return rebuilt_client

    @staticmethod
    def _should_propagate_cancelled_error(error: BaseException) -> bool:
        """Only swallow MCP-internal cancellations, not task cancellation."""
        if not isinstance(error, asyncio.CancelledError):
            return False

        task = asyncio.current_task()
        if task is None:
            return False

        cancelling = getattr(task, "cancelling", None)
        if callable(cancelling):
            return cancelling() > 0

        # Python < 3.11: Task.cancelling() is unavailable.
        # Fall back to propagating CancelledError to avoid swallowing
        # genuine task cancellations when we cannot inspect the state.
        return True

    @staticmethod
    async def _reconnect_mcp_client(
        client: Any,
        timeout: float = 60.0,
    ) -> bool:
        """Best-effort reconnect for stateful MCP clients."""
        close_fn = getattr(client, "close", None)
        if callable(close_fn):
            try:
                await close_fn()
            except asyncio.CancelledError:  # pylint: disable=try-except-raise
                raise
            except Exception:  # pylint: disable=broad-except
                pass

        connect_fn = getattr(client, "connect", None)
        if not callable(connect_fn):
            return False

        try:
            await asyncio.wait_for(connect_fn(), timeout=timeout)
            return True
        except asyncio.CancelledError:  # pylint: disable=try-except-raise
            raise
        except asyncio.TimeoutError:
            return False
        except Exception:  # pylint: disable=broad-except
            return False

    @staticmethod
    def _rebuild_mcp_client(client: Any) -> Any | None:
        """Rebuild a fresh MCP client instance from stored config metadata."""
        rebuild_info = getattr(client, "_dominusprime_rebuild_info", None)
        if not isinstance(rebuild_info, dict):
            return None

        transport = rebuild_info.get("transport")
        name = rebuild_info.get("name")

        try:
            if transport == "stdio":
                rebuilt_client = StdIOStatefulClient(
                    name=name,
                    command=rebuild_info.get("command"),
                    args=rebuild_info.get("args", []),
                    env=rebuild_info.get("env", {}),
                    cwd=rebuild_info.get("cwd"),
                )
                setattr(rebuilt_client, "_dominusprime_rebuild_info", rebuild_info)
                return rebuilt_client

            rebuilt_client = HttpStatefulClient(
                name=name,
                transport=transport,
                url=rebuild_info.get("url"),
                headers=rebuild_info.get("headers"),
            )
            setattr(rebuilt_client, "_dominusprime_rebuild_info", rebuild_info)
            return rebuilt_client
        except Exception:  # pylint: disable=broad-except
            return None

    async def _reasoning(
        self,
        tool_choice: Literal["auto", "none", "required"] | None = None,
    ) -> Msg:
        """Ensure a stable default tool-choice behavior across providers."""
        tool_choice = normalize_reasoning_tool_choice(
            tool_choice=tool_choice,
            has_tools=bool(self.toolkit.get_json_schemas()),
        )

        return await super()._reasoning(tool_choice=tool_choice)

    async def reply(
        self,
        msg: Msg | list[Msg] | None = None,
        structured_model: Type[BaseModel] | None = None,
    ) -> Msg:
        """Override reply to process file blocks and handle commands.

        Args:
            msg: Input message(s) from user
            structured_model: Optional pydantic model for structured output

        Returns:
            Response message
        """
        # Process file and media blocks in messages
        if msg is not None:
            await process_file_and_media_blocks_in_message(msg)

        # Check if message is a system command
        last_msg = msg[-1] if isinstance(msg, list) else msg
        query = (
            last_msg.get_text_content() if isinstance(last_msg, Msg) else None
        )

        if self.command_handler.is_command(query):
            logger.info(f"Received command: {query}")
            msg = await self.command_handler.handle_command(query)
            await self.print(msg)
            return msg

        # Check if multi-agent delegation should be used
        if await self._should_delegate_to_multi_agent(query):
            logger.info("Delegating complex task to multi-agent system")
            return await self._delegate_to_multi_agent(query, msg)

        # Normal message processing
        return await super().reply(msg=msg, structured_model=structured_model)

    async def _should_delegate_to_multi_agent(
        self,
        query: Optional[str],
    ) -> bool:
        """Check if task should be delegated to multi-agent system.
        
        Args:
            query: User query text
            
        Returns:
            True if delegation is recommended
        """
        if not query or not self.complexity_analyzer or not self.task_decomposer:
            return False
        
        # Analyze task complexity
        context = [msg for msg, _ in self.memory.content[-5:]]  # Last 5 messages
        complexity = self.complexity_analyzer.analyze(query, context)
        
        # Get threshold from config
        threshold_str = self._multi_agent_config.complexity_threshold.upper()
        threshold = TaskComplexity[threshold_str]
        
        # Check if complexity exceeds threshold
        should_delegate = self.complexity_analyzer.should_delegate(
            complexity,
            threshold,
        )
        
        if should_delegate:
            explanation = self.complexity_analyzer.explain_complexity(
                query,
                complexity,
                context,
            )
            logger.info(
                "Task complexity: %s (threshold: %s)\nReason: %s",
                complexity.value,
                threshold.value,
                explanation,
            )
        
        return should_delegate

    async def _delegate_to_multi_agent(
        self,
        query: str,
        original_msg: Msg | list[Msg] | None,
    ) -> Msg:
        """Delegate task to multi-agent system.
        
        Args:
            query: User query text
            original_msg: Original message(s)
            
        Returns:
            Response message with aggregated results
        """
        try:
            # Get conversation context
            context = [msg for msg, _ in self.memory.content[-10:]]
            
            # Decompose task into subtasks
            subtasks = await self.task_decomposer.decompose(
                query,
                context=context,
                max_subtasks=self._multi_agent_config.max_subtasks,
            )
            
            logger.info("Decomposed task into %d subtasks", len(subtasks))
            
            # Inform user about delegation
            delegation_msg = Msg(
                name=self.name,
                role="assistant",
                content=(
                    f"🤖 I've analyzed your request and will coordinate "
                    f"{len(subtasks)} specialized sub-agents to handle this efficiently.\n\n"
                    f"**Task Breakdown:**\n"
                    + "\n".join([
                        f"{i+1}. {task.description}"
                        for i, task in enumerate(subtasks)
                    ])
                    + "\n\n*Processing...*"
                ),
            )
            await self.print(delegation_msg)
            
            # Execute subtasks via orchestrator
            aggregated_result = await self.orchestrator.execute_subtasks(subtasks)
            
            # Format results for user
            result_content = "✅ **Multi-Agent Execution Complete**\n\n"
            
            if aggregated_result.success:
                result_content += f"**Status:** Success ({aggregated_result.successful_count}/{aggregated_result.total_count} tasks completed)\n"
                result_content += f"**Total Time:** {aggregated_result.total_time:.2f}s\n\n"
                
                result_content += "**Results:**\n"
                for i, result in enumerate(aggregated_result.results):
                    if result.output:
                        result_content += f"\n{i+1}. {subtasks[i].description}\n"
                        result_content += f"   → {result.output}\n"
                
                if aggregated_result.summary:
                    result_content += f"\n**Summary:**\n{aggregated_result.summary}\n"
            else:
                result_content += f"**Status:** Partial Success ({aggregated_result.successful_count}/{aggregated_result.total_count} tasks completed)\n"
                result_content += f"**Total Time:** {aggregated_result.total_time:.2f}s\n\n"
                
                if aggregated_result.errors:
                    result_content += "**Errors:**\n"
                    for error in aggregated_result.errors[:5]:  # Limit to 5 errors
                        result_content += f"- {error}\n"
            
            response_msg = Msg(
                name=self.name,
                role="assistant",
                content=result_content,
            )
            
            return response_msg
            
        except Exception as e:
            logger.exception("Multi-agent delegation failed: %s", e)
            
            # Fall back to normal processing
            error_msg = Msg(
                name=self.name,
                role="assistant",
                content=(
                    f"⚠️ Multi-agent coordination encountered an error: {e}\n\n"
                    f"Falling back to standard processing..."
                ),
            )
            await self.print(error_msg)
            
            return await super().reply(msg=original_msg)

    async def interrupt(self, msg: Msg | list[Msg] | None = None) -> None:
        """Interrupt the current reply process and wait for cleanup."""
        if self._reply_task and not self._reply_task.done():
            task = self._reply_task
            task.cancel(msg)
            try:
                await task
            except asyncio.CancelledError:
                if not task.cancelled():
                    raise
            except Exception:
                logger.warning(
                    "Exception occurred during interrupt cleanup",
                    exc_info=True,
                )
