import { FOLDER_KEY, noStore, json } from './_kv.js';

export const onRequestPut = async ({ env, request }) => {
  if (!env.TEMPLATES) return noStore();
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'bad_json' }, 400);
  }
  if (!Array.isArray(body)) return json({ error: 'bad_folders' }, 400);
  const folders = [...new Set(body.filter((f) => typeof f === 'string' && f.trim()))]
    .map((f) => f.trim().slice(0, 80))
    .slice(0, 200);
  await env.TEMPLATES.put(FOLDER_KEY, JSON.stringify(folders));
  return json({ ok: true, folders });
};
