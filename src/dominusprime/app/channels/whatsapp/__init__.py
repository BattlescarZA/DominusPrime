# -*- coding: utf-8 -*-
"""WhatsApp channel: QR code authentication (like WhatsApp Web)."""

from .channel import WhatsAppChannel
from .baileys_adapter import WhatsAppBaileysAdapter

__all__ = ["WhatsAppChannel", "WhatsAppBaileysAdapter"]
