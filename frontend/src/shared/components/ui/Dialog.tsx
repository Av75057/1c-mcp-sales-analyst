import { useEffect, useRef, type ReactNode } from 'react';
import { cn } from '@/shared/lib/utils';

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  className?: string;
}

export function Dialog({ open, onClose, title, children, className }: DialogProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (open) document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div className={cn('bg-[#1a1d23] border border-[#2d3139] rounded-xl p-6 w-full max-w-md mx-4 shadow-elevated', className)}>
        {title && <h2 className="text-lg font-semibold text-white mb-4">{title}</h2>}
        {children}
      </div>
    </div>
  );
}
