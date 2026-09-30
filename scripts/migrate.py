"""Migraciones SQL transaccionales en el contenedor local, sin dependencias Python.

No recibe contraseñas por argumentos. El socket interno se usa solo para administración.
El nombre de base está restringido a desarrollo o pruebas creadas por este proyecto.
"""
import argparse
import hashlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTAINER = 'cafae-postgres-dev'

def database_name(value):
    if value != 'cafae_dev' and not re.fullmatch(r'cafae_test_[a-z0-9_]+', value):
        raise ValueError('Solo se permiten cafae_dev o cafae_test_* en este ejecutor local.')
    return value

def psql(sql, database='cafae_dev', check=True):
    database_name(database)
    result = subprocess.run(['docker', 'exec', '-i', CONTAINER, 'psql', '-X',
        '-U', 'cafae_migrator', '-d', database, '-v', 'ON_ERROR_STOP=1', '-At'],
        input=sql, text=True, encoding='utf-8', capture_output=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result

def migrate(database='cafae_dev'):
    statements = [r'\set ON_ERROR_STOP on', 'BEGIN;',
        'SELECT pg_advisory_xact_lock(82609123);',
        '''CREATE TABLE IF NOT EXISTS public.cafae_migraciones (
            nombre text PRIMARY KEY, sha256 text NOT NULL,
            aplicada_en timestamptz NOT NULL DEFAULT now());''']
    names = []
    for path in sorted((ROOT/'database'/'migrations').glob('[0-9]*.sql')):
        name = path.name
        if not re.fullmatch(r'[0-9]{3}_[a-z_]+\.sql', name):
            raise ValueError('Nombre de migración inválido')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        statements += [f"""DO $$ BEGIN IF EXISTS (SELECT 1 FROM public.cafae_migraciones
          WHERE nombre='{name}' AND sha256<>'{digest}') THEN
          RAISE EXCEPTION 'La migración aplicada cambió: {name}'; END IF; END $$;""",
          f"SELECT NOT EXISTS (SELECT 1 FROM public.cafae_migraciones WHERE nombre='{name}') AS aplicar \\gset",
          r'\if :aplicar', path.read_text(encoding='utf-8'),
          f"INSERT INTO public.cafae_migraciones(nombre,sha256) VALUES ('{name}','{digest}');",r'\endif']
        names.append(name)
    statements += ['COMMIT;']
    psql('\n'.join(statements), database)
    return names

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', default='cafae_dev', type=database_name)
    args = parser.parse_args()
    print('Migraciones verificadas:', ', '.join(migrate(args.database)))
