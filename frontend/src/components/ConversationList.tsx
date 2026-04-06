import { useEffect, useMemo, useState } from "react";
import { useAppState } from "../state/appState";

export function ConversationList() {
  const {
    currentUser,
    conversations,
    refreshConversations,
    setOpenConversationId,
    otherUserByConv,
  } = useAppState();
  const [recipient, setRecipient] = useState("");

  useEffect(() => {
    refreshConversations();
  }, []);

  if (!currentUser) return null;

  const syntheticConvs = useMemo(
    () =>
      Object.entries(otherUserByConv).map(([id, other]) => ({
        id,
        other_user: other,
      })),
    [otherUserByConv]
  );

  // Deduplicate conversations - server conversations take precedence over synthetic ones
  const all = useMemo(() => {
    const serverConvs = conversations.map((c) => ({
      id: c.id,
      other_user: c.other_user,
    }));
    const serverConvIds = new Set(serverConvs.map((c) => c.id));

    // Only include synthetic conversations that don't already exist as server conversations
    const uniqueSyntheticConvs = syntheticConvs.filter(
      (c) => !serverConvIds.has(c.id)
    );

    return [...serverConvs, ...uniqueSyntheticConvs];
  }, [conversations, syntheticConvs]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Messages</h2>

        {/* New Chat Composer */}
        <div className="space-y-3">
          <input
            type="text"
            placeholder="Start chat with username..."
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
          />
          <button
            disabled={!recipient.trim()}
            onClick={() => {
              setOpenConversationId(
                [currentUser.username, recipient.trim()].sort().join(":")
              );
              setRecipient("");
            }}
            className="w-full bg-blue-600 text-white py-2 px-3 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all text-sm"
          >
            Start Chat
          </button>
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {all.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <p className="text-sm">No conversations yet</p>
            <p className="text-xs mt-1">Start a new chat above</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {all.map((c) => (
              <button
                key={c.id}
                onClick={() => setOpenConversationId(c.id)}
                className="w-full p-4 text-left hover:bg-gray-50 transition-colors focus:bg-gray-50 focus:outline-none"
              >
                <div className="flex items-center space-x-3">
                  {/* Avatar */}
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
                    {c.other_user.charAt(0).toUpperCase()}
                  </div>

                  {/* Chat Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {c.other_user}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Click to open chat
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
