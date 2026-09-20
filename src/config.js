/**
 * AERO-ASTRA — Central WebSocket configuration
 *
 * In production (nginx reverse-proxy), the frontend and backend share one
 * origin so no env var is needed — the WS scheme follows the page scheme.
 *
 * In local development set VITE_WS_URL=ws://localhost:8000 in
 * .env.development; Vite will pick it up automatically.
 */

const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';

/**
 * Base WebSocket URL.
 * Falls back to the current page's host when VITE_WS_URL is not set
 * (i.e. in the hosted / Docker build).
 */
export const WS_BASE =
  import.meta.env.VITE_WS_URL ?? `${proto}://${window.location.host}`;

/** Main simulation + agent stream */
export const WS_URL = `${WS_BASE}/ws`;

/** Sandbox (Run A / Run B comparison) stream */
export const SANDBOX_WS_URL = `${WS_BASE}/ws/sandbox`;
