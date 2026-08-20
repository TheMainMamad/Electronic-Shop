import structlog

logger = structlog.get_logger()


def send_password_reset_email(*, to_email: str, token: str) -> None:
    """Deliver the reset link. No SMTP provider is configured for this project,
    so delivery is logged instead of sent — swap this body for a real provider
    call (e.g. an SMTP/API client reading its credentials from env) without
    touching callers.
    """
    logger.info("password_reset_email_dispatched", to_email=to_email, token=token)


def send_email_verification_email(*, to_email: str, token: str) -> None:
    logger.info("email_verification_dispatched", to_email=to_email, token=token)
