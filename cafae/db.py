"""Conexiones cortas y transacciones; nunca compartir conexiones entre sesiones."""
import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


def connection_settings():
    return dict(host=os.environ.get('CAFAE_DB_HOST', 'db'),
                port=int(os.environ.get('CAFAE_DB_PORT', '5432')),
                dbname=os.environ.get('CAFAE_DB_NAME', 'cafae_dev'),
                user='cafae_service', password=os.environ['CAFAE_DB_PASSWORD'],
                connect_timeout=5, application_name='cafae_app', row_factory=dict_row)


@contextmanager
def transaction(settings=None):
    with psycopg.connect(**(settings or connection_settings())) as conn:
        conn.execute('SET LOCAL ROLE cafae_auth')
        conn.execute('SET LOCAL search_path TO cafae, pg_temp')
        conn.execute("SET LOCAL statement_timeout = '10s'")
        conn.execute("SET LOCAL lock_timeout = '5s'")
        yield conn
