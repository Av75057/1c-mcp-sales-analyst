import React from 'react';

interface SuggestionChipsProps {
  suggestions: string[];
  onClick: (suggestion: string) => void;
}

export const SuggestionChips: React.FC<SuggestionChipsProps> = React.memo(({ suggestions, onClick }) => {
  if (!suggestions?.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {suggestions.map((s, idx) => (
        <button key={idx} onClick={() => onClick(s)}
          className="text-xs px-2.5 py-1 rounded-full border transition-colors"
          style={{ borderColor: 'var(--brand)', color: 'var(--brand)' }}>
          {s}
        </button>
      ))}
    </div>
  );
});

SuggestionChips.displayName = 'SuggestionChips';
