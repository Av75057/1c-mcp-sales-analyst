import { useChatWebSocket } from '../hooks/useWebSocket';
import { ChatWindow } from '../components/ChatWindow';
import { ChatSidebar } from '../components/ChatSidebar';

export default function ChatPage() {
  const { sendMessage, loadSessions, loadMessages, newSession } = useChatWebSocket();

  return (
    <div className="flex h-[calc(100vh-3rem)] gap-4">
      <ChatSidebar
        onLoadSessions={loadSessions}
        onLoadMessages={loadMessages}
        onNewSession={newSession}
      />
      <div className="flex-1 flex flex-col">
        <div className="mb-3">
          <h1 className="text-xl font-bold text-white">💬 AI Чат</h1>
          <p className="text-sm text-[#6b7280]">Аналитик продаж и склада на базе 1С + DeepSeek</p>
        </div>
        <ChatWindow onSendMessage={sendMessage} />
      </div>
    </div>
  );
}
