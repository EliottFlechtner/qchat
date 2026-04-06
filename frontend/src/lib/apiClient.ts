import { API_BASE_URL } from "./config";
import type {
  RegisterRequest,
  RegisterResponse,
  GetPublicKeysResponse,
  SendRequest,
  SendResponse,
  InboxMessageWire,
  ConversationListResponse,
  ConversationMessagesResponse,
} from "./types";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  console.log("[ApiClient] Making request:", {
    url: `${API_BASE_URL}${path}`,
    method: init?.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
    });

    console.log("[ApiClient] Response received:", {
      status: res.status,
      ok: res.ok,
      statusText: res.statusText,
    });

    if (!res.ok) {
      console.error("[ApiClient] Request failed:", {
        status: res.status,
        statusText: res.statusText,
      });
      throw new Error(`Request failed: ${res.status} ${res.statusText}`);
    }

    const data = await res.json();
    console.log("[ApiClient] Response data:", data);
    return data as T;
  } catch (err) {
    console.error("[ApiClient] Request error:", err);
    throw err;
  }
}

export const ApiClient = {
  async register(req: RegisterRequest): Promise<RegisterResponse> {
    return http<RegisterResponse>("/register", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  async getPublicKeys(username: string): Promise<GetPublicKeysResponse> {
    if (!username) throw new Error("Username is required");
    return http<GetPublicKeysResponse>(
      `/pubkey/${encodeURIComponent(username.trim())}`
    );
  },

  async sendMessage(req: SendRequest): Promise<SendResponse> {
    return http<SendResponse>("/send", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  async getInbox(username: string): Promise<InboxMessageWire[]> {
    return http<InboxMessageWire[]>(`/inbox/${encodeURIComponent(username)}`);
  },

  async getConversations(username: string): Promise<ConversationListResponse> {
    return http<ConversationListResponse>(
      `/conversations/${encodeURIComponent(username)}`
    );
  },

  async getConversationMessages(
    username: string,
    conversationId: string
  ): Promise<ConversationMessagesResponse> {
    return http<ConversationMessagesResponse>(
      `/conversations/${encodeURIComponent(username)}/${encodeURIComponent(
        conversationId
      )}/messages`
    );
  },
};
