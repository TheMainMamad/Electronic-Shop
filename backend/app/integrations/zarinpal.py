from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.core.config import get_settings

settings = get_settings()

_SANDBOX_BASE = "https://sandbox.zarinpal.com"
_PRODUCTION_BASE = "https://payment.zarinpal.com"


class ZarinPalNotConfigured(Exception):
    pass


class ZarinPalError(Exception):
    pass


@dataclass(frozen=True)
class PaymentRequestResult:
    authority: str
    payment_url: str


@dataclass(frozen=True)
class PaymentVerifyResult:
    success: bool
    reference_id: str | None
    raw_response: dict[str, Any]


class ZarinPalClient(Protocol):
    def is_configured(self) -> bool: ...

    async def request_payment(
        self, *, amount_rial: int, description: str, callback_url: str
    ) -> PaymentRequestResult: ...

    async def verify_payment(
        self, *, amount_rial: int, authority: str
    ) -> PaymentVerifyResult: ...


class ZarinPalSandboxClient:
    """ZarinPal sandbox integration. Amounts are always passed in Rial
    (ZarinPal's unit); this project's own money columns are Toman, so
    callers convert (1 Toman = 10 Rial) before calling this client."""

    def __init__(self) -> None:
        self._base = _SANDBOX_BASE if settings.zarinpal_sandbox else _PRODUCTION_BASE

    def is_configured(self) -> bool:
        return bool(settings.zarinpal_merchant_id and settings.zarinpal_callback_url)

    async def request_payment(
        self, *, amount_rial: int, description: str, callback_url: str
    ) -> PaymentRequestResult:
        if not self.is_configured():
            raise ZarinPalNotConfigured("درگاه پرداخت در حال حاضر پیکربندی نشده است.")

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self._base}/pg/v4/payment/request.json",
                json={
                    "merchant_id": settings.zarinpal_merchant_id,
                    "amount": amount_rial,
                    "description": description,
                    "callback_url": callback_url,
                },
            )
        payload = response.json()
        data = payload.get("data") or {}
        if response.status_code != 200 or data.get("code") != 100:
            raise ZarinPalError("ایجاد تراکنش پرداخت ناموفق بود.")

        authority = data["authority"]
        return PaymentRequestResult(
            authority=authority,
            payment_url=f"{self._base}/pg/StartPay/{authority}",
        )

    async def verify_payment(self, *, amount_rial: int, authority: str) -> PaymentVerifyResult:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self._base}/pg/v4/payment/verify.json",
                json={
                    "merchant_id": settings.zarinpal_merchant_id,
                    "amount": amount_rial,
                    "authority": authority,
                },
            )
        payload = response.json()
        data = payload.get("data") or {}
        code = data.get("code")
        # 100 = freshly verified, 101 = already verified (still a success on replay).
        success = code in (100, 101)
        reference_id = str(data["ref_id"]) if success and data.get("ref_id") else None
        return PaymentVerifyResult(success=success, reference_id=reference_id, raw_response=payload)


_client: ZarinPalClient | None = None


def get_zarinpal_client() -> ZarinPalClient:
    global _client
    if _client is None:
        _client = ZarinPalSandboxClient()
    return _client


def set_zarinpal_client(client: ZarinPalClient) -> None:
    """Test-only seam: substitute a fake client instead of hitting the network."""
    global _client
    _client = client
