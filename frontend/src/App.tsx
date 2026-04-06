import { AppStateProvider, useAppState } from "./state/appState";
import { Onboarding } from "./components/Onboarding";
import { ConversationList } from "./components/ConversationList";
import { ConversationView } from "./components/ConversationView";

function Shell() {
  const { currentUser } = useAppState();
  return (
    <div className="min-h-screen bg-gray-50">
      {!currentUser && (
        <div className="flex items-center justify-center min-h-screen">
          <Onboarding />
        </div>
      )}
      {currentUser && (
        <div className="flex h-screen">
          <div className="w-1/3 min-w-80 border-r border-gray-200 bg-white">
            <ConversationList />
          </div>
          <div className="flex-1 bg-white">
            <ConversationView />
          </div>
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
