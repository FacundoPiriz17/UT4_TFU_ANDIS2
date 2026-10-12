from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.aspects.audit import auditar
from app.database import get_db
from app.models import Genero, Juego, JuegoTieneGenero
from app.schemas import JuegoCreate, JuegoUpdate
from security.dependencies import obtener_usuario_actual

router = APIRouter(
    prefix="/juegos",
    tags=["Juegos"],
    dependencies=[Depends(obtener_usuario_actual)],
)


def _asignar_generos(
    db: Session,
    id_juego: int,
    generos: list[str],
) -> None:
    for nombre in generos:
        nombre = nombre.strip()

        if not nombre:
            continue

        genero = db.get(Genero, nombre)

        if genero is None:
            genero = Genero(
                NombreGenero=nombre,
                DescripcionGenero=None,
            )
            db.add(genero)
            db.flush()

        relacion = db.get(
            JuegoTieneGenero,
            {
                "IdJuego": id_juego,
                "NombreGenero": nombre,
            },
        )

        if relacion is None:
            db.add(
                JuegoTieneGenero(
                    IdJuego=id_juego,
                    NombreGenero=nombre,
                )
            )


@router.post("", status_code=status.HTTP_201_CREATED)
@auditar("INSERTAR_JUEGO")
def crear_juego(
    datos: JuegoCreate,
    db: Session = Depends(get_db),
):
    juego = Juego(NombreJuego=datos.nombre)
    db.add(juego)
    db.flush()

    _asignar_generos(db, juego.IdJuego, datos.generos)

    db.commit()
    db.refresh(juego)

    return {
        "id_juego": juego.IdJuego,
        "nombre": juego.NombreJuego,
        "generos": datos.generos,
    }


@router.put("/{id_juego}")
@auditar("ACTUALIZAR_JUEGO")
def actualizar_juego(
    id_juego: int,
    datos: JuegoUpdate,
    db: Session = Depends(get_db),
):
    juego = db.get(Juego, id_juego)

    if juego is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado",
        )

    juego.NombreJuego = datos.nombre

    if datos.generos is not None:
        (
            db.query(JuegoTieneGenero)
            .filter(JuegoTieneGenero.IdJuego == id_juego)
            .delete()
        )
        _asignar_generos(
            db,
            id_juego,
            datos.generos,
        )

    db.commit()
    db.refresh(juego)

    return {
        "id_juego": juego.IdJuego,
        "nombre": juego.NombreJuego,
    }


@router.delete("/{id_juego}", status_code=status.HTTP_204_NO_CONTENT)
@auditar("ELIMINAR_JUEGO")
def eliminar_juego(
    id_juego: int,
    db: Session = Depends(get_db),
):
    juego = db.get(Juego, id_juego)

    if juego is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado",
        )

    try:
        db.delete(juego)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="El juego tiene relaciones asociadas y no puede eliminarse",
        )

    return None
