import { TPL_PREFIX, noStore, json } from '../_kv.js';

const MAX_BYTES = 96 * 1024;
const clean = (id) => (typeof id === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(id) ? id : null);

export const onRequestPut = async ({ env, params, request }) => {
  if (!env.TEMPLATES) return noStore();
  const id = clean(params.id);
  if (!id) return json({ error: 'bad_id' }, 400);

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'bad_json' }, 400);
  }
  if (!body || typeof body !== 'object' || !Array.isArray(body.sel))
    return json({ error: 'bad_template' }, 400);

  const record = {
    id,
    name: String(body.name || 'Untitled').slice(0, 120),
    folder: String(body.folder || 'Uncategorised').slice(0, 80),
    sel: body.sel.filter((x) => typeof x === 'string').slice(0, 500),
    q: body.q && typeof body.q === 'object' ? body.q : {},
    u: body.u && typeof body.u === 'object' ? body.u : {},
    g: body.g && typeof body.g === 'object' ? body.g : {},
    fee: Number.isFinite(+body.fee) ? +body.fee : 22.5,
    created: Number.isFinite(+body.created) ? +body.created : Date.now(),
    used: Number.isFinite(+body.used) ? +body.used : undefined,
  };

  const payload = JSON.stringify(record);
  if (payload.length > MAX_BYTES) return json({ error: 'too_large' }, 413);

  await env.TEMPLATES.put(TPL_PREFIX + id, payload);
  return json({ ok: true, id });
};

export const onRequestDelete = async ({ env, params }) => {
  if (!env.TEMPLATES) return noStore();
  const id = clean(params.id);
  if (!id) return json({ error: 'bad_id' }, 400);
  await env.TEMPLATES.delete(TPL_PREFIX + id);
  return json({ ok: true, id });
};
