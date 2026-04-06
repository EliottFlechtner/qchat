const env = import.meta.env;

export const API_BASE_URL: string = env.VITE_API_BASE_URL || '/api';

// Build an absolute WS URL if not provided via env
function computeDefaultWsUrl(): string {
  if (typeof window !== 'undefined' && window.location) {
    const isSecure = window.location.protocol === 'https:';
    const scheme = isSecure ? 'wss://' : 'ws://';
    return `${scheme}${window.location.host}/ws`;
  }
  return 'ws://localhost:8000/ws';
}

export const WS_BASE_URL: string =
    env.VITE_WS_BASE_URL || computeDefaultWsUrl();
