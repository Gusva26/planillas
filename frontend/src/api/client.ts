/**
 * Cliente HTTP para la API REST de CAFAE.
 */

const TOKEN_KEY = 'cafae_token';

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

export async function apiRequest<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    setToken(null);
    window.location.hash = '#/login';
    throw new Error('Sesión expirada o no autorizada.');
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Ocurrió un error en el servidor.');
    }
    return data as T;
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Ocurrió un error en la solicitud.');
  }

  return response as unknown as T;
}

export async function downloadFile(path: string, filename: string): Promise<void> {
  const token = getToken();
  const headers = new Headers();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(path, { headers });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Error al descargar archivo.');
  }

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

export async function previewPdfInTab(path: string): Promise<void> {
  const token = getToken();
  const headers = new Headers();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(path, { headers });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Error al visualizar documento PDF.');
  }

  const blob = await response.blob();
  const file = new Blob([blob], { type: 'application/pdf' });
  const fileURL = URL.createObjectURL(file);
  window.open(fileURL, '_blank');
}

