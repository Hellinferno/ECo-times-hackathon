interface Props {
  label?: string;
}

export default function LoadingScreen({ label = 'Loading...' }: Props) {
  return (
    <div
      className="flex flex-col items-center justify-center animate-fade-in"
      style={{
        minHeight: '60vh',
        gap: 16,
      }}
    >
      {/* Animated spinner */}
      <div style={{ position: 'relative', width: 40, height: 40 }}>
        <div
          className="spinner"
          style={{
            width: 40,
            height: 40,
            borderWidth: 2,
            borderColor: 'var(--border-primary)',
            borderTopColor: 'var(--accent)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 6,
            border: '2px solid transparent',
            borderTopColor: 'var(--accent-light)',
            borderRadius: '50%',
            animation: 'spin 1.2s linear infinite reverse',
          }}
        />
      </div>

      <span
        style={{
          fontSize: 11,
          fontWeight: 500,
          color: 'var(--text-muted)',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        {label}
      </span>
    </div>
  );
}
