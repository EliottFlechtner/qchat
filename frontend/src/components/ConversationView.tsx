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
    <div className="h-full flex flex-col">
      {/* Chat Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
            {other.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{other}</h3>
            <p className="text-sm text-gray-500">End-to-end encrypted</p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center text-gray-500">
              <p className="text-lg font-medium">No messages yet</p>
              <p className="text-sm mt-1">Start the conversation below</p>
            </div>
          </div>
        ) : (
          messages.map((m) => {
            const isFromCurrentUser = m.sender === currentUser.username;
            return (
              <div
                key={m.id}
                className={`flex ${
                  isFromCurrentUser ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
                    isFromCurrentUser
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <div className="text-sm">
                    {m.text ?? (
                      <span className="italic text-red-300">
                        Unable to decrypt
                      </span>
                    )}
                  </div>
                  <div
                    className={`text-xs mt-1 ${
                      isFromCurrentUser ? "text-blue-100" : "text-gray-500"
                    }`}
                  >
                    {new Date(m.wire.sent_at).toLocaleTimeString()}
                    {!m.trusted && (
                      <span className="ml-1 text-yellow-400">⚠</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Message Composer */}
      <div className="p-4 border-t border-gray-200 bg-white">
        {error && (
          <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        <div className="flex items-end space-x-3">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Type a message..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(text);
                }
              }}
              className="w-full px-4 py-3 border border-gray-300 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
            />
          </div>
          <button
            onClick={() => handleSend(text)}
            disabled={!text.trim()}
            className="bg-blue-600 text-white p-3 rounded-full hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
