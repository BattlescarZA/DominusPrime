# -*- coding: utf-8 -*-
"""Error recovery and resilience for multi-agent system."""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class RetryConfig:
    """Configuration for retry logic."""

    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout: float = 60.0  # Seconds before attempting recovery
    monitoring_window: float = 300.0  # Seconds to track failures


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""

    check_interval: float = 30.0  # Seconds between checks
    timeout: float = 5.0  # Health check timeout
    unhealthy_threshold: int = 3  # Failed checks before unhealthy


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests fail immediately
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """Initialize circuit breaker.
        
        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None
        
        # Track failures in monitoring window
        self.recent_failures: List[float] = []

    def _cleanup_old_failures(self):
        """Remove failures outside monitoring window."""
        cutoff = time.time() - self.config.monitoring_window
        self.recent_failures = [
            t for t in self.recent_failures if t > cutoff
        ]

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function through circuit breaker.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        # Check if circuit should transition to half-open
        if self.state == CircuitState.OPEN:
            if self.opened_at and (time.time() - self.opened_at) >= self.config.timeout:
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.debug(
                f"Circuit breaker success in HALF_OPEN: "
                f"{self.success_count}/{self.config.success_threshold}"
            )
            
            if self.success_count >= self.config.success_threshold:
                logger.info("Circuit breaker closing (recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.recent_failures.clear()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = max(0, self.failure_count - 1)

    async def _on_failure(self):
        """Handle failed execution."""
        self.last_failure_time = time.time()
        self.recent_failures.append(self.last_failure_time)
        self._cleanup_old_failures()
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker opening (recovery failed)")
            self.state = CircuitState.OPEN
            self.opened_at = time.time()
            self.failure_count = len(self.recent_failures)
        elif self.state == CircuitState.CLOSED:
            self.failure_count = len(self.recent_failures)
            
            if self.failure_count >= self.config.failure_threshold:
                logger.warning(
                    f"Circuit breaker opening "
                    f"({self.failure_count} failures in window)"
                )
                self.state = CircuitState.OPEN
                self.opened_at = time.time()

    def reset(self):
        """Reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None
        self.recent_failures.clear()


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass


