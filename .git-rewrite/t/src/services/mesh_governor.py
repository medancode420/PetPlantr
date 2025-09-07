"""
Mesh Fidelity Governor for PetPlantr
Automatically adjusts mesh generation quality based on system load to maintain SLOs
"""
import logging
import time
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

# Import with fallback for development
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.settings import settings
    from services.metrics import governor_transitions_total, mesh_preset_active, mesh_fidelity_degraded_total
    SETTINGS_AVAILABLE = True
    METRICS_AVAILABLE = True
except ImportError:
    logger.warning("Settings or metrics not available for mesh governor")
    SETTINGS_AVAILABLE = False
    METRICS_AVAILABLE = False
    # Mock settings for development
    class MockSettings:
        feature_mesh_governor = True
        governor_qdepth_warn = 80
        governor_qdepth_drop = 120
        governor_tokens_warn = 5
        governor_tokens_drop = 8
    settings = MockSettings()
    governor_transitions_total = None
    mesh_preset_active = None
    mesh_fidelity_degraded_total = None


def _get_int(name: str, default: int) -> int:
    """Safely retrieve an int setting, tolerating MagicMock/unset values.

    When tests patch `settings` with a MagicMock and only set some attrs,
    unknown attributes resolve to MagicMock objects which break comparisons.
    This helper coerces to int or returns the provided default.
    """
    try:
        value = getattr(settings, name)
    except Exception:
        return default
    # Treat non-primitive (e.g., MagicMock) as unset
    if not isinstance(value, (int, float, str, bool)):
        return default
    try:
        return int(value)
    except Exception:
        return default

class MeshPreset(Enum):
    """Mesh generation quality presets."""
    BASELINE = "baseline"  # High quality - normal operations
    WARN = "warn"         # Medium quality - under load warning
    DROP = "drop"         # Low quality - emergency load shedding

