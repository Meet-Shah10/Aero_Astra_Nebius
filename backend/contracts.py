"""
AERO-ASTRA — Shared Data Contracts
====================================
Cross-agent data types that do not belong to any single agent module.

Design rationale:
- IncidentContext carries a single incident_id, agent identity, model info,
  and timing through the entire pipeline so downstream consumers (SCRIBE,
  CHRONICLE, audit logs) can join records from different agents without
  timestamp heuristics.
- AnomalyEvent and its enums (SeverityLevel, UrgencyLevel) are defined here
  because they are produced by SENTINEL and consumed by SHERLOCK — they
  should not live inside either agent's private schema module.
  For backward compatibility, sherlock.schemas re-exports them.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Enums — shared across agents
# ─────────────────────────────────────────────────────────────────────────────


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UrgencyLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ─────────────────────────────────────────────────────────────────────────────
# AnomalyEvent — produced by SENTINEL, consumed by SHERLOCK
# ─────────────────────────────────────────────────────────────────────────────


class AnomalyEvent(BaseModel):
    """
    The anomaly event payload SHERLOCK receives from an upstream source
    (typically SENTINEL). CHRONICLE's event log context is optional —
    SHERLOCK degrades gracefully and still produces a valid diagnosis
    without it.
    """

    anomaly_id: str = Field(..., description="Unique identifier for this anomaly event")
    flagged_subsystem: str = Field(
        ...,
        description=(
            "The subsystem in which the anomaly was detected. "
            "Must be one of the 6 modelled subsystems: "
            "EPS, TCS, ADCS, OBC, TT&C, Propulsion"
        ),
    )
    flagged_parameter: str = Field(
        ...,
        description="Specific telemetry parameter that triggered the anomaly flag",
    )
    severity: SeverityLevel = Field(
        ..., description="Severity level assigned by the upstream detector"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Upstream detector's confidence in this being a real anomaly (0-1)",
    )
    timestamp: datetime = Field(
        ..., description="UTC timestamp when the anomaly was detected"
    )
    telemetry_window: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Raw telemetry rows around the anomaly window. "
            "Each row is a dict of parameter->value. May be empty."
        ),
    )
    event_log_context: str | None = Field(
        default=None,
        description=(
            "Formatted event log context from CHRONICLE, if available. "
            "SHERLOCK works correctly without this (graceful degradation)."
        ),
    )

    @field_validator("confidence_score")
    @classmethod
    def _validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"confidence_score must be in [0, 1], got {v}")
        return round(v, 4)


# ─────────────────────────────────────────────────────────────────────────────
# IncidentContext — threaded through every agent output
# ─────────────────────────────────────────────────────────────────────────────


class IncidentContext(BaseModel):
    """
    Provenance record attached to every agent output and WebSocket message.

    A single incident_id is generated when SENTINEL fires, and every
    downstream agent (SHERLOCK, ORACLE, ATHENA, GUARDIAN, SCRIBE) includes
    its own IncidentContext with that same incident_id. This enables
    reliable join across the pipeline's outputs without timestamp heuristics.
    """

    incident_id: str = Field(
        ...,
        description="UUID4 shared by all agents processing the same anomaly.",
    )
    agent: str = Field(
        ...,
        description="Agent name: SENTINEL, SHERLOCK, ORACLE, ATHENA, GUARDIAN, SCRIBE.",
    )
    model: str | None = Field(
        default=None,
        description="LLM model slug (e.g. 'nvidia/Nemotron-3_5-Lightning'). None for non-LLM agents.",
    )
    provider: str | None = Field(
        default=None,
        description="LLM provider name (e.g. 'Nebius Token Factory'). None for non-LLM agents.",
    )
    latency_ms: int = Field(
        default=0,
        ge=0,
        description="Wall-clock time this agent spent, in milliseconds.",
    )
    tokens_in: int | None = Field(
        default=None,
        description="Prompt tokens consumed. None if not an LLM call.",
    )
    tokens_out: int | None = Field(
        default=None,
        description="Completion tokens produced. None if not an LLM call.",
    )
    attempts: int = Field(
        default=1,
        ge=1,
        description="Number of LLM/retry attempts (1 = succeeded first try).",
    )
    ts_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when this record was produced.",
    )

    @staticmethod
    def new_incident_id() -> str:
        """Generate a new UUID4 incident ID."""
        return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# Diagnosis-to-fault hypothesis mapping (V1 fix)
# ─────────────────────────────────────────────────────────────────────────────

# Maps SHERLOCK's primary_root_cause (a subsystem name) to the candidate
# fault hypotheses that ORACLE should test. This ensures ORACLE never
# receives the simulator's ground-truth fault label — only plausible
# hypotheses derived from the diagnosis.
#
# When a subsystem maps to multiple faults, ORACLE tests all of them and
# picks the one with the best recovery score. This is physically correct:
# a "TCS" root cause could be either a thermal runaway or a heater failure,
# and the recovery strategy differs.

DIAGNOSIS_TO_FAULT_HYPOTHESES: dict[str, list[str]] = {
    "TCS":        ["tcs_thermal_runaway"],
    "EPS":        ["eps_battery_degradation", "eps_cascade_power_failure"],
    "ADCS":       ["adcs_reaction_wheel_degradation", "adcs_sensor_fusion_failure"],
    "Propulsion": ["propulsion_thruster_fault"],
    "TT&C":       ["ttc_signal_dropout"],
    "OBC":        [],  # no fault model for OBC yet
}
