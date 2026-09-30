"""Ejecuta pruebas del Motor de Cálculos y Ciclo de Planillas contra una base aislada."""
import json
import re
import subprocess
import uuid
from datetime import datetime, timezone

from migrate import CONTAINER, ROOT, database_name, migrate


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    db = database_name('cafae_test_pln_' + uuid.uuid4().hex[:12])
    run('docker', 'exec', CONTAINER, 'createdb', '-U', 'cafae_migrator', db)
    try:
        migrate(db)
        result = subprocess.run([
            'docker', 'compose', 'run', '--rm', '--no-deps', '-T',
            '-e', 'CAFAE_DB_NAME=' + db,
            '-v', str(ROOT / 'tests' / 'planillas') + ':/tests:ro',
            '-v', str(ROOT / 'cafae') + ':/app/cafae:ro',
            'app', 'python', '/tests/test_planillas.py'
        ], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')

        output = result.stdout + result.stderr
        print(output, end='')
        result.check_returncode()
        count = re.search(r'Ran (\d+) tests', output)
        if not count:
            raise RuntimeError('No se encontró el resumen de pruebas.')
        dest = ROOT / 'test-results'
        dest.mkdir(exist_ok=True)
        (dest / 'planillas.json').write_text(json.dumps({
            'ok': True,
            'tests': int(count.group(1)),
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'scope': 'Cálculos Decimal ROUND_HALF_UP, creación maestro/copia, edición por lote, cierre y reapertura'
        }, indent=2), encoding='utf-8')
    finally:
        run('docker', 'exec', CONTAINER, 'dropdb', '-U', 'cafae_migrator', db)


if __name__ == '__main__':
    main()
