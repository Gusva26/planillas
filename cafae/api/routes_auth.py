"""Rutas de autenticación y gestión de usuarios."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from cafae.api.deps import auth_service, get_current_user, require_role
from cafae.security import AccessError, SessionError, UserError

router = APIRouter(prefix='/auth', tags=['Autenticación'])


class LoginRequest(BaseModel):
    username: str = Field(..., max_length=80)
    password: str = Field(..., max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    repeat_password: str


class CreateUserRequest(BaseModel):
    username: str = Field(..., max_length=80)
    nombre_completo: str = Field(..., max_length=200)
    rol: str
    password_temporal: str = Field(..., min_length=12, max_length=128)


class UpdateUserRequest(BaseModel):
    nombre_completo: str = Field(..., max_length=200)
    rol: str
    activo: bool
    revision: int


class ResetPasswordRequest(BaseModel):
    password_temporal: str = Field(..., min_length=12, max_length=128)
    revision: int


@router.post('/login')
def login(req: LoginRequest):
    try:
        token = auth_service.login(req.username, req.password, origin='spa-client')
        user = auth_service.current_user(token)
        return {
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['usuario'],
                'nombre': user['nombre_completo'],
                'rol': user['rol'],
                'debe_cambiar_password': user['debe_cambiar_password'],
            }
        }
    except AccessError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except (UserError, SessionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post('/logout')
def logout(user: Annotated[dict, Depends(get_current_user)]):
    auth_service.logout(user['token'])
    return {'ok': True, 'mensaje': 'Sesión cerrada correctamente.'}


@router.get('/me')
def get_me(user: Annotated[dict, Depends(get_current_user)]):
    return {
        'id': user['id'],
        'username': user['username'],
        'nombre': user['nombre'],
        'rol': user['rol'],
        'debe_cambiar_password': user['debe_cambiar_password'],
    }


@router.post('/change-password')
def change_password(
    req: ChangePasswordRequest,
    user: Annotated[dict, Depends(get_current_user)]
):
    if req.new_password != req.repeat_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Las contraseñas nuevas no coinciden.',
        )
    try:
        auth_service.change_password(user['token'], req.current_password, req.new_password)
        return {'ok': True, 'mensaje': 'Contraseña actualizada con éxito.'}
    except (UserError, SessionError, AccessError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# Gestión de usuarios (Solo ADMINISTRADOR)
users_router = APIRouter(prefix='/users', tags=['Usuarios'])


@users_router.get('')
def list_users(user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]):
    try:
        users = auth_service.list_users(user['token'])
        return [
            {
                'id': u['id'],
                'usuario': u['usuario'],
                'nombre_completo': u['nombre_completo'],
                'rol': u['rol'],
                'activo': u['activo'],
                'debe_cambiar_password': u['debe_cambiar_password'],
                'revision': u['revision'],
            }
            for u in users
        ]
    except (UserError, SessionError, AccessError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@users_router.post('')
def create_user(
    req: CreateUserRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    try:
        new_id = auth_service.create_user(
            user['token'], req.username, req.nombre_completo, req.rol, req.password_temporal
        )
        return {'ok': True, 'id': new_id, 'mensaje': 'Usuario creado exitosamente.'}
    except (UserError, SessionError, AccessError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@users_router.put('/{user_id}')
def update_user(
    user_id: int,
    req: UpdateUserRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    try:
        auth_service.update_user(
            user['token'], user_id, req.revision, req.nombre_completo, req.rol, req.activo
        )
        return {'ok': True, 'mensaje': 'Cuenta actualizada exitosamente.'}
    except (UserError, SessionError, AccessError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@users_router.post('/{user_id}/reset-password')
def reset_password(
    user_id: int,
    req: ResetPasswordRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    try:
        auth_service.reset_password(
            user['token'], user_id, req.revision, req.password_temporal
        )
        return {'ok': True, 'mensaje': 'Contraseña restablecida exitosamente.'}
    except (UserError, SessionError, AccessError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
