/**
 * Shared low-level utilities.
 *
 * cx    — conditional class-name joiner (Tailwind-friendly alternative to clsx)
 * clamp — numeric range clamping
 */

export function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}
