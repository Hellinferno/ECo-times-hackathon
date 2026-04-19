/**
 * Shared number and string formatting utilities.
 *
 * Previously duplicated across DCFResultsView.tsx and LBOResultsView.tsx.
 * Import from here instead of defining locally.
 */

/**
 * Format a number with Indian locale (en-IN) short suffixes.
 * Returns '-' for null/undefined, string-passthrough for NaN.
 */
export function fmt(n: number | unknown, decimals = 0): string {
    if (n === null || n === undefined || n === '') return '—'
    const num = Number(n)
    if (isNaN(num)) return String(n)
    if (Math.abs(num) >= 1e9) return `${(num / 1e9).toFixed(1)}B`
    if (Math.abs(num) >= 1e7) return `${(num / 1e7).toFixed(1)} Cr`
    if (Math.abs(num) >= 1e5) return `${(num / 1e5).toFixed(1)}L`
    if (decimals === 0) return num.toLocaleString('en-IN', { maximumFractionDigits: 0 })
    return num.toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

/**
 * Format a decimal fraction as a percentage string (e.g. 0.125 → "12.5%").
 */
export function pct(n: number | null | undefined): string {
    if (n === null || n === undefined) return '—'
    return `${(n * 100).toFixed(1)}%`
}

/**
 * Format a number with a currency prefix.
 * Default prefix is 'Rs ' for Indian Rupee display.
 */
export function currency(n: number | null | undefined, cur = 'Rs '): string {
    if (n === null || n === undefined) return '—'
    return `${cur}${fmt(n, 2)}`
}

/**
 * Format a multiple (e.g. 12.5 → "12.50x").
 */
export function multiple(n: number | unknown): string {
    if (n === null || n === undefined) return '—'
    return `${fmt(Number(n), 2)}x`
}

/**
 * Convert snake_case / underscore labels to Title Case.
 * Also normalises common finance abbreviations (WACC, TGR).
 */
export function titleCase(label: string): string {
    return label
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase())
        .replace('Tgr', 'TGR')
        .replace('Wacc', 'WACC')
        .replace('Irr', 'IRR')
        .replace('Moic', 'MOIC')
        .replace('Ebitda', 'EBITDA')
        .replace('Ev/', 'EV/')
}
