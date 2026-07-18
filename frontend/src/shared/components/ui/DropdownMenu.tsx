import { useState, useRef, useEffect, type ReactNode } from 'react';
import { cn } from '@/shared/lib/utils';

interface DropdownMenuProps {
  trigger: ReactNode;
  children: ReactNode;
  align?: 'start' | 'end';
}

export function DropdownMenu({ trigger, children, align = 'end' }: DropdownMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    if (open) document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, [open]);

  return (
    <div ref={ref} className="relative inline-block">
      <div onClick={() => setOpen(!open)}>{trigger}</div>
      {open && (
        <div
          className={cn(
            'absolute top-full mt-1 z-50 min-w-[180px] border rounded-lg shadow-elevated py-1',
            align === 'end' ? 'right-0' : 'left-0'
          )}
          style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}
          onClick={() => setOpen(false)}
        >
          {children}
        </div>
      )}
    </div>
  );
}

export function DropdownMenuItem({
  children,
  onClick,
  danger,
}: {
  children: ReactNode;
  onClick?: () => void;
  danger?: boolean;
}) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left px-3 py-2 text-sm transition-colors',
        danger ? 'text-error' : ''
      )}
      style={{
        color: danger ? undefined : 'var(--text-primary)',
        backgroundColor: isHovered ? 'var(--bg-card-hover)' : undefined,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {children}
    </button>
  );
}
