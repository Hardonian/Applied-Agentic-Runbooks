"""
Experiment tracking and A/B testing framework for Agent Factory Platform.

Enables researchers and data scientists to track experiments, compare variants,
and analyze results.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ExperimentStatus(str, Enum):
    """Experiment status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VariantType(str, Enum):
    """Variant types."""
    CONTROL = "control"
    TREATMENT = "treatment"


@dataclass
class Variant:
    """Experiment variant."""
    id: str
    name: str
    variant_type: VariantType
    config: dict[str, Any]
    allocation_percent: float = 50.0  # Percentage of traffic


@dataclass
class ExperimentResult:
    """Result of an experiment run."""
    variant_id: str
    success: bool
    metrics: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Experiment:
    """Experiment definition."""
    id: str
    name: str
    description: str
    variants: list[Variant]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    start_date: datetime | None = None
    end_date: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ExperimentTracker:
    """
    Tracks experiments and A/B tests.
    
    Example:
        >>> tracker = ExperimentTracker()
        >>> experiment = tracker.create_experiment(
        ...     name="Model Comparison",
        ...     variants=[
        ...         Variant("control", "gpt-4o", VariantType.CONTROL),
        ...         Variant("treatment", "claude-3", VariantType.TREATMENT)
        ...     ]
        ... )
        >>> result = tracker.record_result(experiment.id, "control", success=True, metrics={"accuracy": 0.95})
    """
    
    def __init__(self):
        """Initialize experiment tracker."""
        self.experiments: dict[str, Experiment] = {}
        self.results: dict[str, list[ExperimentResult]] = {}
    
    def create_experiment(
        self,
        name: str,
        description: str,
        variants: list[Variant],
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Experiment:
        """
        Create a new experiment.
        
        Args:
            name: Experiment name
            description: Experiment description
            variants: List of variants
            created_by: Creator identifier
            metadata: Optional metadata
            
        Returns:
            Created experiment
        """
        experiment_id = str(uuid.uuid4())
        
        # Validate variants
        total_allocation = sum(v.allocation_percent for v in variants)
        if abs(total_allocation - 100.0) > 0.01:
            raise ValueError(f"Variant allocation must sum to 100%, got {total_allocation}%")
        
        experiment = Experiment(
            id=experiment_id,
            name=name,
            description=description,
            variants=variants,
            created_by=created_by,
            metadata=metadata or {},
        )
        
        self.experiments[experiment_id] = experiment
        self.results[experiment_id] = []
        
        return experiment
    
    def start_experiment(self, experiment_id: str) -> None:
        """
        Start an experiment.
        
        Args:
            experiment_id: Experiment ID
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.start_date = datetime.utcnow()
    
    def pause_experiment(self, experiment_id: str) -> None:
        """Pause an experiment."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        experiment.status = ExperimentStatus.PAUSED
    
    def complete_experiment(self, experiment_id: str) -> None:
        """Complete an experiment."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_date = datetime.utcnow()
    
    def assign_variant(self, experiment_id: str, user_id: str) -> Variant:
        """
        Assign a variant to a user (deterministic).
        
        Args:
            experiment_id: Experiment ID
            user_id: User identifier
            
        Returns:
            Assigned variant
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        if experiment.status != ExperimentStatus.RUNNING:
            # Return control variant if experiment not running
            return next(v for v in experiment.variants if v.variant_type == VariantType.CONTROL)
        
        # Deterministic assignment based on user_id hash
        import hashlib
        hash_value = int(hashlib.md5(f"{experiment_id}:{user_id}".encode()).hexdigest(), 16)
        assignment = (hash_value % 10000) / 100.0
        
        cumulative = 0.0
        for variant in experiment.variants:
            cumulative += variant.allocation_percent
            if assignment < cumulative:
                return variant
        
        # Fallback to last variant
        return experiment.variants[-1]
    
    def record_result(
        self,
        experiment_id: str,
        variant_id: str,
        success: bool,
        metrics: dict[str, float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Record an experiment result.
        
        Args:
            experiment_id: Experiment ID
            variant_id: Variant ID
            success: Whether the run was successful
            metrics: Metrics dictionary
            metadata: Optional metadata
        """
        if experiment_id not in self.results:
            self.results[experiment_id] = []
        
        result = ExperimentResult(
            variant_id=variant_id,
            success=success,
            metrics=metrics,
            metadata=metadata or {},
        )
        
        self.results[experiment_id].append(result)
    
    def get_experiment_results(self, experiment_id: str) -> dict[str, Any]:
        """
        Get experiment results and statistics.
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            Results dictionary with statistics
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        results = self.results.get(experiment_id, [])
        
        # Calculate statistics per variant
        variant_stats = {}
        for variant in experiment.variants:
            variant_results = [r for r in results if r.variant_id == variant.id]
            
            if not variant_results:
                variant_stats[variant.id] = {
                    "count": 0,
                    "success_rate": 0.0,
                    "metrics": {},
                }
                continue
            
            success_count = sum(1 for r in variant_results if r.success)
            success_rate = success_count / len(variant_results)
            
            # Aggregate metrics
            metrics = {}
            if variant_results:
                metric_keys = variant_results[0].metrics.keys()
                for key in metric_keys:
                    values = [r.metrics[key] for r in variant_results if key in r.metrics]
                    if values:
                        metrics[key] = {
                            "mean": sum(values) / len(values),
                            "min": min(values),
                            "max": max(values),
                            "count": len(values),
                        }
            
            variant_stats[variant.id] = {
                "count": len(variant_results),
                "success_rate": success_rate,
                "metrics": metrics,
            }
        
        # Compare variants
        comparisons = {}
        control_variant = next(
            (v for v in experiment.variants if v.variant_type == VariantType.CONTROL),
            None
        )
        
        if control_variant and control_variant.id in variant_stats:
            control_stats = variant_stats[control_variant.id]
            
            for variant in experiment.variants:
                if variant.variant_type == VariantType.TREATMENT:
                    treatment_stats = variant_stats[variant.id]
                    
                    ctrl_rate = float(str(control_stats["success_rate"]))
                    treat_rate = float(str(treatment_stats["success_rate"]))
                    if ctrl_rate > 0:
                        improvement = (
                            (treat_rate - ctrl_rate)
                            / ctrl_rate
                            * 100
                        )
                    else:
                        improvement = 0.0
                    
                    comparisons[variant.id] = {
                        "improvement_percent": improvement,
                        "control_success_rate": control_stats["success_rate"],
                        "treatment_success_rate": treatment_stats["success_rate"],
                    }
        
        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment.name,
            "status": experiment.status.value,
            "total_runs": len(results),
            "variant_stats": variant_stats,
            "comparisons": comparisons,
            "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
            "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
        }
    
    def list_experiments(
        self,
        status: ExperimentStatus | None = None,
        created_by: str | None = None,
    ) -> list[Experiment]:
        """
        List experiments with optional filters.
        
        Args:
            status: Filter by status
            created_by: Filter by creator
            
        Returns:
            List of experiments
        """
        results = list(self.experiments.values())
        
        if status:
            results = [e for e in results if e.status == status]
        
        if created_by:
            results = [e for e in results if e.created_by == created_by]
        
        return results


# Global instance
_experiment_tracker: ExperimentTracker | None = None


def get_experiment_tracker() -> ExperimentTracker:
    """Get global experiment tracker instance."""
    global _experiment_tracker
    if _experiment_tracker is None:
        _experiment_tracker = ExperimentTracker()
    return _experiment_tracker
