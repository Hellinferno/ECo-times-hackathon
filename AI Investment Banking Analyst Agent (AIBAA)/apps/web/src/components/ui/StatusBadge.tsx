interface Props {
  variant?: 'default' | 'positive' | 'warning' | 'negative' | 'accent';
  children: React.ReactNode;
  dot?: boolean;
}

const VARIANT_STYLES: Record<string, { bg: string; border: string; color: string; dotColor: string }> = {
  default: {
    bg: 'var(--bg-surface)',
    border: 'var(--border-primary)',
    color: 'var(--text-secondary)',
    dotColor: 'var(--text-muted)',
  },
  positive: {
    bg: 'var(--positive-bg)',
    border: 'var(--positive-border)',
    color: 'var(--positive)',
    dotColor: 'var(--positive)',
  },
  warning: {
    bg: 'var(--warning-bg)',
    border: 'var(--warning-border)',
    color: 'var(--warning)',
    dotColor: 'var(--warning)',
  },
  negative: {
    bg: 'var(--negative-bg)',
    border: 'var(--negative-border)',
    color: 'var(--negative)',
    dotColor: 'var(--negative)',
  },
  accent: {
    bg: 'rgba(99, 130, 255, 0.08)',
    border: 'rgba(99, 130, 255, 0.25)',
    color: 'var(--accent-light)',
    dotColor: 'var(--accent)',
  },
};

export default function StatusBadge({ variant = 'default', children, dot = false }: Props) {
  const s = VARIANT_STYLES[variant] || VARIANT_STYLES.default;

  return (
    <span
      className="badge"
      style={{
        background: s.bg,
        borderColor: s.border,
        color: s.color,
      }}
    >
      {dot && (
        <span
          style={{
            width: 5,
            height: 5,
            borderRadius: '50%',
            background: s.dotColor,
            display: 'inline-block',
            boxShadow: `0 0 6px ${s.dotColor}`,
          }}
        />
      )}
      {children}
    </span>
  );
}
