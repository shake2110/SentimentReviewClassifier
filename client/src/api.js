const TOKEN_KEY = 'aspectlens.token';
const USER_KEY = 'aspectlens.user';

export const session = {
  token: () => localStorage.getItem(TOKEN_KEY),
  user: () => {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY) || 'null');
    } catch {
      return null;
    }
  },
  save(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

export class ApiError extends Error {
  constructor(message, status, fields = {}) {
    super(message);
    this.status = status;
    this.fields = fields;
  }
}

/**
 * fetch wrapper: JSON in/out, bearer token, readable errors.
 *   api('/api/products')
 *   api('/api/auth/login', { method: 'POST', body: {...} })
 *   api('/api/products', { method: 'POST', form: formData })
 */
export async function api(path, { method = 'GET', body, form, signal } = {}) {
  const headers = {};
  const token = session.token();
  if (token) headers.Authorization = `Bearer ${token}`;

  let payload;
  if (form) payload = form;
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(path, { method, headers, body: payload, signal });
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    throw new ApiError('Cannot reach the server. Is the backend running on port 5050?', 0);
  }

  let data = null;
  try {
    data = await res.json();
  } catch {
    /* empty or non-JSON body */
  }

  if (!res.ok) {
    if (res.status === 401 && token) window.dispatchEvent(new Event('aspectlens:unauthorized'));
    throw new ApiError(data?.error || `Request failed (${res.status}).`, res.status, data?.fields || {});
  }
  return data;
}
