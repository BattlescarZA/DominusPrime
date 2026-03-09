# -*- coding: utf-8 -*-
"""WhatsApp channel router."""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


def _get_whatsapp_channel(request: Request):
    """Retrieve the WhatsAppChannel from app state, or None."""
    app = getattr(request, "app", None)
    if not app:
        return None
    cm = getattr(app.state, "channel_manager", None)
    if not cm:
        return None
    for ch in cm.channels:
        if ch.channel == "whatsapp":
            return ch
    return None


@router.get(
    "/qr",
    summary="Get WhatsApp QR code",
    description="Retrieve the current WhatsApp QR code for authentication",
)
async def get_qr_code(request: Request) -> JSONResponse:
    """Get WhatsApp QR code for authentication.
    
    Returns:
        JSON response with:
        - qr_code: The QR code string (if available)
        - authenticated: Whether WhatsApp is authenticated
        - status: Connection status message
    """
    whatsapp_ch = _get_whatsapp_channel(request)
    if not whatsapp_ch:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp channel is not available or not enabled"
        )
    
    # Check if channel has QR code attribute
    qr_code = getattr(whatsapp_ch, "_qr_code", None)
    authenticated = getattr(whatsapp_ch, "_authenticated", False)
    
    return JSONResponse({
        "qr_code": qr_code,
        "authenticated": authenticated,
        "status": "authenticated" if authenticated else ("waiting_for_qr" if not qr_code else "ready_to_scan")
    })


@router.get(
    "/status",
    summary="Get WhatsApp connection status",
    description="Check WhatsApp connection and authentication status",
)
async def get_status(request: Request) -> JSONResponse:
    """Get WhatsApp connection status.
    
    Returns:
        JSON response with connection status information
    """
    whatsapp_ch = _get_whatsapp_channel(request)
    if not whatsapp_ch:
        return JSONResponse({
            "enabled": False,
            "connected": False,
            "authenticated": False,
            "status": "not_enabled"
        })
    
    authenticated = getattr(whatsapp_ch, "_authenticated", False)
    connected = getattr(whatsapp_ch, "_client", None) is not None
    
    return JSONResponse({
        "enabled": True,
        "connected": connected,
        "authenticated": authenticated,
        "status": "connected" if authenticated else ("connecting" if connected else "disconnected")
    })
