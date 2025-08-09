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
  const all = [
    ...conversations.map((c) => ({ id: c.id, other_user: c.other_user })),
    ...syntheticConvs,
  ];

  return (
    <div className="conv-list">
      <div className="compose">
        <input
          placeholder="Start chat with username"
          value={recipient}
          onChange={(e) => setRecipient(e.target.value)}
        />
        <button
          disabled={!recipient.trim()}
          onClick={() => {
            setOpenConversationId(
              [currentUser.username, recipient.trim()].sort().join(":")
            );
            setRecipient("");
          }}
        >
          Open
        </button>
      </div>

      <h3>Conversations</h3>
      <ul>
        {all.map((c) => (
          <li key={c.id}>
            <button onClick={() => setOpenConversationId(c.id)}>
              {c.other_user}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
