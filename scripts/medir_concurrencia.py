"""Mide el techo de concurrencia de la capa de datos (deuda D-11).

Hoy cada operación abre su propia conexión (`cafae/db.py`), sin pool. Antes de
agregar uno hay que saber si el costo de abrir conexión es realmente el
limitante, así que este script mide dos rutas:

- `SELECT 1` a través de `transaction()`: costo puro de conexión + `SET LOCAL`.
- `CatalogoService.list_niveles`: una lectura real, con permiso y rol SQL.

Sube la concurrencia (1, 4, 8, 16, 32, 64 hilos) y reporta p50, p95, máximo,
operaciones por segundo y errores. Corre contra una base desechable
`cafae_test_*`, nunca contra `cafae_dev`.

Uso:
    python scripts/medir_concurrencia.py

Con `CAFAE_DB_NAME=cafae_test_*` definido, el mismo archivo actúa como el
medidor que se ejecuta dentro del contenedor.
"""
import json
import os
import secrets
import statistics
import subprocess
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

NIVELES = (1, 4, 8, 16, 32, 64)
MARCA = 'MEDICION_JSON:'


# ---------------------------------------------------------------------------
# Medidor (se ejecuta dentro del contenedor)
# ---------------------------------------------------------------------------
def _medir():
    import psycopg

    from cafae.auth import AuthService
    from cafae.catalogos import CatalogoService
    from cafae.db import connection_settings, transaction
    from cafae.security import UserError

    if not os.environ.get('CAFAE_DB_NAME', '').startswith('cafae_test_'):
        raise SystemExit('La medición exige una base cafae_test_* aislada.')

    auth = AuthService()
    cat = CatalogoService(auth)
    clave = secrets.token_urlsafe(24)
    try:
        auth.bootstrap('admin_medicion', 'Administrador Medición', clave)
    except UserError:
        pass
    token = auth.login('admin_medicion', clave, uuid.uuid4().hex)

    with transaction() as conn:
        max_conexiones = conn.execute('SHOW max_connections').fetchone()['max_connections']

    def una_conexion():
        with transaction() as conn:
            conn.execute('SELECT 1').fetchone()

    def una_lectura():
        cat.list_niveles(token)

    # Control: la misma consulta sobre una conexión que ya existe. Si esto
    # también se estanca, el techo no es abrir conexión sino el cliente.
    def control_reutilizado():
        """Devuelve (consulta, cierre) con una conexión viva por hilo."""
        locales = threading.local()
        abiertas = []
        cerrojo = threading.Lock()

        def consulta():
            conn = getattr(locales, 'conn', None)
            if conn is None or conn.closed:
                conn = psycopg.connect(**connection_settings(), autocommit=True)
                conn.execute('SET ROLE cafae_auth')
                conn.execute('SET search_path TO cafae, pg_temp')
                conn.execute("SET statement_timeout = '10s'")
                conn.execute("SET lock_timeout = '5s'")
                locales.conn = conn
                with cerrojo:
                    abiertas.append(conn)
            conn.execute('SELECT 1').fetchone()

        def cerrar():
            for conn in abiertas:
                conn.close()

        return consulta, cerrar

    resultados = []
    for operacion, fabrica in (('select_1', None),
                               ('select_1_reutilizada', control_reutilizado),
                               ('list_niveles', None)):
        for hilos in NIVELES:
            cerrar = lambda: None
            if fabrica is None:
                funcion = una_conexion if operacion == 'select_1' else una_lectura
            else:
                funcion, cerrar = fabrica()

            total = max(40, hilos * 8)
            tiempos, errores = [], []

            def trabajo(_):
                inicio = time.perf_counter()
                try:
                    funcion()
                except Exception as exc:  # se reporta, no se silencia
                    errores.append(f'{type(exc).__name__}: {exc}')
                return (time.perf_counter() - inicio) * 1000

            arranque = time.perf_counter()
            with ThreadPoolExecutor(max_workers=hilos) as pool:
                tiempos = list(pool.map(trabajo, range(total)))
            duracion = time.perf_counter() - arranque
            cerrar()

            resultados.append({
                'operacion': operacion,
                'hilos': hilos,
                'peticiones': total,
                'p50_ms': round(statistics.median(tiempos), 1),
                'p95_ms': round(_percentil(tiempos, 95), 1),
                'max_ms': round(max(tiempos), 1),
                'ops_por_segundo': round(total / duracion, 1),
                'errores': len(errores),
                'error_ejemplo': errores[0] if errores else None,
            })

    print(MARCA + json.dumps({
        'max_connections': max_conexiones,
        'resultados': resultados,
    }, ensure_ascii=False))


def _percentil(valores, p):
    ordenados = sorted(valores)
    posicion = min(len(ordenados) - 1, int(round((p / 100) * len(ordenados))) - 1)
    return ordenados[max(posicion, 0)]


# ---------------------------------------------------------------------------
# Orquestador (se ejecuta en el host)
# ---------------------------------------------------------------------------
def _orquestar():
    from migrate import CONTAINER, ROOT, database_name, migrate

    db = database_name('cafae_test_conc_' + uuid.uuid4().hex[:10])
    subprocess.run(['docker', 'exec', CONTAINER, 'createdb', '-U', 'cafae_migrator', db], check=True)
    try:
        migrate(db)
        resultado = subprocess.run([
            'docker', 'compose', 'run', '--rm', '--no-deps', '-T',
            '-e', 'CAFAE_DB_NAME=' + db,
            '-v', str(ROOT / 'scripts' / 'medir_concurrencia.py') + ':/app/medir.py:ro',
            '-v', str(ROOT / 'cafae') + ':/app/cafae:ro',
            'app', 'python', '/app/medir.py',
        ], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')

        salida = resultado.stdout + resultado.stderr
        if resultado.returncode:
            print(salida, end='')
            raise RuntimeError('La medición falló dentro del contenedor.')

        linea = next((l for l in salida.splitlines() if l.startswith(MARCA)), None)
        if not linea:
            print(salida, end='')
            raise RuntimeError('No se encontró el resultado de la medición.')

        datos = json.loads(linea[len(MARCA):])
        _imprimir(datos)

        dest = ROOT / 'test-results'
        dest.mkdir(exist_ok=True)
        (dest / 'concurrencia.json').write_text(json.dumps({
            'ok': True,
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'base': 'cafae_test_* desechable',
            **datos,
        }, indent=2, ensure_ascii=False), encoding='utf-8')
        print('\nDetalle en test-results/concurrencia.json')
    finally:
        subprocess.run(['docker', 'exec', CONTAINER, 'dropdb', '-U', 'cafae_migrator', db], check=True)


def _imprimir(datos):
    print(f"max_connections del servidor: {datos['max_connections']}\n")
    print(f"{'operacion':<22}{'hilos':>6}{'p50 ms':>9}{'p95 ms':>9}{'max ms':>9}{'ops/s':>9}{'errores':>9}")
    for fila in datos['resultados']:
        print(f"{fila['operacion']:<22}{fila['hilos']:>6}{fila['p50_ms']:>9}"
              f"{fila['p95_ms']:>9}{fila['max_ms']:>9}{fila['ops_por_segundo']:>9}{fila['errores']:>9}")
    fallas = [f for f in datos['resultados'] if f['errores']]
    if fallas:
        print('\nPrimeros errores:')
        for fila in fallas[:3]:
            print(f"  {fila['operacion']} a {fila['hilos']} hilos: {fila['error_ejemplo']}")


if __name__ == '__main__':
    if os.environ.get('CAFAE_DB_NAME', '').startswith('cafae_test_'):
        _medir()
    else:
        _orquestar()
