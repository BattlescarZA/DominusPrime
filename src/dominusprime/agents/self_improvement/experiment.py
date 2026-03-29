# -*- coding: utf-8 -*-
"""
Experiment tracking and logging system.
"""

import os
import csv
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class Experiment:
    """Single experiment record."""
    
    # Identification
    commit_hash: str
    experiment_id: str
    timestamp: str
    
    # Hypothesis
    hypothesis: str
    strategy: str  # "incremental", "radical", "simplification", etc.
    
    # Results
    metric_value: float
    metric_name: str
    memory_gb: float
    execution_time: float
    
    # Decision
    status: str  # "keep", "discard", "crash"
    
    # Additional data
    secondary_metrics: Dict[str, float] = None
    tests_passed: int = 0
    tests_total: int = 0
    lines_of_code: int = 0
    error_message: Optional[str] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.secondary_metrics is None:
            self.secondary_metrics = {}
    
    def to_tsv_row(self) -> List[str]:
        """
        Convert to TSV row format (matching autoresearch format).
        
        Format: commit	val_metric	memory_gb	status	description
        """
        return [
            self.commit_hash[:7],  # Short hash
            f"{self.metric_value:.6f}",
            f"{self.memory_gb:.1f}",
            self.status,
            self.hypothesis,
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        return data


class ExperimentLog:
    """
    Manages experiment logging to file.
    
    Maintains two formats:
    1. TSV file (simple, autoresearch-compatible)
    2. JSON file (detailed, machine-readable)
    """
    
    def __init__(self, log_dir: str, experiment_name: str):
        self.log_dir = Path(log_dir)
        self.experiment_name = experiment_name
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.tsv_path = self.log_dir / "results.tsv"
        self.json_path = self.log_dir / "experiments.json"
        self.summary_path = self.log_dir / "summary.json"
        
        # Initialize files if needed
        self._initialize_files()
        
        # In-memory cache
        self.experiments: List[Experiment] = []
        self._load_experiments()
    
    def _initialize_files(self):
        """Initialize log files with headers."""
        # TSV header
        if not self.tsv_path.exists():
            with open(self.tsv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(['commit', 'val_metric', 'memory_gb', 'status', 'description'])
        
        # JSON file
        if not self.json_path.exists():
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _load_experiments(self):
        """Load existing experiments from JSON file."""
        if self.json_path.exists():
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert dicts back to Experiment objects
                    for exp_dict in data:
                        exp = Experiment(**exp_dict)
                        self.experiments.append(exp)
            except Exception as e:
                print(f"Warning: Could not load experiments: {e}")
    
    def log_experiment(self, experiment: Experiment):
        """
        Log an experiment to both TSV and JSON files.
        
        Args:
            experiment: Experiment to log
        """
        # Add to in-memory cache
        self.experiments.append(experiment)
        
        # Append to TSV
        with open(self.tsv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(experiment.to_tsv_row())
        
        # Update JSON (write all experiments)
        with open(self.json_path, 'w', encoding='utf-8') as f:
            data = [exp.to_dict() for exp in self.experiments]
            json.dump(data, f, indent=2)
        
        # Update summary
        self._update_summary()
    
    def _update_summary(self):
        """Update summary statistics."""
        if not self.experiments:
            return
        
        total = len(self.experiments)
        kept = sum(1 for e in self.experiments if e.status == "keep")
        discarded = sum(1 for e in self.experiments if e.status == "discard")
        crashed = sum(1 for e in self.experiments if e.status == "crash")
        
        # Find best experiment
        kept_experiments = [e for e in self.experiments if e.status == "keep"]
        if kept_experiments:
            best = max(kept_experiments, key=lambda e: e.metric_value)
            best_metric = best.metric_value
            best_commit = best.commit_hash
        else:
            best_metric = 0.0
            best_commit = ""
        
        # Calculate improvement
        if kept_experiments:
            first_kept = kept_experiments[0]
            improvement = best_metric - first_kept.metric_value
            improvement_pct = (improvement / first_kept.metric_value * 100) if first_kept.metric_value != 0 else 0
        else:
            improvement = 0.0
            improvement_pct = 0.0
        
        summary = {
            "experiment_name": self.experiment_name,
            "total_experiments": total,
            "kept": kept,
            "discarded": discarded,
            "crashed": crashed,
            "success_rate": kept / total if total > 0 else 0,
            "best_metric": best_metric,
            "best_commit": best_commit,
            "total_improvement": improvement,
            "improvement_percentage": improvement_pct,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        with open(self.summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
    
    def get_baseline(self) -> Optional[Experiment]:
        """Get the baseline (first kept experiment)."""
        kept = [e for e in self.experiments if e.status == "keep"]
        return kept[0] if kept else None
    
    def get_best(self) -> Optional[Experiment]:
        """Get the best experiment so far."""
        kept = [e for e in self.experiments if e.status == "keep"]
        if not kept:
            return None
        return max(kept, key=lambda e: e.metric_value)
    
    def get_recent(self, n: int = 10) -> List[Experiment]:
        """Get the n most recent experiments."""
        return self.experiments[-n:]
    
    def get_history(self) -> List[Experiment]:
        """Get all experiments."""
        return self.experiments
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if self.summary_path.exists():
            with open(self.summary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}


class GitManager:
    """Manages git operations for experiments."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def create_branch(self, branch_name: str) -> bool:
        """Create and checkout a new branch."""
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False
    
    def commit(self, message: str, files: Optional[List[str]] = None) -> Optional[str]:
        """
        Commit changes and return commit hash.
        
        Args:
            message: Commit message
            files: List of files to commit (None = all changes)
        
        Returns:
            Commit hash or None if failed
        """
        import subprocess
        try:
            # Add files
            if files:
                for file in files:
                    subprocess.run(['git', 'add', file], cwd=self.repo_path, check=True)
            else:
                subprocess.run(['git', 'add', '-A'], cwd=self.repo_path, check=True)
            
            # Commit
            subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Get commit hash
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def reset_to_commit(self, commit_hash: str) -> bool:
        """Reset to a specific commit."""
        import subprocess
        try:
            subprocess.run(
                ['git', 'reset', '--hard', commit_hash],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_current_commit(self) -> Optional[str]:
        """Get current commit hash."""
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def get_diff(self, commit1: str, commit2: str) -> str:
        """Get diff between two commits."""
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'diff', commit1, commit2],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""
