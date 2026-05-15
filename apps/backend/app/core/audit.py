"""Audit logging for write operations."""
import json, logging, os
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG = Path(os.getenv("AUDIT_LOG_PATH", "/var/log/medi-vault/audit.jsonl"))
AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("audit")

def audit_log(action: str, user_id: str | None, resource: str, details: dict | None = None):
    """Write an audit log entry."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "user_id": user_id or "anonymous",
        "resource": resource,
        "details": details or {},
    }
    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    logger.info(f"AUDIT: {action} on {resource} by {user_id}")
