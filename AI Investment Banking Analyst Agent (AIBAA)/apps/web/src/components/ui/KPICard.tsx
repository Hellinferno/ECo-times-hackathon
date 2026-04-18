import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface Props {
  label: string;
  value: string | number;
  trend?: 'up' | 'down' | 'neutral';
  trendLabel?: string;
  delay?: number;
}

export default function KPICard({ label, value, trend, trendLabel, delay = 0 }: Props) {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'var(--positive)' : trend === 'down' ? 'var(--negative)' : 'var(--text-muted)';

  return (
    <div
      className="glass-card"
      style={{
        padding: '20px 24px',
        animation: `fadeInUp 0.3s ease ${delay}ms both`,
      }}
    >
      <div
        style={{
          fontSize: 10,
          fontWeight: 500,
          color: 'var(--text-muted)',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          marginBottom: 12,
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        {label}
      </div>

      <div className="flex items-end justify-between gap-4">
        <div
          style={{
            fontSize: 32,
            fontWeight: 300,
            color: 'var(--text-primary)',
            lineHeight: 1,
            letterSpacing: '-0.03em',
          }}
        >
          {value}
        </div>

        {trend && (
          <div className="flex items-center gap-1.5" style={{ marginBottom: 4 }}>
            <TrendIcon size={12} color={trendColor} />
            {trendLabel && (
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 500,
                  color: trendColor,
                  fontFamily: "'JetBrains Mono', monospace",
                }}
              >
                {trendLabel}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
