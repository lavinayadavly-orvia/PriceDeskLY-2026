import { readAll, noStore, json } from '../_kv.js';

export const onRequestGet = async ({ env }) => {
  if (!env.TEMPLATES) return noStore();
  try {
    return json(await readAll(env.TEMPLATES));
  } catch (e) {
    return json({ error: 'read_failed', message: String(e) }, 500);
  }
};
