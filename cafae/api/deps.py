"""Dependencias de autenticación y autorización para la API REST.

Esquema único de credenciales: ``Authorization: Bearer <token>``.
El token no se acepta por query string ni por cabeceras alternativas: así no
termina en logs, historial del navegador, proxies ni referrers.
"""
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status

from cafae.auth import AuthService
from cafae.security import PERMISSIONS, AccessError, SessionError

auth_service = AuthService()
AUTH_SCHEME = 'Bearer '
MISSING_SCHEME = 'Se requiere el encabezado Authorization: Bearer <token>.'
INVALID_SESSION = 'Token inválido o expirado.'


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={'WWW-Authenticate': 'Bearer'},
    )


def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
) -> dict:
    """Valida la sesión a partir del encabezado Bearer y devuelve el usuario."""
    if not authorization or not authorization.startswith(AUTH_SCHEME):
        raise _unauthorized(MISSING_SCHEME)
    token = authorization[len(AUTH_SCHEME):].strip()
    if not token:
        raise _unauthorized(MISSING_SCHEME)

    try:
        user = auth_service.current_user(token)
    except SessionError as exc:
        raise _unauthorized(str(exc))
    except AccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    return {
        'id': user['id'],
        'user_id': user['id'],
        'username': user['usuario'],
        'nombre': user['nombre_completo'],
        'rol': user['rol'],
        'debe_cambiar_password': user['debe_cambiar_password'],
        'token': token,
    }


def require_role(*allowed_roles: str):
    def role_checker(user: Annotated[dict, Depends(get_current_user)]):
        if user.get('rol') not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Acceso denegado: se requiere uno de los roles {allowed_roles}.',
            )
        return user
    return role_checker


def require_permission(permission: str):
    """Exige un permiso declarado en ``security.PERMISSIONS``.

    Es la primera barrera; el servicio vuelve a validarlo en la transacción
    (`data_transaction`) y la base aplica el rol SQL correspondiente.
    """
    allowed = PERMISSIONS.get(permission, frozenset())

    def permission_checker(user: Annotated[dict, Depends(get_current_user)]):
        if user.get('rol') not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Tu rol no permite realizar esta operación.',
            )
        return user

    # Metadato para verificaciones y tests: el permiso queda declarado en la ruta.
    permission_checker.permiso_requerido = permission
    return permission_checker