class MeshGovernor:
    """
    Mesh fidelity governor that adjusts quality based on system load.
    
    Implements three-tier quality degradation:
    - BASELINE: High quality (Shape-E, 64 steps, guidance 7.5)
    - WARN: Medium quality (Shape-E, 40 steps, guidance 6.5) 
    - DROP: Low quality (Point-E, 32 steps, guidance 6.0)
    """
    
    def __init__(self):
        self.current_preset = MeshPreset.BASELINE
        self.last_transition_time = time.time()
        self.transition_history = []
        
        # Quality presets configuration
        self.presets = {
            MeshPreset.BASELINE: {
                "engine": "shape-e",
                "steps": 64,
                "guidance": 7.5,
                "description": "High quality - normal operations",
                "expected_time_sec": 120,
                "quality_score": 1.0
            },
            MeshPreset.WARN: {
                "engine": "shape-e", 
                "steps": 40,
                "guidance": 6.5,
                "description": "Medium quality - load warning",
                "expected_time_sec": 80,
                "quality_score": 0.8
            },
            MeshPreset.DROP: {
                "engine": "point-e",
                "steps": 32,
                "guidance": 6.0,
                "description": "Low quality - emergency load shedding",
                "expected_time_sec": 45,
                "quality_score": 0.6
            }
        }
    
    def select_preset(self, queue_depth: int, tokens_in_use: int) -> Dict[str, Any]:
        """
        Select appropriate mesh preset based on current system load.
        
        Args:
            queue_depth: Current mesh queue depth
            tokens_in_use: Current tokens in use
            
        Returns:
            Dict containing preset configuration and metadata
        """
        if not settings.feature_mesh_governor:
            # Governor disabled - always use baseline
            preset_config = self.presets[MeshPreset.BASELINE].copy()
            preset_config.update({
                "preset": MeshPreset.BASELINE.value,
                "governor_applied": False,
                "reason": "governor_disabled"
            })
            return preset_config
        
        # Determine appropriate preset based on load
        new_preset = self._determine_preset(queue_depth, tokens_in_use)
        
        # Check for preset transition
        if new_preset != self.current_preset:
            self._transition_to_preset(new_preset, queue_depth, tokens_in_use)
        
        # Get preset configuration
        preset_config = self.presets[new_preset].copy()
        preset_config.update({
            "preset": new_preset.value,
            "governor_applied": new_preset != MeshPreset.BASELINE,
            "queue_depth": queue_depth,
            "tokens_in_use": tokens_in_use,
            "reason": self._get_degradation_reason(new_preset, queue_depth, tokens_in_use)
        })
        
        # Record degradation metrics
        if new_preset != MeshPreset.BASELINE and METRICS_AVAILABLE and mesh_fidelity_degraded_total:
            reason = preset_config["reason"]
            mesh_fidelity_degraded_total.labels(reason=reason).inc()
        
        return preset_config
    
    def _determine_preset(self, queue_depth: int, tokens_in_use: int) -> MeshPreset:
        """Determine the appropriate preset based on current load."""
        # Emergency load shedding conditions
        qdepth_drop = _get_int("governor_qdepth_drop", 120)
        tokens_drop = _get_int("governor_tokens_drop", 8)
        if (queue_depth >= qdepth_drop or 
            tokens_in_use >= tokens_drop):
            return MeshPreset.DROP
        
        # Warning level conditions
        qdepth_warn = _get_int("governor_qdepth_warn", 80)
        tokens_warn = _get_int("governor_tokens_warn", 5)
        if (queue_depth >= qdepth_warn or
            tokens_in_use >= tokens_warn):
            return MeshPreset.WARN
        
        # Normal operations
        return MeshPreset.BASELINE
    
    def _transition_to_preset(self, new_preset: MeshPreset, queue_depth: int, tokens_in_use: int):
        """Handle transition to a new preset."""
        old_preset = self.current_preset
        now = time.time()
        
        # Log transition
        old_preset_name = old_preset.value if hasattr(old_preset, 'value') else str(old_preset)
        new_preset_name = new_preset.value if hasattr(new_preset, 'value') else str(new_preset)
        
        logger.info(
            f"Mesh governor transitioning: {old_preset_name} → {new_preset_name} "
            f"(queue: {queue_depth}, tokens: {tokens_in_use})"
        )
        
        # Record transition metrics
        if METRICS_AVAILABLE and governor_transitions_total:
            governor_transitions_total.labels(
                from_preset=old_preset_name,
                to_preset=new_preset_name
            ).inc()
        
        # Update active preset metric
        if METRICS_AVAILABLE and mesh_preset_active:
            preset_values = {
                MeshPreset.BASELINE: 0,
                MeshPreset.WARN: 1,
                MeshPreset.DROP: 2
            }
            mesh_preset_active.set(preset_values[new_preset])
        
        # Update state
        self.current_preset = new_preset
        self.last_transition_time = now
        
        # Track transition history (keep last 100)
        self.transition_history.append({
            "timestamp": now,
            "from_preset": old_preset_name,
            "to_preset": new_preset_name,
            "queue_depth": queue_depth,
            "tokens_in_use": tokens_in_use
        })
        if len(self.transition_history) > 100:
            self.transition_history.pop(0)
    
    def _get_degradation_reason(self, preset: MeshPreset, queue_depth: int, tokens_in_use: int) -> str:
        """Get the reason for quality degradation."""
        if preset == MeshPreset.BASELINE:
            return "none"
        
        reasons: list[str] = []
        qdepth_drop = _get_int("governor_qdepth_drop", 120)
        qdepth_warn = _get_int("governor_qdepth_warn", 80)
        tokens_drop = _get_int("governor_tokens_drop", 8)
        tokens_warn = _get_int("governor_tokens_warn", 5)
        if queue_depth >= qdepth_drop:
            reasons.append("queue_critical")
        elif queue_depth >= qdepth_warn:
            reasons.append("queue_warning")
        
        if tokens_in_use >= tokens_drop:
            reasons.append("tokens_critical")
        elif tokens_in_use >= tokens_warn:
            reasons.append("tokens_warning")
        
        return "_".join(reasons) if reasons else "load_balancing"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current governor statistics."""
        return {
            "enabled": settings.feature_mesh_governor,
            "current_preset": self.current_preset.value,
            "preset_config": self.presets[self.current_preset],
            "last_transition": self.last_transition_time,
            "transitions_count": len(self.transition_history),
            "thresholds": {
                "queue_warn": _get_int("governor_qdepth_warn", 80),
                "queue_drop": _get_int("governor_qdepth_drop", 120),
                "tokens_warn": _get_int("governor_tokens_warn", 5),
                "tokens_drop": _get_int("governor_tokens_drop", 8)
            },
            "recent_transitions": self.transition_history[-5:] if self.transition_history else []
        }
    
    def force_preset(self, preset: MeshPreset, reason: str = "manual"):
        """Force a specific preset (for testing/emergency use)."""
        if preset != self.current_preset:
            logger.warning(f"Manually forcing mesh preset to {preset.value}: {reason}")
            self._transition_to_preset(preset, 0, 0)

# Global mesh governor instance
mesh_governor = MeshGovernor()

def select_mesh_preset(queue_depth: int, tokens_in_use: int) -> Dict[str, Any]:
    """
    Select appropriate mesh generation preset based on current load.
    
    This is the main interface used by mesh generation routes.
    
    Args:
        queue_depth: Current mesh generation queue depth
        tokens_in_use: Current processing tokens in use
        
    Returns:
        Dict containing:
        - engine: "shape-e" or "point-e"
        - steps: Number of generation steps
        - guidance: Guidance scale
        - preset: Preset name ("baseline", "warn", "drop")
        - governor_applied: Boolean indicating if quality was degraded
        - reason: Reason for degradation if applicable
        - expected_time_sec: Expected generation time
        - quality_score: Quality score (0-1)
    """
    return mesh_governor.select_preset(queue_depth, tokens_in_use)

def get_mesh_governor_stats() -> Dict[str, Any]:
    """Get current mesh governor statistics."""
    return mesh_governor.get_stats()

def force_mesh_preset(preset_name: str, reason: str = "manual"):
    """Force a specific mesh preset (for testing/emergency)."""
    preset_map = {
        "baseline": MeshPreset.BASELINE,
        "warn": MeshPreset.WARN, 
        "drop": MeshPreset.DROP
    }
    
    if preset_name in preset_map:
        mesh_governor.force_preset(preset_map[preset_name], reason)
    else:
        raise ValueError(f"Unknown preset: {preset_name}. Valid options: {list(preset_map.keys())}")

# Export the main interface
__all__ = [
    "select_mesh_preset",
    "get_mesh_governor_stats",
    "force_mesh_preset",
    "MeshPreset",
    "mesh_governor"
]
