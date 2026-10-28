/**
 * Cliente HTTP para la API REST de CAFAE.
 *
 * Toda respuesta de error se traduce a `ApiError` (sobre RFC 9457) para que las
 * vistas puedan usar `mensajeDeError(err)` sin tocar `any`.
 */
import { ApiError, apiErrorDesdeStatus, esProblem } from './errors';

const TOKEN_KEY = 'cafae_token';
const DETAIL_POR_DEFECTO = 'Ocurrió un error en el servidor.';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

function headersConCredenciales(extra?: HeadersInit): Headers {
  const headers = new Headers(extra ?? {});
  const token = getToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return headers;
}

function cerrarSesion(): void {
  setToken(null);
  window.location.hash = '#/login';
}

function parsearJson(texto: string): unknown {
  if (!texto.trim()) return null;
  try {
    return JSON.parse(texto);
  } catch {
    return null;
  }
}

function extraerDetail(valor: unknown): string {
  if (typeof valor === 'object' && valor !== null && 'detail' in valor) {
    const detail = (valor as { detail: unknown }).detail;
    if (typeof detail === 'string') return detail;
  }
  if (typeof valor === 'string') return valor;
  return '';
}

/**
 * Convierte una respuesta fallida en `ApiError`.
 *
 * Acepta el sobre del contrato, el `{detail: "..."}` legacy de FastAPI y
 * cuerpos de texto plano (por ejemplo, errores de documentos).
 */
async function errorDeRespuesta(response: Response, fallback = DETAIL_POR_DEFECTO): Promise<ApiError> {
  let texto = '';
  try {
    texto = await response.text();
  } catch {
    texto = '';
  }

  const cuerpo = parsearJson(texto);
  if (esProblem(cuerpo)) {
    return new ApiError(cuerpo);
  }

  const detalle = extraerDetail(cuerpo) || texto.trim() || fallback;
  const instancia = response.url ? new URL(response.url, window.location.origin).pathname : undefined;
  return apiErrorDesdeStatus(response.status, detalle, instancia);
}

async function verificarRespuesta(response: Response, fallback?: string): Promise<Response> {
  if (response.status === 401) {
    cerrarSesion();
    throw await errorDeRespuesta(response, 'Sesión expirada o no autorizada.');
  }
  if (!response.ok) {
    throw await errorDeRespuesta(response, fallback);
  }
  return response;
}

/**
 * Ejecuta una petición y devuelve el JSON ya parseado.
 *
 * El tipo se declara siempre en el punto de llamada (`apiRequest<Planilla[]>(...)`);
 * el valor por defecto es `unknown` para que ningún resultado entre a la UI sin
 * contrato explícito.
 */
export async function apiRequest<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = headersConCredenciales(options.headers);
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(path, { ...options, headers });
  await verificarRespuesta(response);

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get('content-type') ?? '';
  const texto = await response.text();
  if (!texto) {
    return undefined as T;
  }
  if (contentType.includes('json')) {
    const datos = parsearJson(texto);
    if (datos === null) {
      throw apiErrorDesdeStatus(
        response.status,
        'El servidor devolvió una respuesta ilegible.',
        path
      );
    }
    return datos as T;
  }
  return texto as unknown as T;
}

/** Descarga un archivo binario respetando el nombre indicado por la vista. */
export async function downloadFile(path: string, filename: string): Promise<void> {
  const response = await fetch(path, { headers: headersConCredenciales() });
  await verificarRespuesta(response, 'Error al descargar archivo.');

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

/** Abre un PDF en una pestaña nueva sin exponer el token en la URL. */
export async function previewPdfInTab(path: string): Promise<void> {
  const response = await fetch(path, { headers: headersConCredenciales() });
  await verificarRespuesta(response, 'Error al visualizar documento PDF.');

  const blob = await response.blob();
  const file = new Blob([blob], { type: 'application/pdf' });
  const fileURL = URL.createObjectURL(file);
  window.open(fileURL, '_blank');
}
