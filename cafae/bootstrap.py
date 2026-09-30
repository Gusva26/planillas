"""Ejecutar localmente: docker compose run --rm app python -m cafae.bootstrap"""
from getpass import getpass
import sys

from cafae.auth import AuthService
from cafae.security import UserError


def main():
    if not sys.stdin.isatty():
        raise UserError('Ejecuta este comando en una terminal interactiva para ingresar la contraseña de forma oculta.')
    print('Crear el primer administrador · CAFAE UGEL Chepén')
    username = input('Usuario: ')
    name = input('Nombre completo: ')
    password = getpass('Contraseña (12–128 caracteres, ingreso oculto): ')
    if password != getpass('Repite la contraseña: '):
        raise UserError('Las contraseñas no coinciden.')
    AuthService().bootstrap(username, name, password)
    print('Administrador creado. Ya puedes iniciar sesión en http://localhost:8501.')


if __name__ == '__main__':
    try:
        main()
    except (UserError, KeyboardInterrupt, EOFError) as exc:
        print(str(exc) or 'Operación cancelada.', file=sys.stderr)
        sys.exit(1)
