import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { useDashboardFilterStore } from '../stores/dashboardFilterStore';

interface MobileFilterSheetProps {
  isOpen: boolean;
  onClose: () => void;
  filterField: string;
  options: { label: string; value: string }[];
}

export const MobileFilterSheet: React.FC<MobileFilterSheetProps> = ({ isOpen, onClose, filterField, options }) => {
  const setCrossFilter = useDashboardFilterStore((s) => s.setCrossFilter);

  useEffect(() => {
    if (isOpen) document.body.style.overflow = 'hidden';
    else document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40" />
      <div onClick={(e) => e.stopPropagation()}
        className="relative w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5 max-h-[60vh] overflow-y-auto"
        style={{ backgroundColor: 'var(--bg-card)' }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Фильтр: {filterField}</h3>
          <button onClick={onClose} className="p-1 rounded" style={{ color: 'var(--text-muted)' }}><X className="w-5 h-5" /></button>
        </div>
        <div className="space-y-1">
          {options.map((opt) => (
            <button key={opt.value} onClick={() => { setCrossFilter({ widgetId: `mobile-${filterField}`, field: filterField, value: opt.value, label: `${filterField}: ${opt.value}` }); onClose(); }}
              className="w-full text-left px-4 py-3 rounded-lg text-sm transition-colors"
              style={{ color: 'var(--text-primary)' }}
              onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'}
              onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}>
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
