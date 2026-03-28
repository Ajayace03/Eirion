from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import jwt
import httpx

security = HTTPBearer()

# Cache for Clerk's JWKS (JSON Web Key Set)
_CLERK_JWKS = None

async def get_clerk_jwks():
    global _CLERK_JWKS
    if _CLERK_JWKS is None:
        clerk_frontend_api = os.getenv("CLERK_FRONTEND_API_URL")
        if not clerk_frontend_api:
            return None
            
        jwks_url = f"{clerk_frontend_api}/.well-known/jwks.json"
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(jwks_url)
                res.raise_for_status()
                _CLERK_JWKS = res.json()
        except Exception as e:
            print(f"[Auth] Failed to fetch Clerk JWKS: {e}")
            return None
    return _CLERK_JWKS

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the Clerk JWT token from the Authorization header via JWKS.
    Falls back to a stub user if CLERK_SECRET_KEY is omitted for local dev.
    """
    token = credentials.credentials

    # Strict mode using Clerk
    if os.getenv("CLERK_SECRET_KEY") and os.getenv("CLERK_FRONTEND_API_URL"):
        try:
            jwks = await get_clerk_jwks()
            if not jwks:
                raise HTTPException(status_code=500, detail="Auth configuration error")
                
            public_keys = {}
            for jwk in jwks["keys"]:
                kid = jwk["kid"]
                public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
                
            kid = jwt.get_unverified_header(token).get("kid")
            key = public_keys.get(kid)
            
            if not key:
                raise HTTPException(status_code=401, detail="Signing key not found")
                
            decoded = jwt.decode(
                token, 
                key, 
                algorithms=["RS256"],
                options={"verify_aud": False} # Validate 'aud' depending on your Clerk config
            )
            return {"user_id": decoded.get("sub")}
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # Local development fallback
    return {"user_id": "test_hackathon_user"}
