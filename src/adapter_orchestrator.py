"""LaunchAgent-Entry [CRUX-MK]"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


class AdapterOrchestrator:
    def __init__(self, state_dir: Optional[str] = None):
        self.state_dir = Path(state_dir or Path.home() / ".df-state" / "usa-business-entity-setup")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.stop_flag = self.state_dir / "STOP.flag"

    def should_run(self) -> tuple[bool, str]:
        if self.stop_flag.exists():
            return False, "STOP.flag set"
        return True, "ok"

    def run_daily(self) -> dict:
        from .usa_llc_main import USABusinessEntitySetup
        from .audit_logger import AuditLogger

        ok, reason = self.should_run()
        if not ok:
            return {"status": "skipped", "reason": reason}

        setup = USABusinessEntitySetup()
        report = setup.to_report()

        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = self.state_dir / f"run-{run_id}.json"
        report_path.write_text(json.dumps(report, indent=2))

        audit = AuditLogger(state_dir=self.state_dir)
        audit.append_event({
            "event": "daily_run_complete",
            "run_id": run_id,
            "progress_pct": report["progress_pct"],
            "n_steps": report["n_steps"],
            "n_blocked": len(report["blocked_steps"]),
            "source_mode": report["source_mode"],
        })
        return {"status": "ok", "run_id": run_id, "report_path": str(report_path)}


if __name__ == "__main__":
    o = AdapterOrchestrator()
    result = o.run_daily()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") in ("ok", "skipped") else 1)
