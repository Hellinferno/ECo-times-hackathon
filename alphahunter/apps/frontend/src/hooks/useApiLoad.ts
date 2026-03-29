import { useEffect, useState } from "react";
import type { ApiResponse } from "../api/client";

/**
 * Thin wrapper around the standard cancelled-flag async fetch pattern.
 *
 * Replaces the identical 20-line useEffect block that previously appeared
 * in every page component. Pages that need multiple concurrent fetches,
 * conditional branches, or complex waterfall logic should continue to use
 * useEffect directly.
 *
 * `refresh()` forces a re-fetch without changing any of the external deps.
 */
export function useApiLoad<T>(
  fetcher: () => Promise<ApiResponse<T>>,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  deps: readonly any[],
): { data: T | null; loading: boolean; error: string; refresh: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rev, setRev] = useState(0);

  const refresh = () => setRev((r) => r + 1);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetcher()
      .then((res) => {
        if (!cancelled) {
          setData(res.data);
          setError("");
        }
      })
      .catch((err: unknown) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Request failed.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, rev]);

  return { data, loading, error, refresh };
}
