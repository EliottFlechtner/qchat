import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type {
  CurrentUser,
  InboxMessageWire,
  ConversationListItem,
  DecryptedMessage,
  UserKeysRecord,
} from "../lib/types";
import { ApiClient } from "../lib/apiClient";
import { KeyStore } from "../lib/keyStore";
import { WebSocketClient } from "../lib/wsClient";
import { computeMessageId } from "../lib/messageId";
import {
  generateKemKeypair,
  generateSigKeypair,
  decryptWireToText,
  encryptTextToWire,
} from "../lib/cryptoAdapter";
import { MessageStore } from "../lib/messageStore";

type AppContextState = {
  currentUser?: CurrentUser;
  ensureOnboarded: (username: string) => Promise<void>;
  conversations: ConversationListItem[];
  refreshConversations: () => Promise<void>;
  messagesByConv: Record<string, DecryptedMessage[]>;
  openConversationId?: string;
  setOpenConversationId: (id?: string) => void;
  otherUserByConv: Record<string, string>;
  sendText: (recipient: string, text: string) => Promise<void>;
};

const AppContext = createContext<AppContextState | undefined>(undefined);

// eslint-disable-next-line react-refresh/only-export-components
export function useAppState(): AppContextState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("AppContext missing");
  return ctx;
}

