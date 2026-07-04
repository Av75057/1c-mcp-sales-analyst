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
            'absolute top-full mt-1 z-50 min-w-[180px] bg-[#1a1d23] border border-[#2d3139] rounded-lg shadow-elevated py-1',
            align === 'end' ? 'right-0' : 'left-0'
          )}
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
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left px-3 py-2 text-sm transition-colors hover:bg-[#22262e]',
        danger ? 'text-error hover:text-error' : 'text-[#e5e7eb]'
      )}
    >
      {children}
    </button>
  );
}
