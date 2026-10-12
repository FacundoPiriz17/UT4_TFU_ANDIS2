from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    contrasena: str


class PersonaCreate(BaseModel):
    email: str
    nombre: str = Field(min_length=1, max_length=30)
    apellido: str = Field(min_length=1, max_length=30)
    contrasena: str = Field(min_length=6, max_length=72)


class PersonaUpdate(BaseModel):
    nombre: str = Field(min_length=1, max_length=30)
    apellido: str = Field(min_length=1, max_length=30)


class JuegoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    generos: list[str] = []


class JuegoUpdate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    generos: list[str] | None = None


class CompraCreate(BaseModel):
    email_persona: str
    id_juego: int
    costo_base: int = Field(gt=0)
    politica: Literal["normal", "invierno"] = "normal"


class CompraUpdate(BaseModel):
    costo_base: int = Field(gt=0)
    politica: Literal["normal", "invierno"] = "normal"
