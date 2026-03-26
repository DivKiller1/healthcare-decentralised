from fastapi import Request, HTTPException
import jwt

SECRET = "supersecretkey"
ALGORITHM = "HS256"

def verify_token(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        scheme, token = auth_header.split()

        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        decoded = jwt.decode(token, SECRET, algorithms=[ALGORITHM])

        request.state.user = decoded
        return decoded

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")