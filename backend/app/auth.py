import os
from fastapi import Header, HTTPException
from jwt import PyJWKClient
import jwt
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY")

JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"

# Busca e mantém em cache as chaves públicas do Supabase.
# O header 'apikey' é obrigatório — sem ele, o gateway do Supabase
# bloqueia a requisição com 401, mesmo sendo um endpoint público de chaves.
jwks_client = PyJWKClient(
    JWKS_URL,
    headers={"apikey": SUPABASE_PUBLISHABLE_KEY},
)


def get_current_user_id(authorization: str = Header(...)) -> str:
    """
    Lê o header 'Authorization: Bearer <token>', valida a assinatura
    usando a chave pública do Supabase (ES256), e retorna o ID do usuário (sub).
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou mal formatado")

    token = authorization.replace("Bearer ", "")

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")

    return payload["sub"]