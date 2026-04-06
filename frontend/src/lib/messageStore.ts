import { getDb } from "./db";
import type { DecryptedMessage } from "./types";
const STORE = "messages";

export const MessageStore = {
  async saveConversation(
    conversationId: string,
    messages: DecryptedMessage[]
  ): Promise<void> {
    const db = await getDb();
    await db.put(STORE, messages, conversationId);
  },
  async getConversation(
    conversationId: string
  ): Promise<DecryptedMessage[] | undefined> {
    const db = await getDb();
    return (await db.get(STORE, conversationId)) as
      | DecryptedMessage[]
      | undefined;
  },
};