class RetryManager:
    """Manages retry logic with exponential backoff."""

    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize retry manager.
        
        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retryable_exceptions: tuple = (Exception,),
        **kwargs,
    ):
        """Execute function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            retryable_exceptions: Tuple of exceptions to retry on
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt == self.config.max_retries:
                    logger.error(
                        f"All {self.config.max_retries} retries exhausted"
                    )
                    raise
                
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
        
        # Should never reach here, but just in case
        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: delay = initial_delay * (base ** attempt)
        delay = self.config.initial_delay * (
            self.config.exponential_base ** attempt
        )
        
        # Cap at max_delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            import random
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)


@dataclass
class HealthStatus:
    """Health status of a component."""

    healthy: bool = True
    last_check: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    last_error: Optional[str] = None


class HealthMonitor:
    """Monitors health of system components."""

    def __init__(self, config: Optional[HealthCheckConfig] = None):
        """Initialize health monitor.
        
        Args:
            config: Health check configuration
        """
        self.config = config or HealthCheckConfig()
        self.component_status: Dict[str, HealthStatus] = {}
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

    async def register_component(
        self,
        name: str,
        health_check: Callable,
    ):
        """Register a component for health monitoring.
        
        Args:
            name: Component name
            health_check: Async function that returns True if healthy
        """
        if name not in self.component_status:
            self.component_status[name] = HealthStatus()
        
        # Store health check function
        if not hasattr(self, '_health_checks'):
            self._health_checks = {}
        self._health_checks[name] = health_check

    async def start_monitoring(self):
        """Start health monitoring loop."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitoring started")

    async def stop_monitoring(self):
        """Stop health monitoring loop."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                await self._check_all_components()
                await asyncio.sleep(self.config.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")

    async def _check_all_components(self):
        """Check health of all registered components."""
        if not hasattr(self, '_health_checks'):
            return
        
        for name, health_check in self._health_checks.items():
            await self._check_component(name, health_check)

    async def _check_component(self, name: str, health_check: Callable):
        """Check health of a single component.
        
        Args:
            name: Component name
            health_check: Health check function
        """
        status = self.component_status[name]
        
        try:
            # Execute health check with timeout
            is_healthy = await asyncio.wait_for(
                health_check(),
                timeout=self.config.timeout,
            )
            
            if is_healthy:
                # Component is healthy
                if not status.healthy:
                    logger.info(f"Component '{name}' recovered")
                status.healthy = True
                status.consecutive_failures = 0
                status.last_error = None
            else:
                # Health check returned False
                await self._handle_unhealthy(name, status, "Health check returned False")
                
        except asyncio.TimeoutError:
            await self._handle_unhealthy(name, status, "Health check timed out")
        except Exception as e:
            await self._handle_unhealthy(name, status, str(e))
        
        status.last_check = time.time()

    async def _handle_unhealthy(
        self,
        name: str,
        status: HealthStatus,
        error: str,
    ):
        """Handle unhealthy component.
        
        Args:
            name: Component name
            status: Current health status
            error: Error message
        """
        status.consecutive_failures += 1
        status.last_error = error
        
        if status.consecutive_failures >= self.config.unhealthy_threshold:
            if status.healthy:
                logger.error(
                    f"Component '{name}' marked as UNHEALTHY after "
                    f"{status.consecutive_failures} failures"
                )
            status.healthy = False

    def is_healthy(self, name: str) -> bool:
        """Check if component is healthy.
        
        Args:
            name: Component name
            
        Returns:
            True if healthy, False otherwise
        """
        if name not in self.component_status:
            return True  # Assume healthy if not monitored
        
        return self.component_status[name].healthy

    def get_status(self, name: str) -> Optional[HealthStatus]:
        """Get health status of component.
        
        Args:
            name: Component name
            
        Returns:
            HealthStatus or None if not found
        """
        return self.component_status.get(name)

    def get_all_statuses(self) -> Dict[str, HealthStatus]:
        """Get health statuses of all components.
        
        Returns:
            Dictionary mapping component names to health statuses
        """
        return self.component_status.copy()


class ErrorRecoveryManager:
    """Manages error recovery strategies for multi-agent system."""

    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
        health_config: Optional[HealthCheckConfig] = None,
    ):
        """Initialize error recovery manager.
        
        Args:
            retry_config: Retry configuration
            circuit_config: Circuit breaker configuration
            health_config: Health check configuration
        """
        self.retry_manager = RetryManager(retry_config)
        self.health_monitor = HealthMonitor(health_config)
        
        # Circuit breakers per component
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.circuit_config = circuit_config or CircuitBreakerConfig()

    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker for component.
        
        Args:
            name: Component name
            
        Returns:
            CircuitBreaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(self.circuit_config)
        return self.circuit_breakers[name]

    async def execute_with_recovery(
        self,
        name: str,
        func: Callable,
        *args,
        use_circuit_breaker: bool = True,
        use_retry: bool = True,
        retryable_exceptions: tuple = (Exception,),
        **kwargs,
    ):
        """Execute function with full error recovery.
        
        Args:
            name: Component name for tracking
            func: Async function to execute
            *args: Positional arguments
            use_circuit_breaker: Enable circuit breaker
            use_retry: Enable retry logic
            retryable_exceptions: Exceptions to retry on
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        async def _execute():
            if use_circuit_breaker:
                circuit = self.get_circuit_breaker(name)
                return await circuit.call(func, *args, **kwargs)
            else:
                return await func(*args, **kwargs)
        
        if use_retry:
            return await self.retry_manager.execute_with_retry(
                _execute,
                retryable_exceptions=retryable_exceptions,
            )
        else:
            return await _execute()

    async def start_monitoring(self):
        """Start health monitoring."""
        await self.health_monitor.start_monitoring()

    async def stop_monitoring(self):
        """Stop health monitoring."""
        await self.health_monitor.stop_monitoring()
