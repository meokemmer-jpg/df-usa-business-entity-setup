"""Tests fuer AdapterOrchestrator [CRUX-MK]."""
import json
import tempfile
from pathlib import Path
import pytest
from src.adapter_orchestrator import AdapterOrchestrator


@pytest.fixture
def tmp_state_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_should_run_default_ok(tmp_state_dir):
    o = AdapterOrchestrator(state_dir=tmp_state_dir)
    ok, _ = o.should_run()
    assert ok is True


def test_should_run_blocked_by_stop(tmp_state_dir):
    o = AdapterOrchestrator(state_dir=tmp_state_dir)
    o.stop_flag.write_text("halt")
    ok, _ = o.should_run()
    assert ok is False


def test_run_daily_persists_report(tmp_state_dir):
    o = AdapterOrchestrator(state_dir=tmp_state_dir)
    result = o.run_daily()
    assert result["status"] == "ok"
    report = json.loads(Path(result["report_path"]).read_text())
    assert report["n_steps"] == 9
    assert report["source_mode"] == "sandbox-mock"


def test_run_daily_skipped(tmp_state_dir):
    o = AdapterOrchestrator(state_dir=tmp_state_dir)
    o.stop_flag.write_text("halt")
    result = o.run_daily()
    assert result["status"] == "skipped"
