/**
 * Contrato de errores del API (RFC 9457) del lado del cliente.
 *
 * El backend garantiza el sobre `application/problem+json` descrito en
 * `cafae/api/errors.py` y en `docs/11-contrato-api.md`. La UI debe ramificar
 * por `code`, nunca por el texto de `detail`.
 */

/** Códigos estables publicados por el backend. */
export const CODIGOS_ERROR = [
  'SOLICITUD_INVALIDA',
  'NO_AUTENTICADO',
  'SIN_PERMISO',
  'NO_ENCONTRADO',
  'CONFLICTO_REVISION',
  'CONFLICTO_ESTADO',
  'VALIDACION',
  'ERROR_INTERNO',
] as const;

export type CodigoError = (typeof CODIGOS_ERROR)[number];

/** Código local para respuestas que no cumplen el sobre (proxy, red, versiones viejas). */
export type CodigoDesconocido = 'ERROR_DESCONOCIDO';

export interface CampoInvalido {
  campo: string;
  mensaje: string;
}

/** Cuerpo de error tal como viaja por la red. */
export interface Problem {
  type: string;
  title: string;
  status: number;
  code: string;
  detail: string;
  instance?: string;
  errors?: CampoInvalido[];
}

const TITULOS_POR_STATUS: Record<number, string> = {
  400: 'Solicitud inválida',
  401: 'No autenticado',
  403: 'Sin permiso',
  404: 'Recurso no encontrado',
  409: 'Conflicto de estado',
  422: 'Solicitud inválida',
  500: 'Error interno',
};

const CODIGOS_POR_STATUS: Record<number, CodigoError> = {
  400: 'SOLICITUD_INVALIDA',
  401: 'NO_AUTENTICADO',
  403: 'SIN_PERMISO',
  404: 'NO_ENCONTRADO',
  409: 'CONFLICTO_ESTADO',
  422: 'VALIDACION',
};

export function esCodigoError(valor: unknown): valor is CodigoError {
  return typeof valor === 'string' && (CODIGOS_ERROR as readonly string[]).includes(valor);
}

/** Traduce un status HTTP suelto al catálogo, igual que `problema_para_status` en el backend. */
export function codigoParaStatus(status: number): CodigoError {
  return CODIGOS_POR_STATUS[status] ?? (status >= 500 ? 'ERROR_INTERNO' : 'SOLICITUD_INVALIDA');
}

/** Error uniforme del API: conserva `code`, `status` y los errores por campo. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: CodigoError | CodigoDesconocido;
  readonly title: string;
  readonly instance?: string;
  readonly erroresDeCampo: readonly CampoInvalido[];

  constructor(problem: Problem) {
    super(problem.detail || problem.title);
    this.name = 'ApiError';
    this.status = problem.status;
    this.code = esCodigoError(problem.code) ? problem.code : 'ERROR_DESCONOCIDO';
    this.title = problem.title;
    this.instance = problem.instance;
    this.erroresDeCampo = problem.errors ?? [];
  }

  /** `true` cuando otro usuario movió la planilla: hay que recargar antes de guardar. */
  get esConflictoDeRevision(): boolean {
    return this.code === 'CONFLICTO_REVISION';
  }
}

function esRegistro(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === 'object' && valor !== null;
}

/** Detecta el sobre del contrato sin confiar en el `Content-Type`. */
export function esProblem(valor: unknown): valor is Problem {
  return (
    esRegistro(valor) &&
    typeof valor.type === 'string' &&
    typeof valor.title === 'string' &&
    typeof valor.status === 'number' &&
    typeof valor.code === 'string' &&
    typeof valor.detail === 'string'
  );
}

export function esApiError(err: unknown): err is ApiError {
  return err instanceof ApiError;
}

/** Arma un `ApiError` a partir de un status y un detalle sueltos (respuestas legacy o de red). */
export function apiErrorDesdeStatus(status: number, detail: string, instance?: string): ApiError {
  const code = codigoParaStatus(status);
  return new ApiError({
    type: `urn:problem-type:cafae:${code.toLowerCase().replaceAll('_', '-')}`,
    title: TITULOS_POR_STATUS[status] ?? (status >= 500 ? 'Error interno' : 'Solicitud inválida'),
    status,
    code,
    detail,
    instance,
  });
}

/** Mensaje listo para mostrar al usuario; nunca devuelve `undefined`. */
export function mensajeDeError(err: unknown, fallback = 'Ocurrió un error inesperado.'): string {
  if (esApiError(err)) {
    return err.message || fallback;
  }
  if (err instanceof Error) {
    return err.message || fallback;
  }
  if (typeof err === 'string' && err.trim()) {
    return err;
  }
  return fallback;
}
