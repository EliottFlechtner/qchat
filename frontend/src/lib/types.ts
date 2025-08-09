export type RegisterRequest = {
  username: string;
  kem_pk: string; // base64
  sig_pk: string; // base64
};

export type RegisterResponse = {
  status: "registered" | "already_registered";
};

export type GetPublicKeysResponse = {
  username: string;
  kem_pk: string; // base64
  sig_pk: string; // base64
};

export type SendRequest = {
  sender: string;
  recipient: string;
  ciphertext: string; // base64
  nonce: string; // base64 12 bytes
  encapsulated_key: string; // base64
  signature: string; // base64
  expires_at?: string | null;
};

export type SendResponse = {
  status: "sent";
};

export type InboxMessageWire = {
  sender: string;
  ciphertext: string;
  nonce: string;
  encapsulated_key: string;
  signature: string;
  sent_at: string; // ISO
};

export type ConversationListItem = {
  id: string; // UUID
  other_user: string;
  created_at: string; // ISO
  updated_at: string; // ISO
};

export type ConversationListResponse = {
  conversations: ConversationListItem[];
};

export type ConversationMessagesResponse = {
  conversation_id: string;
  messages: InboxMessageWire[];
};

export type CurrentUser = {
  username: string;
  kem_pk: string;
  sig_pk: string;
};

export type UserKeysRecord = {
  username: string;
  kem_sk: string; // base64 PKCS8
  kem_pk: string; // base64 SPKI
  sig_sk: string; // base64 PKCS8
  sig_pk: string; // base64 SPKI
};

export type DecryptedMessage = {
  id: string; // deterministic hash over ciphertext+nonce+signature
  sender: string;
  text?: string; // present when decrypt succeeded
  trusted: boolean; // signature verified
  wire: InboxMessageWire;
};

export type ConversationMessagesState = {
  conversationId: string;
  otherUser: string;
  messages: DecryptedMessage[];
};

export type PublicKeyCacheEntry = {
  kem_pk: string;
  sig_pk: string;
};
