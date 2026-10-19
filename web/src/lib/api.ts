import { auth } from './firebase';

const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const API = `${base}/api/v1`;

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await auth.currentUser?.getIdToken();
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && options.body) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (!response.ok) {
    const errorText = await response.text();
    let detail = errorText;
    try { detail = JSON.parse(errorText).detail || errorText; } catch { /* Keep the server response text. */ }
    throw new Error(`API ${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}
