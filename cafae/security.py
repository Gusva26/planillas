import hashlib
import re
import secrets

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError


class UserError(Exception):
    """Error esperado cuyo texto puede mostrarse al usuario."""


class AccessError(UserError):
    pass


class SessionError(AccessError):
    pass


HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, type=Type.ID)
# Mantiene el coste de verificación para cuentas inexistentes; no es una credencial.
DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(32))
ROLES = ('ADMINISTRADOR', 'PLANILLAS', 'CONSULTA')
PERMISSIONS = {
    'consultar': frozenset(ROLES),
    'editar_planillas': frozenset(ROLES[:2]),
    'generar_documentos': frozenset(ROLES[:2]),
    'txt_bancario': frozenset(ROLES[:2]),
    'cerrar_planilla': frozenset(ROLES[:1]),
    'reabrir_planilla': frozenset(ROLES[:1]),
    'trabajadores': frozenset(ROLES[:2]),
    'catalogos': frozenset(ROLES[:1]),
    'usuarios': frozenset(ROLES[:1]),
    'auditoria': frozenset(ROLES[:1]),
}


def normalize_username(value):
    result = value.strip().lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{2,79}', result):
        raise UserError('Usa de 3 a 80 letras sin tildes, números, punto, guion o guion bajo para el usuario.')
    return result


def validate_name(value):
    value = value.strip()
    if not 2 <= len(value) <= 200 or any(ord(c) < 32 for c in value):
        raise UserError('Escribe un nombre completo de 2 a 200 caracteres.')
    return value


def hash_password(value):
    if not isinstance(value, str) or not 12 <= len(value) <= 128 or not value.strip():
        raise UserError('La contraseña debe tener entre 12 y 128 caracteres. Puedes usar una frase larga.')
    return HASHER.hash(value)


def verify_password(encoded, value):
    if not isinstance(value, str) or len(value) > 128:
        return False
    try:
        return HASHER.verify(encoded, value)
    except (VerificationError, InvalidHashError):
        return False


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()
