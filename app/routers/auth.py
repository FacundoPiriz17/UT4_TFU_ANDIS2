from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.aspects.audit import auditar
from app.database import get_db
from app.models import Login
from app.schemas import LoginRequest
from security.jwt import crear_token
from security.password import verificar_contrasena

router = APIRouter(prefix="/auth", tags=["Autenticacion"])


@router.post("/login")
@auditar("LOGIN")
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    credenciales = db.get(Login, datos.email)

    if credenciales is None or not verificar_contrasena(
        datos.contrasena,
        credenciales.ContrasenaLogin,
    ):
        raise HTTPException(
            status_code=401,
            detail="Credenciales invalidas",
        )

    return {
        "access_token": crear_token(datos.email),
        "token_type": "bearer",
    }
