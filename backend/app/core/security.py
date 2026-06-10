import ssl
import certifi
import jwt
from jwt import PyJWKClient

from app.core.config import SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY

# Allows the usage of access token using JWT.

_ssl_context = ssl.create_default_context(cafile=certifi.where())
_jwk_client = PyJWKClient(
    f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json",
    ssl_context=_ssl_context,
    headers={"apikey": SUPABASE_PUBLISHABLE_KEY},
)


def decode_access_token(token: str) -> dict:
    signing_key = _jwk_client.get_signing_key_from_jwt(token)
    return jwt.decode(token, signing_key.key, algorithms=["ES256", "RS256"], audience="authenticated")
