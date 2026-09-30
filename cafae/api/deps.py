"""Dependencias de autenticación y autorización para la API REST."""
from typing import Annotated, Optional
from fastapi import Depends, Header, HTTPException, status
from cafae.auth import AuthService

from cafae.security import AccessError, SessionError, UserError

auth_service = AuthService()


def get_token(
    authorization: Annotated[Optional[str], Header()] = None,
    x_session_token: Annotated[Optional[str], Header()] = None,
) -> str:
    token = None
    if authorization and authorization.startswith('Bearer '):
        token = authorization.split(' ', 1)[1].strip()
    elif x_session_token:
        token = x_session_token.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='No se proporcionó un token de sesión válido.',
        )
    return token


def get_current_user(
    token: Annotated[Optional[str], Header(alias='X-Session-Token')] = None,
    authorization: Annotated[Optional[str], Header()] = None,
    query_token: Optional[str] = None,
) -> dict:
    actual_token = None
    if authorization and authorization.startswith('Bearer '):
        actual_token = authorization.split(' ', 1)[1].strip()
    elif token:
        actual_token = token.strip()
    elif authorization:
        actual_token = authorization.strip()
    elif query_token:
        actual_token = query_token.strip()

    if not actual_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Sesión no autenticada.',
        )

    try:
        user = auth_service.current_user(actual_token)
        return {
            'id': user['id'],
            'user_id': user['id'],
            'username': user['usuario'],
            'nombre': user['nombre_completo'],
            'rol': user['rol'],
            'debe_cambiar_password': user['debe_cambiar_password'],
            'token': actual_token,
        }
    except SessionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except AccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token inválido o expirado.')


def require_role(*allowed_roles: str):
    def role_checker(user: Annotated[dict, Depends(get_current_user)]):
        if user.get('rol') not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Acceso denegado: se requiere uno de los roles {allowed_roles}.',
            )
        return user
    return role_checker
