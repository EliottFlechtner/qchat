import { useState } from "react";
import { useAppState } from "../state/appState";

export function ConversationView() {
  const {
    currentUser,
    openConversationId,
    messagesByConv,
    otherUserByConv,
    sendText,
  } = useAppState();
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (!currentUser || !openConversationId) return null;
  const messages = messagesByConv[openConversationId] || [];

  // For synthetic conversation IDs (username1:username2), extract the other user
  let other = otherUserByConv[openConversationId] || "";
  if (!other && openConversationId.includes(":")) {
    const [user1, user2] = openConversationId.split(":");
    other = user1 === currentUser.username ? user2 : user1;
  }

  console.log("[ConversationView] Conversation details:", {
    openConversationId,
    other,
    currentUser: currentUser.username,
    messagesCount: messages.length,
  });

  const handleSend = async (message: string) => {
    console.log("[ConversationView] Starting handleSend", { message, other });
    if (!message.trim()) {
      console.log("[ConversationView] Empty message, ignoring");
      return;
    }
    setError(null);
    try {
      console.log("[ConversationView] Calling sendText with:", {
        recipient: other,
        message: message.trim(),
      });
      await sendText(other, message.trim());
      console.log("[ConversationView] Message sent successfully");
      setText("");
    } catch (err) {
      console.error("[ConversationView] Error sending message:", err);
      setError(err instanceof Error ? err.message : "Failed to send message");
    }
  };

  return (
    <div className="conv-view">
      <div className="header">
        <h3>Chat with {other}</h3>
      </div>
      <div
        className="messages"
        style={{
          maxHeight: 300,
          overflow: "auto",
          border: "1px solid #ddd",
          padding: 8,
        }}
      >
        {messages.map((m) => (
          <div key={m.id} style={{ marginBottom: 8 }}>
            <div style={{ fontSize: 12, color: "#666" }}>
              {m.sender} • {new Date(m.wire.sent_at).toLocaleString()}{" "}
              {m.trusted ? "" : "(untrusted)"}
            </div>
            <div>{m.text ?? "<unable to decrypt>"}</div>
          </div>
        ))}
      </div>
      <div className="composer" style={{ marginTop: 8 }}>
        <input
          placeholder="Type a message"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend(text);
          }}
        />
        {error && <div style={{ color: "red", marginTop: 4 }}>{error}</div>}
        <button onClick={() => handleSend(text)}>Send</button>
      </div>
    </div>
  );
}
