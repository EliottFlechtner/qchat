import {getDb} from './db';
import type {PublicKeyCacheEntry, UserKeysRecord} from './types';

const USER_KEYS_STORE = 'keys';
const PUBLIC_KEY_CACHE_STORE = 'pkcache';

export const KeyStore = {
  async saveUserKeys(record: UserKeysRecord): Promise<void> {
    const db = await getDb();
    await db.put(USER_KEYS_STORE, record);
  },

  async getUserKeys(username: string): Promise<UserKeysRecord|undefined> {
    const db = await getDb();
    return (await db.get(USER_KEYS_STORE, username)) as | UserKeysRecord |
        undefined;
  },

  async cachePublicKeys(username: string, keys: PublicKeyCacheEntry):
      Promise<void> {
        const db = await getDb();
        await db.put(PUBLIC_KEY_CACHE_STORE, {username, ...keys});
      },

  async getCachedPublicKeys(username: string):
      Promise<PublicKeyCacheEntry|undefined> {
        const db = await getDb();
        const entry = (await db.get(PUBLIC_KEY_CACHE_STORE, username)) as |
            ({username: string} & PublicKeyCacheEntry) | undefined;
        if (!entry) return undefined;
        return {
          kem_pk: entry.kem_pk,
          sig_pk: entry.sig_pk,
        };
      },
};
