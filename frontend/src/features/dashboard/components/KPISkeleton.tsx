import React from 'react';

export const KPISkeleton: React.FC = React.memo(() => (
  <div className="rounded-xl border p-4 animate-pulse" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
    <div className="h-4 rounded w-1/3 mb-3" style={{ backgroundColor: 'var(--skeleton)' }} />
    <div className="h-8 rounded w-2/3 mb-4" style={{ backgroundColor: 'var(--skeleton)' }} />
    <div className="flex justify-between items-center">
      <div className="h-4 rounded w-1/4" style={{ backgroundColor: 'var(--skeleton)' }} />
      <div className="h-8 rounded w-16" style={{ backgroundColor: 'var(--skeleton)' }} />
    </div>
  </div>
));

KPISkeleton.displayName = 'KPISkeleton';
