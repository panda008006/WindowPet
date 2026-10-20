export function authHeaders(token: string): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {}
}
