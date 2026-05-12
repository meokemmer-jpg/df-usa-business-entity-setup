"""
USA-Business-Entity-Setup [CRUX-MK]
Florida-LLC-Formation-Pipeline mit LexVance + Florida-Anwalt + Banking-Stub.

K_0 Touch: LLC-Formation-Fees + Banking + Anwalt-Honorar
Q_0 Touch: USA-Business-Domain als Familien-Vehikel-Vorbereitung
"""
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


# Florida-LLC Formation-Costs (Stand 2026)
FLORIDA_LLC_ARTICLES_FILING_FEE_USD = 125.00  # Articles of Organization
FLORIDA_LLC_ANNUAL_REPORT_FEE_USD = 138.75  # Recurring
EIN_APPLICATION_FEE_USD = 0.00  # IRS-Free
LEXVANCE_HONORAR_EUR_RANGE = (3_000, 8_000)  # Schaetzung
FLORIDA_ANWALT_HONORAR_USD_RANGE = (1_500, 5_000)  # Schaetzung


@dataclass(frozen=True)
class SetupStep:
    """LLC-Setup-Step."""
    step_id: str
    name: str
    category: str  # "formation" | "tax" | "banking" | "compliance" | "coupling"
    status: str  # "pending" | "in-progress" | "complete" | "blocked"
    estimated_cost_usd: float
    estimated_duration_days: int
    blocker: Optional[str] = None


# 9-Step Florida-LLC-Setup-Pipeline
DEFAULT_PIPELINE = [
    SetupStep("S-001", "Florida-LLC Articles of Organization (Sunbiz.org)", "formation", "pending", 125.00, 7),
    SetupStep("S-002", "EIN Application (IRS Form SS-4 online)", "tax", "pending", 0.00, 14, "Requires LLC-Number from S-001"),
    SetupStep("S-003", "Operating Agreement Drafting (Florida-Anwalt)", "formation", "pending", 2_500.00, 14, "Requires Florida-Anwalt-Coordination"),
    SetupStep("S-004", "Registered Agent Service Setup (Florida-Adresse)", "compliance", "pending", 100.00, 3),
    SetupStep("S-005", "Business Banking Account (Chase / Wells Fargo)", "banking", "pending", 0.00, 21, "Requires EIN + Operating Agreement + Owner-In-Person-Visit"),
    SetupStep("S-006", "USA-State-Tax-Registration (Florida)", "tax", "pending", 0.00, 7),
    SetupStep("S-007", "Federal-Tax-Election (S-Corp vs LLC pass-through)", "tax", "pending", 500.00, 14, "Requires Steuerberater + LexVance"),
    SetupStep("S-008", "9OS-NEXT-USA-Coupling-Vorbereitung (Tech-Setup)", "coupling", "pending", 0.00, 30),
    SetupStep("S-009", "Annual-Compliance-Calendar Setup (Florida + IRS)", "compliance", "pending", 0.00, 7),
]


class USABusinessEntitySetup:
    """USA-LLC-Formation-Pipeline-Tracker."""

    def __init__(self, real_enabled: Optional[bool] = None):
        if real_enabled is None:
            real_enabled = os.environ.get("DF_USA_LLC_REAL_ENABLED", "false").lower() == "true"
        self.real_enabled = real_enabled
        self.phronesis_ticket = os.environ.get("PHRONESIS_TICKET", "MISSING")

        if self.real_enabled and self.phronesis_ticket == "MISSING":
            raise RuntimeError(
                "K13-PAV-VIOLATION: USA-LLC-Real-Mode ohne PHRONESIS_TICKET. "
                "LexVance + Florida-Anwalt Coordination Pflicht."
            )

    def get_default_pipeline(self) -> list[SetupStep]:
        return list(DEFAULT_PIPELINE)

    def compute_total_cost(self, steps: list[SetupStep]) -> float:
        """Total Setup-Cost USD."""
        return round(sum(s.estimated_cost_usd for s in steps), 2)

    def compute_total_duration(self, steps: list[SetupStep]) -> int:
        """Sequenzielle Total-Duration (worst case)."""
        return sum(s.estimated_duration_days for s in steps)

    def compute_progress_pct(self, steps: list[SetupStep]) -> float:
        if not steps:
            return 0.0
        complete = sum(1 for s in steps if s.status == "complete")
        return round(complete / len(steps) * 100, 1)

    def get_blocked_steps(self, steps: list[SetupStep]) -> list[SetupStep]:
        """Steps mit status='blocked' ODER non-empty blocker-Field."""
        return [s for s in steps if s.status == "blocked" or s.blocker]

    def get_next_actions(self, steps: list[SetupStep]) -> list[dict]:
        """Naechste Pending-Steps ohne Blocker."""
        results = []
        for s in steps:
            if s.status == "pending" and not s.blocker:
                results.append({
                    "step_id": s.step_id,
                    "name": s.name,
                    "category": s.category,
                    "cost_usd": s.estimated_cost_usd,
                    "duration_days": s.estimated_duration_days,
                })
        return results

    def to_report(self) -> dict:
        steps = self.get_default_pipeline()
        return {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_mode": "real" if self.real_enabled else "sandbox-mock",
            "phronesis_ticket": self.phronesis_ticket,
            "n_steps": len(steps),
            "progress_pct": self.compute_progress_pct(steps),
            "total_cost_usd": self.compute_total_cost(steps),
            "total_duration_days": self.compute_total_duration(steps),
            "lexvance_honorar_eur_range": LEXVANCE_HONORAR_EUR_RANGE,
            "florida_anwalt_honorar_usd_range": FLORIDA_ANWALT_HONORAR_USD_RANGE,
            "blocked_steps": [asdict(s) for s in self.get_blocked_steps(steps)],
            "next_actions": self.get_next_actions(steps),
            "all_steps": [asdict(s) for s in steps],
        }
