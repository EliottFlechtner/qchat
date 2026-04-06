import { openDB } from "idb";
import type { IDBPDatabase } from "idb";

const DB_NAME = "qchat";
const DB_VERSION = 2; // bump to ensure all stores exist

export async function getDb(): Promise<IDBPDatabase> {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains("keys")) {
        const store = db.createObjectStore("keys", { keyPath: "username" });
        store.createIndex("by_username", "username", { unique: true });
      }
      if (!db.objectStoreNames.contains("pkcache")) {
        const store = db.createObjectStore("pkcache", { keyPath: "username" });
        store.createIndex("by_username", "username", { unique: true });
      }
      if (!db.objectStoreNames.contains("messages")) {
        db.createObjectStore("messages");
      }
    },
  });
}
