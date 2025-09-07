from typing import Optional

class ProviderBusy(Exception):
    """Upstream provider (e.g., Replicate) is overloaded or rate-limiting.
    Raise this from any upstream wrapper when you observe a 429/503.
    """
    def __init__(self, status: int, message: str = "provider busy", retry_after: Optional[str] = None):
        super().__init__(message)
        self.status = int(status)
        self.retry_after = retry_after
