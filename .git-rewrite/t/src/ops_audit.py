import time, json, logging, hashlib, os
from collections import deque
from typing import Any, Dict, List, Optional
from logging.handlers import RotatingFileHandler

class OpsAudit:
    def __init__(self, max_entries: int = 200, file_path: Optional[str] = None):
        self.buffer = deque(maxlen=max_entries)
        self.log = logging.getLogger("ops.audit")
        self.log.setLevel(logging.INFO)
        if file_path:
            handler = RotatingFileHandler(file_path, maxBytes=5*1024*1024, backupCount=3)
            fmt = logging.Formatter("%(message)s")
            handler.setFormatter(fmt)
            self.log.addHandler(handler)

    def _actor(self, request) -> str:
        tok = request.headers.get("X-Ops-Token")
        if tok:
            digest = hashlib.sha256(tok.encode()).hexdigest()[:8]
            return f"ops:{digest}"
        return "ops:unknown"

    def _ip(self, request) -> Optional[str]:
        try:
            xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
            if xff:
                return xff.split(",")[0].strip()
        except Exception:
            pass
        try:
            return request.client.host if request.client else None
        except Exception:
            return None

    def _sanitize(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        red: Dict[str, Any] = {}
        for k, v in (changes or {}).items():
            if "token" in k.lower() or "secret" in k.lower():
                red[k] = "***"
            else:
                red[k] = v
        return red

    def record(self, request, action: str, status: str, changes: Optional[Dict[str, Any]] = None, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        entry = {
            "ts": int(time.time()),
            "action": action,
            "status": status,
            "actor": self._actor(request),
            "ip": self._ip(request),
            "ua": request.headers.get("user-agent"),
            "path": request.url.path,
            "changes": self._sanitize(changes or {}),
            "meta": meta or {},
            "request_id": request.headers.get("X-Request-ID"),
        }
        self.buffer.append(entry)
        try:
            self.log.info(json.dumps(entry, separators=(",", ":")))
        except Exception:
            # logging should never break ops path
            pass
        return entry

    def recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []
        m = min(limit, len(self.buffer))
        return list(self.buffer)[-m:]

def init_ops_audit(app):
    max_entries = int(os.getenv("OPS_AUDIT_MAX", "200"))
    file_path = os.getenv("OPS_AUDIT_FILE")  # optional
    try:
        app.state.audit = OpsAudit(max_entries=max_entries, file_path=file_path)
    except Exception:
        # Ensure app still boots even if file sink is not writable
        app.state.audit = OpsAudit(max_entries=max_entries, file_path=None)
