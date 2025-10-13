import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from .config import settings

api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Security(api_key_scheme)):  # noqa: B008
    """
    FastAPI dependency for API key authentication.

    Note: Security() call in default argument is the correct FastAPI pattern.
    """
    if key is None or not secrets.compare_digest(key, settings.APP_AUTH_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
        )
    return "api-client"


async def verify_firebase_token(token: str) -> str | None:
    """
    Verify Firebase authentication token.

    TODO: Implement Firebase Admin SDK integration

    Args:
        token: Firebase ID token

    Returns:
        Firebase UID if valid, None otherwise
    """
    # TODO: Implement Firebase verification
    # from firebase_admin import auth
    # try:
    #     decoded_token = auth.verify_id_token(token)
    #     return decoded_token['uid']
    # except Exception:
    #     return None

    # Temporary: For development/testing without Firebase
    # This should be removed in production
    return "None"
