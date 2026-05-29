"""
Placeholder for future WebSocket / SSE real-time dashboard updates.

Current dashboard uses REST polling (GET /dashboard/*). When adding WebSockets:
  - broadcast new Alert rows and audit_log inserts to subscribed clients
  - authenticate via JWT on connection handshake
  - scope channels by role (admin/analyst only)

This module documents the intended extension point without adding dependencies.
"""

# Example future shape (not implemented):
#
# class DashboardRealtimeHub:
#     async def connect(self, websocket, user: User): ...
#     async def broadcast_alert(self, alert: Alert): ...
