/**
 * Edge gate for PriceDeskLY.
 *
 * Runs on every request BEFORE any asset is served, so the application
 * HTML - which embeds the full rate card - never reaches an unauthenticated
 * browser. A client-side password prompt would not do this: the page would
 * already have been delivered.
 *
 * Credentials come from Pages environment variables when set, so they can be
 * rotated without a commit. See README for how to set AUTH_USER / AUTH_PASS.
 */
const REALM = 'PriceDeskLY';

function timingSafeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function unauthorized() {
  return new Response('Authentication required.', {
    status: 401,
    headers: {
      'WWW-Authenticate': `Basic realm="${REALM}", charset="UTF-8"`,
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Robots-Tag': 'noindex, nofollow, noarchive',
    },
  });
}

export const onRequest = async ({ request, env, next }) => {
  const user = env.AUTH_USER || 'rweMM';
  const pass = env.AUTH_PASS || 'cost@2026';

  const header = request.headers.get('Authorization') || '';
  if (!header.startsWith('Basic ')) return unauthorized();

  let decoded;
  try {
    decoded = atob(header.slice(6));
  } catch {
    return unauthorized();
  }

  const sep = decoded.indexOf(':');
  if (sep < 0) return unauthorized();

  const okUser = timingSafeEqual(decoded.slice(0, sep), user);
  const okPass = timingSafeEqual(decoded.slice(sep + 1), pass);
  if (!(okUser && okPass)) return unauthorized();

  // Authenticated: serve the asset, but never let a shared cache keep it.
  const res = await next();
  const out = new Response(res.body, res);
  out.headers.set('Cache-Control', 'no-store, private');
  out.headers.set('X-Robots-Tag', 'noindex, nofollow, noarchive');
  return out;
};
