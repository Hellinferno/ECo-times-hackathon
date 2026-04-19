/**
 * Design token constants — single source of truth for inline styles.
 *
 * These map to the CSS variables defined in index.css. Use these in
 * components that need dynamic/conditional inline styling instead of
 * hardcoding color strings directly.
 */

export const COLORS = {
  // Backgrounds
  bgVoid:     'var(--bg-void)',
  bgPrimary:  'var(--bg-primary)',
  bgSurface:  'var(--bg-surface)',
  bgElevated: 'var(--bg-elevated)',
  bgCard:     'var(--bg-card)',
  bgInput:    'var(--bg-input)',
  bgHover:    'var(--bg-hover)',

  // Borders
  border:       'var(--border-primary)',
  borderSubtle: 'var(--border-subtle)',
  borderFocus:  'var(--border-focus)',

  // Text
  textPrimary:   'var(--text-primary)',
  textSecondary: 'var(--text-secondary)',
  textMuted:     'var(--text-muted)',
  textAccent:    'var(--text-accent)',

  // Semantic
  positive:       'var(--positive)',
  positiveBg:     'var(--positive-bg)',
  positiveBorder: 'var(--positive-border)',
  negative:       'var(--negative)',
  negativeBg:     'var(--negative-bg)',
  negativeBorder: 'var(--negative-border)',
  warning:        'var(--warning)',
  warningBg:      'var(--warning-bg)',
  warningBorder:  'var(--warning-border)',
  info:           'var(--info)',
  infoBg:         'var(--info-bg)',
  infoBorder:     'var(--info-border)',

  // Accent
  accent:     'var(--accent)',
  accentLight: 'var(--accent-light)',
} as const;

export const RADIUS = {
  sm: 'var(--radius-sm)',
  md: 'var(--radius-md)',
  lg: 'var(--radius-lg)',
  xl: 'var(--radius-xl)',
} as const;

export const SHADOW = {
  sm: 'var(--shadow-sm)',
  md: 'var(--shadow-md)',
  lg: 'var(--shadow-lg)',
} as const;

export const FONT_SIZE = {
  xs:   '10px',
  sm:   '11px',
  base: '13px',
  md:   '14px',
  lg:   '16px',
  xl:   '20px',
  xxl:  '24px',
} as const;

export const SPACING = {
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '24px',
  xxl: '32px',
} as const;
