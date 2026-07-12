import { useEffect } from 'react';
import { useChatStore } from '../stores/chatStore';
import { Button } from '@/shared/components/ui/Button';
import { formatDate } from '@/shared/lib/utils';

interface ChatSidebarProps {
  onLoadSessions: () => void;
  onLoadMessages: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onNewSession: () => void;
}

export function ChatSidebar({ onLoadSessions, onLoadMessages, onDeleteSession, onNewSession }: ChatSidebarProps) {
  const { sessions, currentSessionId } = useChatStore();

  useEffect(() => {
    onLoadSessions();
  }, []);

  return (
    <div className="w-64 border-r border-[#2d3139] pr-3 flex flex-col h-full">
      <div className="flex gap-2 mb-3">
        <Button size="sm" onClick={onNewSession} className="flex-1">+ Новый чат</Button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-1">
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`group flex items-center rounded-lg text-sm transition-colors ${
              s.id === currentSessionId
                ? 'bg-brand-500/20 text-white border border-brand-500/30'
                : 'text-[#9ca3af] hover:bg-[#22262e] hover:text-white'
            }`}
          >
            <button
              onClick={() => onLoadMessages(s.id)}
              className="flex-1 text-left px-3 py-2 min-w-0"
            >
              <div className="truncate font-medium">{s.title || 'Новый чат'}</div>
              <div className="text-xs text-[#6b7280] mt-0.5">
                {s.message_count} сообщ. · {formatDate(s.created_at)}
              </div>
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); if (confirm('Удалить чат?')) onDeleteSession(s.id); }}
              className="p-2 opacity-0 group-hover:opacity-100 hover:text-error transition-opacity shrink-0"
              title="Удалить"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
