"""HMAC-SHA256-basierter Audit-Logger [CRUX-MK]"""
import hmac
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class AuditLogger:
    def __init__(self, state_dir: Path, secret_env: str = "DF_AUDIT_SECRET"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.state_dir / "audit-log.jsonl"
        self.secret = os.environ.get(secret_env, "sandbox-default-secret-NOT-FOR-PROD").encode()

    def _last_hash(self) -> str:
        if not self.log_path.exists():
            return "0" * 64
        last_line = ""
        for line in self.log_path.read_text().splitlines():
            if line.strip():
                last_line = line
        if not last_line:
            return "0" * 64
        try:
            return json.loads(last_line).get("chain_hash", "0" * 64)
        except json.JSONDecodeError:
            return "0" * 64

    def append_event(self, event: dict) -> dict:
        prev_hash = self._last_hash()
        record = {"ts": datetime.now(timezone.utc).isoformat(), "prev_hash": prev_hash, **event}
        payload = json.dumps(record, sort_keys=True).encode()
        chain_hash = hmac.new(self.secret, prev_hash.encode() + payload, hashlib.sha256).hexdigest()
        record["chain_hash"] = chain_hash
        with self.log_path.open("a") as f:
            f.write(json.dumps(record) + "\n")
        return record

    def verify_chain(self) -> tuple[bool, Optional[str]]:
        if not self.log_path.exists():
            return True, None
        prev = "0" * 64
        for i, line in enumerate(self.log_path.read_text().splitlines()):
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("prev_hash") != prev:
                return False, f"chain-break at record {i}"
            payload_rec = {k: v for k, v in rec.items() if k != "chain_hash"}
            payload = json.dumps(payload_rec, sort_keys=True).encode()
            expected = hmac.new(self.secret, prev.encode() + payload, hashlib.sha256).hexdigest()
            if rec.get("chain_hash") != expected:
                return False, f"hash-mismatch at record {i}"
            prev = rec["chain_hash"]
        return True, None
