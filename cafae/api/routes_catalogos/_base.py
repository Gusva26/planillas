"""Modelos de entrada y servicio compartido de los routers de catálogos."""
from typing import Optional

from pydantic import BaseModel, Field

from cafae.catalogos import CatalogoService

catalogo_service = CatalogoService()


class InstitucionRequest(BaseModel):
    nombre: str = Field(..., max_length=240)
    codigo_modular: Optional[str] = Field(None, max_length=30)
    nivel_id: Optional[int] = None
    distrito: Optional[str] = Field(None, max_length=120)
    meta_id: Optional[int] = None
    observaciones: Optional[str] = None


class AreaRequest(BaseModel):
    nombre: str = Field(..., max_length=150)
    meta_id: Optional[int] = None


class MetaRequest(BaseModel):
    codigo: str = Field(..., max_length=30)
    descripcion: Optional[str] = Field(None, max_length=500)
    programa_id: Optional[int] = None
    partida_id: Optional[int] = None


class NivelRequest(BaseModel):
    nombre: str = Field(..., max_length=100)


class ProgramaRequest(BaseModel):
    codigo: str = Field(..., max_length=30)
    nombre: str = Field(..., max_length=180)
    orden: Optional[int] = 0
    padre_id: Optional[int] = None


class PartidaRequest(BaseModel):
    codigo: str = Field(..., max_length=40)
    descripcion: str = Field(..., max_length=500)


class CargoRequest(BaseModel):
    nombre: str = Field(..., max_length=150)


class CategoriaRequest(BaseModel):
    codigo: str = Field(..., max_length=50)
    descripcion: str = Field(..., max_length=150)


class SituacionRequest(BaseModel):
    nombre: str = Field(..., max_length=120)


class SubtipoRequest(BaseModel):
    nombre: str = Field(..., max_length=120)


class ConfiguracionRequest(BaseModel):
    nombre_institucion: str = Field(..., max_length=200)
    nombre_sistema: str = Field(..., max_length=200)
    zona_horaria: Optional[str] = 'America/Lima'


class FirmaRequest(BaseModel):
    nombre_completo: Optional[str] = Field(None, max_length=200)
    cargo: Optional[str] = Field(None, max_length=200)
    nombre_firmante: Optional[str] = Field(None, max_length=200)
    cargo_firmante: Optional[str] = Field(None, max_length=200)
    orden: Optional[int] = None
    ambito: Optional[str] = None


class TipoDescuentoRequest(BaseModel):
    codigo: Optional[str] = Field(None, max_length=30)
    nombre: str = Field(..., max_length=100)
    orden: Optional[int] = 1
    aplica_iiee: Optional[bool] = True
    aplica_sede: Optional[bool] = True
    activo: Optional[bool] = True


class ToggleEstadoRequest(BaseModel):
    activo: Optional[bool] = None

