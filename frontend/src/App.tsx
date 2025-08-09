import "./App.css";
import { AppStateProvider, useAppState } from "./state/appState";
import { Onboarding } from "./components/Onboarding";
import { ConversationList } from "./components/ConversationList";
import { ConversationView } from "./components/ConversationView";

function Shell() {
  const { currentUser } = useAppState();
  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 16 }}>
      <h1>QChat</h1>
      {!currentUser && <Onboarding />}
      {currentUser && (
        <div
          style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 16 }}
        >
          <ConversationList />
          <ConversationView />
        </div>
      )}
    </div>
  );
}

export default function App() {
  return (
    <AppStateProvider>
      <Shell />
    </AppStateProvider>
  );
}
