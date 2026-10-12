from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from security.jwt import verificar_token

bearer = HTTPBearer(auto_error=False)


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    if credenciales is None:
        raise HTTPException(
            status_code=401,
            detail="Token requerido",
        )

    payload = verificar_token(
        credenciales.credentials
    )

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Token invalido o expirado",
        )

    email = payload.get("sub")

    if not email:
        raise HTTPException(
            status_code=401,
            detail="Token sin sujeto",
        )

    return email
