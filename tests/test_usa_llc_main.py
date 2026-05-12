"""Tests fuer USABusinessEntitySetup [CRUX-MK]."""
import pytest
from src.usa_llc_main import (
    USABusinessEntitySetup, DEFAULT_PIPELINE, SetupStep,
    FLORIDA_LLC_ARTICLES_FILING_FEE_USD, EIN_APPLICATION_FEE_USD
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("DF_USA_LLC_REAL_ENABLED", raising=False)
    monkeypatch.delenv("PHRONESIS_TICKET", raising=False)


def test_default_sandbox_mode():
    s = USABusinessEntitySetup()
    assert s.real_enabled is False


def test_real_mode_requires_phronesis(monkeypatch):
    monkeypatch.setenv("DF_USA_LLC_REAL_ENABLED", "true")
    with pytest.raises(RuntimeError, match="K13-PAV-VIOLATION"):
        USABusinessEntitySetup()


def test_default_pipeline_9_steps():
    s = USABusinessEntitySetup()
    pipeline = s.get_default_pipeline()
    assert len(pipeline) == 9
    categories = {step.category for step in pipeline}
    assert "formation" in categories
    assert "tax" in categories
    assert "banking" in categories
    assert "compliance" in categories
    assert "coupling" in categories


def test_florida_articles_fee_constant():
    """Florida LLC Articles of Organization Filing-Fee = $125 (Stand 2026)."""
    assert FLORIDA_LLC_ARTICLES_FILING_FEE_USD == 125.00


def test_ein_free_constant():
    """EIN-Application via IRS = free."""
    assert EIN_APPLICATION_FEE_USD == 0.00


def test_compute_total_cost():
    s = USABusinessEntitySetup()
    pipeline = s.get_default_pipeline()
    total = s.compute_total_cost(pipeline)
    # 125 + 0 + 2500 + 100 + 0 + 0 + 500 + 0 + 0 = 3225
    assert total == 3225.00


def test_compute_total_duration():
    s = USABusinessEntitySetup()
    pipeline = s.get_default_pipeline()
    duration = s.compute_total_duration(pipeline)
    # 7+14+14+3+21+7+14+30+7 = 117
    assert duration == 117


def test_progress_pct_zero_at_start():
    s = USABusinessEntitySetup()
    pipeline = s.get_default_pipeline()
    assert s.compute_progress_pct(pipeline) == 0.0


def test_progress_pct_full_when_all_complete():
    s = USABusinessEntitySetup()
    pipeline = [
        SetupStep(p.step_id, p.name, p.category, "complete", p.estimated_cost_usd, p.estimated_duration_days, p.blocker)
        for p in DEFAULT_PIPELINE
    ]
    assert s.compute_progress_pct(pipeline) == 100.0


def test_blocked_steps_detected():
    """S-002 + S-003 + S-005 + S-007 sind blocked by default."""
    s = USABusinessEntitySetup()
    pipeline = s.get_default_pipeline()
    blocked = s.get_blocked_steps(pipeline)
    # S-002 (EIN waits for LLC), S-003 (Anwalt), S-005 (Banking), S-007 (Tax)
    assert len(blocked) == 4
    blocker_step_ids = {s.step_id for s in blocked}
    assert "S-002" in blocker_step_ids
    assert "S-005" in blocker_step_ids


def test_get_next_actions_excludes_blocked():
    s = USABusinessEntitySetup()
    pipeline = s.get_default_pipeline()
    next_actions = s.get_next_actions(pipeline)
    # 9 steps - 4 blocked = 5 unblocked, all pending
    assert len(next_actions) == 5
    step_ids = {a["step_id"] for a in next_actions}
    assert "S-001" in step_ids  # First step always actionable
    assert "S-002" not in step_ids  # Blocked


def test_to_report_includes_pipeline_data():
    s = USABusinessEntitySetup()
    report = s.to_report()
    assert report["n_steps"] == 9
    assert report["progress_pct"] == 0.0
    assert report["total_cost_usd"] == 3225.00
    assert report["total_duration_days"] == 117
    assert "lexvance_honorar_eur_range" in report
    assert "florida_anwalt_honorar_usd_range" in report
    assert report["source_mode"] == "sandbox-mock"


def test_to_report_blocked_steps_present():
    s = USABusinessEntitySetup()
    report = s.to_report()
    assert len(report["blocked_steps"]) == 4