export function AppStateProvider({ children }: { children: React.ReactNode }) {
  const [currentUser, setCurrentUser] = useState<CurrentUser | undefined>(
    undefined
  );
  const [conversations, setConversations] = useState<ConversationListItem[]>(
    []
  );
  const [messagesByConv, setMessagesByConv] = useState<
    Record<string, DecryptedMessage[]>
  >({});
  const [otherUserByConv, setOtherUserByConv] = useState<
    Record<string, string>
  >({});
  const [openConversationId, setOpenConversationId] = useState<
    string | undefined
  >(undefined);
  const wsRef = useRef<WebSocketClient | undefined>(undefined);
  const kemSkRef = useRef<string | undefined>(undefined);
  const sigSkRef = useRef<string | undefined>(undefined);

  // Handle notifications -> pull inbox
  const pullInbox = async (username: string) => {
    const list = await ApiClient.getInbox(username).catch(
      () => [] as InboxMessageWire[]
    );
    if (!list.length) return;

    const keys = await KeyStore.getUserKeys(username);
    if (!keys) return;
    for (const msg of list) {
      // verify + decrypt
      // sender sig pk: cache or fetch
      const pkCached = await KeyStore.getCachedPublicKeys(msg.sender);
      const fetched = pkCached
        ? undefined
        : await ApiClient.getPublicKeys(msg.sender).catch(() => undefined);
      const pk =
        pkCached ||
        (fetched
          ? { kem_pk: fetched.kem_pk, sig_pk: fetched.sig_pk }
          : undefined);
      if (!pk) continue;
      if (!pkCached) await KeyStore.cachePublicKeys(msg.sender, pk);

      const { text, trusted } = await decryptWireToText(
        msg.ciphertext,
        msg.nonce,
        msg.encapsulated_key,
        msg.signature,
        pk.sig_pk,
        keys.kem_sk
      );
      const dm: DecryptedMessage = {
        id: computeMessageId(msg),
        sender: msg.sender,
        text,
        trusted,
        wire: msg,
      };
      // Put into a synthetic conversation ID by participants ordering for MVP
      const convId = await deriveConversationId(username, msg.sender);
      let updated: DecryptedMessage[] = [];
      setMessagesByConv((prev) => {
        const arr = [...(prev[convId] || [])];
        if (!arr.find((m) => m.id === dm.id)) arr.push(dm);
        updated = arr;
        return { ...prev, [convId]: arr };
      });
      setOtherUserByConv((prev) => ({ ...prev, [convId]: msg.sender }));
      await MessageStore.saveConversation(convId, updated);
    }
  };

  async function deriveConversationId(a: string, b: string): Promise<string> {
    return [a, b].sort().join(":");
  }

  const ensureOnboarded = async (username: string) => {
    const existing = await KeyStore.getUserKeys(username);
    let keys: UserKeysRecord | undefined = existing;
    if (!existing) {
      const kem = await generateKemKeypair();
      const sig = await generateSigKeypair();
      keys = {
        username,
        kem_sk: kem.privateKeyB64,
        kem_pk: kem.publicKeyB64,
        sig_sk: sig.privateKeyB64,
        sig_pk: sig.publicKeyB64,
      };
      await KeyStore.saveUserKeys(keys);
    }
    if (!keys) throw new Error("Failed to prepare keys");

    kemSkRef.current = keys.kem_sk;
    sigSkRef.current = keys.sig_sk;

    await ApiClient.register({
      username,
      kem_pk: keys.kem_pk,
      sig_pk: keys.sig_pk,
    }).catch(() => undefined);
    setCurrentUser({ username, kem_pk: keys.kem_pk, sig_pk: keys.sig_pk });

    wsRef.current?.stop();
    const ws = new WebSocketClient(username, {
      onNotification: () => pullInbox(username),
    });
    wsRef.current = ws;
    ws.start();

    // initial inbox pull
    await pullInbox(username);
    await refreshConversations();
  };

  const refreshConversations = async () => {
    if (!currentUser) return;
    const res = await ApiClient.getConversations(currentUser.username).catch(
      () => ({ conversations: [] as ConversationListItem[] })
    );
    setConversations(res.conversations);
    if (res.conversations?.length) {
      setOtherUserByConv((prev) => {
        const copy = { ...prev };
        for (const c of res.conversations) copy[c.id] = c.other_user;
        return copy;
      });
    }
  };

  const sendText = async (recipient: string, text: string) => {
    console.log("[AppState] Starting sendText", { recipient, text });

    if (!currentUser) {
      console.error("[AppState] No current user found");
      throw new Error("You must be logged in to send messages");
    }

    if (!sigSkRef.current) {
      console.error("[AppState] No signature key found");
      throw new Error("Signature key not found");
    }

    if (!recipient.trim()) {
      console.error("[AppState] Empty recipient");
      throw new Error("Recipient is required");
    }

    console.log("[AppState] Checking cached keys for recipient:", recipient);
    // First try to get cached keys
    const cached = await KeyStore.getCachedPublicKeys(recipient);
    console.log("[AppState] Cached keys result:", { cached });

    // If not cached, fetch from server
    let pks = cached;
    if (!cached) {
      try {
        console.log(
          "[AppState] No cached keys, fetching from server for:",
          recipient
        );
        const fetched = await ApiClient.getPublicKeys(recipient);
        console.log("[AppState] Server returned public keys:", fetched);
        if (!fetched?.kem_pk || !fetched?.sig_pk) {
          throw new Error("Invalid public keys received from server");
        }
        pks = { kem_pk: fetched.kem_pk, sig_pk: fetched.sig_pk };
        // Cache the keys for future use
        console.log("[AppState] Caching new keys for:", recipient);
        await KeyStore.cachePublicKeys(recipient, pks);
      } catch (err) {
        console.error("[AppState] Failed to fetch public keys:", err);
        throw new Error("Recipient not found or server error");
      }
    }

    if (!pks?.kem_pk || !pks?.sig_pk) {
      throw new Error("Public keys not available");
    }

    console.log("[AppState] Encrypting message with keys:", {
      recipient,
      hasKemPk: !!pks.kem_pk,
      hasSigSk: !!sigSkRef.current,
    });
    const wire = await encryptTextToWire(text, pks.kem_pk, sigSkRef.current);
    console.log("[AppState] Message encrypted successfully");
    console.log("[AppState] Sending message to server...");
    await ApiClient.sendMessage({
      sender: currentUser.username,
      recipient,
      ciphertext: wire.ciphertext,
      nonce: wire.nonce,
      encapsulated_key: wire.encapsulated_key,
      signature: wire.signature,
      expires_at: null,
    });
    console.log("[AppState] Message sent to server successfully");

    // optimistic add in synthetic conversation
    const convId = await deriveConversationId(currentUser.username, recipient);
    const dm: DecryptedMessage = {
      id: `${Date.now()}`,
      sender: currentUser.username,
      text,
      trusted: true,
      wire: {
        sender: currentUser.username,
        ciphertext: wire.ciphertext,
        nonce: wire.nonce,
        encapsulated_key: wire.encapsulated_key,
        signature: wire.signature,
        sent_at: new Date().toISOString(),
      },
    };
    let updated: DecryptedMessage[] = [];
    setMessagesByConv((prev) => {
      const arr = [...(prev[convId] || [])];
      arr.push(dm);
      updated = arr;
      return { ...prev, [convId]: arr };
    });
    setOtherUserByConv((prev) => ({ ...prev, [convId]: recipient }));
    await MessageStore.saveConversation(convId, updated);
  };

  useEffect(() => {
    // When opening a server-backed conversation (UUID), fetch messages and decrypt any missing
    if (!currentUser || !openConversationId) return;
    const isUuid = /^[0-9a-fA-F-]{36}$/.test(openConversationId);
    if (!isUuid) return;
    (async () => {
      const res = await ApiClient.getConversationMessages(
        currentUser.username,
        openConversationId
      ).catch(() => undefined);
      const myKeys = await KeyStore.getUserKeys(currentUser.username);
      if (!res || !myKeys) return;
      const decrypted: DecryptedMessage[] = [];
      for (const msg of res.messages) {
        const cached = await KeyStore.getCachedPublicKeys(msg.sender);
        const fetched = cached
          ? undefined
          : await ApiClient.getPublicKeys(msg.sender).catch(() => undefined);
        const pks =
          cached ||
          (fetched
            ? { kem_pk: fetched.kem_pk, sig_pk: fetched.sig_pk }
            : undefined);
        if (!pks) continue;
        if (!cached) await KeyStore.cachePublicKeys(msg.sender, pks);
        const { text, trusted } = await decryptWireToText(
          msg.ciphertext,
          msg.nonce,
          msg.encapsulated_key,
          msg.signature,
          pks.sig_pk,
          myKeys.kem_sk
        );
        decrypted.push({
          id: computeMessageId(msg),
          sender: msg.sender,
          text,
          trusted,
          wire: msg,
        });
      }
      setMessagesByConv((prev) => ({
        ...prev,
        [openConversationId]: decrypted,
      }));
      await MessageStore.saveConversation(openConversationId, decrypted);
    })();
  }, [openConversationId, currentUser?.username]);

  const value = useMemo<AppContextState>(
    () => ({
      currentUser,
      ensureOnboarded,
      conversations,
      refreshConversations,
      messagesByConv,
      openConversationId,
      setOpenConversationId,
      otherUserByConv,
      sendText,
    }),
    [
      currentUser,
      conversations,
      messagesByConv,
      openConversationId,
      otherUserByConv,
    ]
  );

  useEffect(() => {
    return () => wsRef.current?.stop();
  }, []);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
