/**
 * Shared KV helpers for the templates API.
 *
 * Storage model: one key per template (tpl:<id>) plus one key for the folder
 * list. Writing a template therefore never clobbers a colleague's concurrent
 * write, which a single blob holding everything would.
 */
export const FOLDER_KEY = 'folders:v1';
export const TPL_PREFIX = 'tpl:';

export const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
  });

/** Not-yet-bound KV is a normal state, not an error: the client falls back to local storage. */
export const noStore = () =>
  json({ error: 'kv_unbound', message: 'No KV namespace is bound to this deployment.' }, 503);

export async function readAll(kv) {
  const items = {};
  let cursor;
  do {
    const page = await kv.list({ prefix: TPL_PREFIX, cursor });
    for (const key of page.keys) {
      const raw = await kv.get(key.name);
      if (!raw) continue;
      try {
        const t = JSON.parse(raw);
        if (t && t.id) items[t.id] = t;
      } catch {
        /* skip a corrupt record rather than failing the whole listing */
      }
    }
    cursor = page.list_complete ? null : page.cursor;
  } while (cursor);

  let folders = [];
  const rawFolders = await kv.get(FOLDER_KEY);
  if (rawFolders) {
    try {
      const parsed = JSON.parse(rawFolders);
      if (Array.isArray(parsed)) folders = parsed.filter((f) => typeof f === 'string');
    } catch {
      /* ignore */
    }
  }
  return { folders, items };
}
