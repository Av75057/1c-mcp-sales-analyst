import { useState, useEffect } from 'react';
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
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    onLoadSessions();
  }, []);

  const handleClick = (id: string, e: React.MouseEvent) => {
    if (e.shiftKey) {
      setSelectedIds((prev) => {
        const next = new Set(prev);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        return next;
      });
    } else {
      setSelectedIds(new Set());
      onLoadMessages(id);
    }
  };

  const handleDeleteSelected = () => {
    if (selectedIds.size === 0) return;
    const msg = selectedIds.size === 1
      ? 'Удалить этот чат?'
      : `Удалить ${selectedIds.size} чатов?`;
    if (!confirm(msg)) return;
    selectedIds.forEach((id) => onDeleteSession(id));
    setSelectedIds(new Set());
  };

  const clearSelection = () => setSelectedIds(new Set());

  return (
    <div className="w-64 border-r border-[#2d3139] pr-3 flex flex-col h-full">
      <div className="flex gap-2 mb-3">
        <Button size="sm" onClick={onNewSession} className="flex-1">+ Новый чат</Button>
      </div>

      {selectedIds.size > 0 && (
        <div className="flex items-center gap-2 mb-2 px-1">
          <button onClick={handleDeleteSelected} className="text-xs text-error hover:text-error/80 transition-colors">
            ✕ Удалить {selectedIds.size}
          </button>
          <button onClick={clearSelection} className="text-xs text-[#6b7280] hover:text-white transition-colors">
            Отмена
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-1">
        {sessions.map((s) => {
          const isSelected = selectedIds.has(s.id);
          return (
            <div
              key={s.id}
              className={`group flex items-center rounded-lg text-sm transition-colors ${
                isSelected
                  ? 'bg-error/10 border border-error/30 text-white'
                  : s.id === currentSessionId && selectedIds.size === 0
                    ? 'bg-brand-500/20 text-white border border-brand-500/30'
                    : 'text-[#9ca3af] hover:bg-[#22262e] hover:text-white'
              }`}
            >
              <button
                onClick={(e) => handleClick(s.id, e)}
                className="flex-1 text-left px-3 py-2 min-w-0"
              >
                <div className="truncate font-medium">{s.title || 'Новый чат'}</div>
                <div className="text-xs text-[#6b7280] mt-0.5">
                  {s.message_count} сообщ. · {formatDate(s.created_at)}
                </div>
              </button>
              {isSelected && <span className="text-error text-xs px-2">✓</span>}
              {!isSelected && (
                <button
                  onClick={(e) => { e.stopPropagation(); if (confirm('Удалить чат?')) onDeleteSession(s.id); }}
                  className="p-2 opacity-0 group-hover:opacity-100 hover:text-error transition-opacity shrink-0"
                  title="Удалить (Shift+клик для множественного выбора)"
                >
                  ✕
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
