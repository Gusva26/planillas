"""Ejecuta las pruebas del contrato del API; no crean ni tocan bases de datos.

Uso: python scripts/test_api.py
Requiere la imagen `cafae-app:local` (docker compose build app).
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = subprocess.run([
        'docker', 'compose', 'run', '--rm', '--no-deps', '-T',
        '-v', str(ROOT / 'tests' / 'api') + ':/tests:ro',
        '-v', str(ROOT / 'cafae') + ':/app/cafae:ro',
        'app', 'python', '/tests/test_contrato.py',
    ], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')

    output = result.stdout + result.stderr
    print(output, end='')
    result.check_returncode()

    count = re.search(r'Ran (\d+) tests?', output)
    if not count:
        raise RuntimeError('No se encontró el resumen de pruebas.')

    dest = ROOT / 'test-results'
    dest.mkdir(exist_ok=True)
    (dest / 'api.json').write_text(json.dumps({
        'ok': True,
        'tests': int(count.group(1)),
        'completed_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'Sobre de error RFC 9457, revisión en creación y esquema OpenAPI',
    }, indent=2), encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main() or 0)
