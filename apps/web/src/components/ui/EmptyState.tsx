import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';

interface Props {
  icon?: ReactNode;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}

export default function EmptyState({ icon, title, subtitle, action }: Props) {
  return (
    <div
      className="flex flex-col items-center justify-center py-20 animate-fade-in-up"
      style={{
        border: '1px dashed var(--border-primary)',
        borderRadius: 'var(--radius-md)',
        background: 'var(--bg-glass)',
      }}
    >
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 'var(--radius-md)',
          background: 'var(--accent-glow)',
          border: '1px solid rgba(99, 130, 255, 0.12)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--accent-light)',
          marginBottom: 16,
        }}
      >
        {icon || <Inbox size={22} />}
      </div>

      <div
        style={{
          fontSize: 15,
          fontWeight: 600,
          color: 'var(--text-primary)',
          marginBottom: 6,
        }}
      >
        {title}
      </div>

      {subtitle && (
        <div
          style={{
            fontSize: 13,
            color: 'var(--text-muted)',
            maxWidth: 320,
            textAlign: 'center',
            lineHeight: 1.5,
            marginBottom: action ? 16 : 0,
          }}
        >
          {subtitle}
        </div>
      )}

      {action}
    </div>
  );
}
