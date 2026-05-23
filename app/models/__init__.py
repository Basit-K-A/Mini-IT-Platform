# Import all models so Base.metadata.create_all() sees every table.
from models.device import Device
from models.event import Event
from models.user import User

__all__ = ["User", "Device", "Event"]
