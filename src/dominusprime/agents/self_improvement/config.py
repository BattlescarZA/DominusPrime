# -*- coding: utf-8 -*-
"""
Configuration classes for self-improvement system.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ImprovementConfig:
    """Configuration for self-improvement experiments."""
    
    # Evaluation
    metric_name: str  # e.g., "f1_score", "success_rate", "response_quality"
    time_budget_seconds: int = 300  # fixed time budget for experiments (5 min default)
    evaluation_samples: int = 20  # number of test cases
    
    # Experiment management
    max_iterations: Optional[int] = None  # None = infinite
    git_enabled: bool = True
    auto_commit: bool = True
    experiment_branch_prefix: str = "improve"
    
    # Decision criteria
    improvement_threshold: float = 0.001  # minimum improvement to keep (0.1%)
    simplicity_bonus: float = 0.01  # bonus for code reduction (1%)
    equal_threshold: float = 0.0005  # within this range = equal performance
    
    # Safety
    max_memory_mb: int = 4096
    max_cpu_percent: int = 80
    crash_tolerance: int = 3  # max consecutive crashes before stopping
    sandbox_enabled: bool = True
    
    # Agent configuration
    llm_model: str = "claude-sonnet-4"
    temperature: float = 0.7
    context_window: int = 100000  # for reading code/history
    
    # Hypothesis generation
    hypothesis_strategies: List[str] = field(default_factory=lambda: [
        "incremental",  # Small tweaks to existing code
        "radical",      # Major architectural changes
        "simplification",  # Remove complexity
        "ensemble",     # Combine multiple approaches
    ])
    
    # Logging
    log_file: str = "improvement.log"
    results_file: str = "results.tsv"
    verbose: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if self.improvement_threshold < 0:
            raise ValueError("improvement_threshold must be non-negative")
        if self.time_budget_seconds <= 0:
            raise ValueError("time_budget_seconds must be positive")
        if self.evaluation_samples <= 0:
            raise ValueError("evaluation_samples must be positive")


@dataclass
class ImprovementPolicy:
    """Governance policy for self-improvement."""
    
    # What can be modified
    allowed_files: List[str] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=lambda: [
        r"__version__",  # Don't modify version strings
        r"LICENSE",      # Don't modify license
        r"\.git/",       # Don't touch git internals
        r"password",     # Don't expose credentials
        r"secret",
        r"api_key",
    ])
    
    # Approval requirements
    require_human_approval_for: List[str] = field(default_factory=lambda: [
        "security",      # Security-related changes
        "data_access",   # Data access patterns
        "network",       # Network operations
        "file_system",   # File system operations
    ])
    
    # Resource limits
    max_memory_mb: int = 4096
    max_cpu_percent: int = 80
    max_disk_mb: int = 1024
    max_experiments_per_day: int = 1000
    max_consecutive_failures: int = 5
    
    # Monitoring
    alert_on_performance_drop: bool = True
    alert_threshold: float = 0.05  # Alert if performance drops > 5%
    log_all_changes: bool = True
    enable_telemetry: bool = True
    
    # Safety
    enable_rollback: bool = True
    auto_rollback_on_crash: bool = True
    sandbox_experiments: bool = True
    kill_switch_enabled: bool = True
    
    def is_file_allowed(self, filepath: str) -> bool:
        """Check if a file is allowed to be modified."""
        import re
        
        if not self.allowed_files:
            # If no explicit allow list, check forbidden patterns
            for pattern in self.forbidden_patterns:
                if re.search(pattern, filepath, re.IGNORECASE):
                    return False
            return True
        
        # If allow list exists, file must be in it
        return any(allowed in filepath for allowed in self.allowed_files)
    
    def requires_approval(self, change_category: str) -> bool:
        """Check if a change category requires human approval."""
        return change_category.lower() in [cat.lower() for cat in self.require_human_approval_for]


@dataclass
class ExperimentMetadata:
    """Metadata for an experiment."""
    
    experiment_id: str
    timestamp: str
    branch_name: str
    commit_hash: Optional[str] = None
    parent_commit: Optional[str] = None
    
    # Hypothesis
    hypothesis: str = ""
    hypothesis_strategy: str = "incremental"
    
    # Configuration
    config: Optional[Dict[str, Any]] = None
    
    # Tags for organization
    tags: List[str] = field(default_factory=list)
    
    # Human notes
    notes: str = ""
