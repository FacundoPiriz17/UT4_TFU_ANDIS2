from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.aspects.audit import auditar
from app.database import get_db
from app.models import Login, Persona
from app.schemas import PersonaCreate, PersonaUpdate
from security.dependencies import obtener_usuario_actual
from security.password import hashear_contrasena

router = APIRouter(
    prefix="/personas",
    tags=["Personas"],
    dependencies=[Depends(obtener_usuario_actual)],
)


@router.post("", status_code=status.HTTP_201_CREATED)
@auditar("INSERTAR_PERSONA")
def crear_persona(
    datos: PersonaCreate,
    db: Session = Depends(get_db),
):
    if db.get(Persona, datos.email) is not None:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una persona con ese email",
        )

    persona = Persona(
        EmailPersona=datos.email,
        NombrePersona=datos.nombre,
        ApellidoPersona=datos.apellido,
    )

    credenciales = Login(
        EmailPersona=datos.email,
        ContrasenaLogin=hashear_contrasena(
            datos.contrasena
        ),
    )

    try:
        db.add(persona)
        db.flush()
        db.add(credenciales)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo crear la persona",
        )

    return {
        "email": persona.EmailPersona,
        "nombre": persona.NombrePersona,
        "apellido": persona.ApellidoPersona,
    }


@router.put("/{email}")
@auditar("ACTUALIZAR_PERSONA")
def actualizar_persona(
    email: str,
    datos: PersonaUpdate,
    db: Session = Depends(get_db),
):
    persona = db.get(Persona, email)

    if persona is None:
        raise HTTPException(
            status_code=404,
            detail="Persona no encontrada",
        )

    persona.NombrePersona = datos.nombre
    persona.ApellidoPersona = datos.apellido

    db.commit()
    db.refresh(persona)

    return {
        "email": persona.EmailPersona,
        "nombre": persona.NombrePersona,
        "apellido": persona.ApellidoPersona,
    }


@router.delete("/{email}", status_code=status.HTTP_204_NO_CONTENT)
@auditar("ELIMINAR_PERSONA")
def eliminar_persona(
    email: str,
    db: Session = Depends(get_db),
):
    persona = db.get(Persona, email)

    if persona is None:
        raise HTTPException(
            status_code=404,
            detail="Persona no encontrada",
        )

    try:
        db.delete(persona)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="La persona tiene compras asociadas y no puede eliminarse",
        )

    return None
