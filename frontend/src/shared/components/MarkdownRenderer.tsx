import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const lines = content.split('\n');

  return (
    <div style={{ color: 'var(--text-primary)' }} className="leading-relaxed text-sm">
      {lines.map((line, idx) => {
        if (line.startsWith('### ')) {
          return <h3 key={idx} className="text-base font-bold mt-3 mb-1">{line.slice(4)}</h3>;
        }
        if (line.startsWith('## ')) {
          return <h2 key={idx} className="text-lg font-bold mt-3 mb-1">{line.slice(3)}</h2>;
        }
        if (line.startsWith('# ')) {
          return <h1 key={idx} className="text-xl font-bold mt-3 mb-1">{line.slice(2)}</h1>;
        }
        if (line.startsWith('- ') || line.startsWith('* ')) {
          return <li key={idx} className="ml-4 mb-0.5">{inlineMarkdown(line.slice(2))}</li>;
        }
        if (/^\d+\.\s/.test(line)) {
          const c = line.replace(/^\d+\.\s/, '');
          return <li key={idx} className="ml-4 mb-0.5 list-decimal">{inlineMarkdown(c)}</li>;
        }
        if (line.trim() === '') {
          return <br key={idx} />;
        }
        return <p key={idx} className="mb-1">{inlineMarkdown(line)}</p>;
      })}
    </div>
  );
};

function inlineMarkdown(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={idx} className="font-semibold">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}
