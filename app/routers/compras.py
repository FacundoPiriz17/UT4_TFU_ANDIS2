from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.aspects.audit import auditar
from app.database import get_db
from app.schemas import CompraCreate, CompraUpdate
from app.services.compras import (
    crear_compra,
    eliminar_compra,
    recalcular_compra,
    _buscar_compras,
)
from security.dependencies import obtener_usuario_actual

router = APIRouter(
    prefix="/compras",
    tags=["Compras"],
    dependencies=[Depends(obtener_usuario_actual)],
)


def _respuesta(compra, politica: str | None = None):
    return {
        "email_persona": compra.EmailPersona,
        "id_juego": compra.IdJuego,
        "fecha_hora": compra.FechaHoraCompra,
        "costo_compra": compra.CostoCompra,
        "politica": politica,
    }


@router.get("/{email_persona}")
def listar_compras(
    email_persona: str,
    db: Session = Depends(get_db),
):

    compras = _buscar_compras(db, email_persona)

    return [
        _respuesta(compra)
        for compra in compras
    ]
    
    
@router.post("", status_code=status.HTTP_201_CREATED)
@auditar("GENERAR_COMPRA")
def generar_compra(
    datos: CompraCreate,
    db: Session = Depends(get_db),
):
    compra = crear_compra(
        db=db,
        email_persona=datos.email_persona,
        id_juego=datos.id_juego,
        costo_base=datos.costo_base,
        politica=datos.politica,
    )

    return _respuesta(compra, datos.politica)


@router.put("/{email_persona}/{id_juego}")
@auditar("ACTUALIZAR_COMPRA")
def actualizar_compra(
    email_persona: str,
    id_juego: int,
    datos: CompraUpdate,
    db: Session = Depends(get_db),
):
    compra = recalcular_compra(
        db=db,
        email_persona=email_persona,
        id_juego=id_juego,
        costo_base=datos.costo_base,
        politica=datos.politica,
    )

    return _respuesta(compra, datos.politica)


@router.delete(
    "/{email_persona}/{id_juego}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@auditar("ELIMINAR_COMPRA")
def borrar_compra(
    email_persona: str,
    id_juego: int,
    db: Session = Depends(get_db),
):
    eliminar_compra(
        db=db,
        email_persona=email_persona,
        id_juego=id_juego,
    )

    return None
