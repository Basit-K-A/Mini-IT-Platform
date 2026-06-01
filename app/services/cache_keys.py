"""Cache key builders — single place for naming conventions."""


class CacheKeys:
    @staticmethod
    def dashboard_overview() -> str:
        return "dashboard:overview"

    @staticmethod
    def dashboard_security_summary() -> str:
        return "dashboard:security_summary"

    @staticmethod
    def stats_device_count() -> str:
        return "stats:devices:count"

    @staticmethod
    def stats_event_count() -> str:
        return "stats:events:count"

    @staticmethod
    def list(resource: str, param_hash: str) -> str:
        return f"list:{resource}:{param_hash}"
