"""Provisiona el rol de servicio local; no crea usuarios de negocio ni imprime secretos."""
import re
import secrets

from migrate import ROOT, migrate, psql


def main():
    path = ROOT / '.env'
    if not path.exists():
        raise SystemExit('Ejecuta scripts/db.ps1 init y scripts/db.ps1 up primero.')
    content = path.read_text(encoding='utf-8')
    match = re.search(r'^CAFAE_DB_PASSWORD=([0-9a-f]{64})\s*$', content, re.MULTILINE)
    if match:
        password = match.group(1)
    elif re.search(r'^CAFAE_DB_PASSWORD=', content, re.MULTILINE):
        raise SystemExit('La configuración de servicio existente no tiene el formato generado. Revísala localmente.')
    else:
        password = secrets.token_hex(32)
        path.write_text(content.rstrip() + '\nCAFAE_DB_PASSWORD=' + password + '\n', encoding='utf-8')
    migrate()
    # Solo hexadecimal generado localmente; el secreto viaja por stdin, no argumentos.
    psql("ALTER ROLE cafae_service PASSWORD '" + password + "';")
    print('Migraciones verificadas y conexión de servicio configurada. No se crearon usuarios de negocio.')


if __name__ == '__main__':
    main()
