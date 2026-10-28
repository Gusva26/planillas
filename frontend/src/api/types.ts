/**
 * Tipos del contrato HTTP compartidos por las vistas.
 *
 * Se mantienen aquí (y no en `types.ts`) porque describen el transporte, no el
 * dominio: si el backend cambia el sobre, cambia este archivo.
 */

/** Respuesta paginada estándar de los listados (`cafae/api/schemas.py`). */
export interface Pagina<T> {
  items: T[];
  total: number;
  limite: number;
  desplazamiento: number;
}

/** Respuesta estándar de las operaciones de escritura. */
export interface RespuestaOk {
  ok: boolean;
  mensaje: string;
  id?: number;
}

export function esPagina<T>(valor: unknown): valor is Pagina<T> {
  if (typeof valor !== 'object' || valor === null) return false;
  const candidato = valor as Record<string, unknown>;
  return Array.isArray(candidato.items) && typeof candidato.total === 'number';
}
