import time

import httpx

from ..config import settings
from ..errors import AppError
from ..money import to_value

_cache = {"token": None, "exp": 0.0}


def _ensure():
    if not settings.paypal_client_id or not settings.paypal_client_secret:
        raise AppError("PAYPAL_NOT_CONFIGURED", "PayPal Sandbox credentials are not configured", 503)


def _token():
    _ensure()
    if _cache["token"] and _cache["exp"] > time.time() + 30:
        return _cache["token"]
    try:
        r = httpx.post(
            settings.paypal_base_url + "/v1/oauth2/token",
            auth=(settings.paypal_client_id, settings.paypal_client_secret),
            data={"grant_type": "client_credentials"},
            timeout=20,
        )
        r.raise_for_status()
    except httpx.HTTPError:
        raise AppError("PROVIDER_ERROR", "Payment provider unavailable", 502)
    d = r.json()
    _cache["token"] = d["access_token"]
    _cache["exp"] = time.time() + d["expires_in"]
    return _cache["token"]


def _call(method, path, **kw):
    headers = {"Authorization": f"Bearer {_token()}", **kw.pop("headers", {})}
    try:
        return httpx.request(method, settings.paypal_base_url + path, headers=headers, timeout=25, **kw)
    except httpx.HTTPError:
        raise AppError("PROVIDER_ERROR", "Payment provider unavailable", 502)


def create_order(local_id, amount, currency, trip_name):
    unit = {
        "reference_id": local_id,
        "custom_id": local_id,
        "description": f"TripBank {trip_name}"[:120],
        "amount": {"currency_code": currency, "value": to_value(amount)},
    }
    if settings.paypal_merchant_id:
        unit["payee"] = {"merchant_id": settings.paypal_merchant_id}
    r = _call(
        "POST",
        "/v2/checkout/orders",
        json={"intent": "CAPTURE", "purchase_units": [unit]},
        headers={"PayPal-Request-Id": f"order-{local_id}"},
    )
    if r.status_code not in (200, 201):
        raise AppError("PROVIDER_ERROR", "Could not create the payment order", 502)
    return r.json()["id"]


def capture(provider_order_id):
    r = _call(
        "POST",
        f"/v2/checkout/orders/{provider_order_id}/capture",
        headers={"PayPal-Request-Id": f"capture-{provider_order_id}", "Content-Type": "application/json"},
    )
    if r.status_code in (200, 201):
        return r.json()
    issue = ""
    try:
        issue = r.json()["details"][0]["issue"]
    except Exception:
        pass
    if issue == "ORDER_ALREADY_CAPTURED":
        raise AppError("ORDER_ALREADY_CAPTURED", "Order already captured", 409)
    if issue in ("ORDER_NOT_APPROVED", "PAYER_ACTION_REQUIRED"):
        raise AppError("ORDER_NOT_APPROVED", "The buyer has not approved this order", 409)
    raise AppError("PROVIDER_ERROR", "Capture failed", 502)


def get_order(provider_order_id):
    r = _call("GET", f"/v2/checkout/orders/{provider_order_id}")
    if r.status_code != 200:
        raise AppError("PROVIDER_ERROR", "Could not read the payment order", 502)
    return r.json()


def verify_webhook(headers, event):
    if not settings.paypal_webhook_id:
        raise AppError("WEBHOOK_NOT_CONFIGURED", "Webhook id is not configured", 503)
    body = {
        "auth_algo": headers.get("paypal-auth-algo"),
        "cert_url": headers.get("paypal-cert-url"),
        "transmission_id": headers.get("paypal-transmission-id"),
        "transmission_sig": headers.get("paypal-transmission-sig"),
        "transmission_time": headers.get("paypal-transmission-time"),
        "webhook_id": settings.paypal_webhook_id,
        "webhook_event": event,
    }
    r = _call("POST", "/v1/notifications/verify-webhook-signature", json=body)
    return r.status_code == 200 and r.json().get("verification_status") == "SUCCESS"
