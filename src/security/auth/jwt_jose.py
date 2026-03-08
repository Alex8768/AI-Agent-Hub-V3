from jose import jwt
from jose.exceptions import JWTError as JoseJWTError
from typing import Optional, Dict, Any
import time

ALGORITHM = "HS256"

class JWTError(Exception):
    pass

def create_token(
    payload: Dict[str, Any],
    secret: str,
    *,
    ttl_seconds: int = 3600,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
) -> str:
    to_encode = payload.copy()
    now = int(time.time())
    to_encode.update({"iat": now, "nbf": now, "exp": now + ttl_seconds})
    if issuer:
        to_encode["iss"] = issuer
    if audience:
        to_encode["aud"] = audience
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)

def verify_token(
    token: str,
    secret: str,
    *,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    leeway_seconds: int = 30,
) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],
            issuer=issuer,
            audience=audience,
            leeway=leeway_seconds,
            options={"verify_aud": audience is not None},
        )
        return payload
    except JoseJWTError as e:
        raise JWTError(str(e))
