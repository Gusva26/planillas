/**
 * Paginación estándar de los listados en el cliente.
 *
 * Todos los listados paginan igual: se pide una página, se recorta la lista
 * recibida y `Pagination` solo dibuja los controles. Reemplaza el cálculo
 * repetido de `slice((currentPage - 1) * pageSize, ...)` en cada vista.
 */
import { useMemo, useState } from 'react';

export interface Paginacion<T> {
  /** Elementos de la página vigente. */
  items: T[];
  pagina: number;
  tamano: number;
  total: number;
  totalPaginas: number;
  /** Posición (1-based) del primer elemento visible; 0 si no hay datos. */
  desde: number;
  /** Posición (1-based) del último elemento visible; 0 si no hay datos. */
  hasta: number;
  irAPagina: (pagina: number) => void;
  cambiarTamano: (tamano: number) => void;
}

export interface OpcionesPaginacion {
  tamanoInicial?: number;
}

export function usePaginacion<T>(
  items: readonly T[],
  { tamanoInicial = 15 }: OpcionesPaginacion = {}
): Paginacion<T> {
  const [pagina, setPagina] = useState(1);
  const [tamano, setTamano] = useState(tamanoInicial);

  const total = items.length;
  const totalPaginas = Math.max(1, Math.ceil(total / tamano));
  const paginaActual = Math.min(Math.max(1, pagina), totalPaginas);
  const inicio = (paginaActual - 1) * tamano;
  const itemsVisibles = useMemo(
    () => items.slice(inicio, inicio + tamano),
    [items, inicio, tamano]
  );

  return {
    items: itemsVisibles,
    pagina: paginaActual,
    tamano,
    total,
    totalPaginas,
    desde: total === 0 ? 0 : inicio + 1,
    hasta: Math.min(inicio + tamano, total),
    irAPagina: (nueva) => setPagina(Math.min(Math.max(1, nueva), totalPaginas)),
    cambiarTamano: (nuevo) => {
      setTamano(nuevo);
      setPagina(1);
    },
  };
}
