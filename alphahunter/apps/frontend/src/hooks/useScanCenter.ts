/**
 * useScanCenter — shared scan state hook.
 *
 * Responsibilities
 * ----------------
 * - Load the latest scan on mount.
 * - Auto-poll every 3 s while a scan is in the "running" state.
 * - Expose triggerScan() and refreshLatest() for manual control.
 */
import { useEffect, useState } from "react";
import { api, type ScanSummary } from "../api/client";

interface ScanCenterState {
  latestScan: ScanSummary | null;
  loading: boolean;
  error: string;
  /** Start a new scan. Returns the new scan_run_id, or null on failure. */
  triggerScan: () => Promise<string | null>;
  /** Force-refresh the latest scan summary from the server. */
  refreshLatest: () => Promise<void>;
}

export function useScanCenter(): ScanCenterState {
  const [latestScan, setLatestScan] = useState<ScanSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeScanId, setActiveScanId] = useState<string | null>(null);

  // ── Initial load ─────────────────────────────────────────────────────────────

  useEffect(() => {
    let cancelled = false;

    const loadLatest = async () => {
      try {
        const response = await api.getLatestScan();
        if (cancelled) return;
        setLatestScan(response.data);
        setError("");
        if (response.data?.status === "running") {
          setActiveScanId(response.data.scan_run_id);
        }
      } catch (scanError) {
        if (cancelled) return;
        setError(scanError instanceof Error ? scanError.message : "Unable to load scan status.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadLatest();
    return () => { cancelled = true; };
  }, []);

  // ── Active-scan polling (3 s interval while running) ─────────────────────────

  useEffect(() => {
    if (!activeScanId) return;

    let cancelled = false;
    const intervalId = window.setInterval(() => {
      void (async () => {
        try {
          const response = await api.getScanStatus(activeScanId);
          if (cancelled) return;
          setLatestScan(response.data);
          if (response.data.status !== "running") setActiveScanId(null);
        } catch (scanError) {
          if (cancelled) return;
          setError(scanError instanceof Error ? scanError.message : "Unable to refresh scan status.");
          setActiveScanId(null);
        }
      })();
    }, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [activeScanId]);

  // ── Exposed actions ───────────────────────────────────────────────────────────

  const refreshLatest = async () => {
    setLoading(true);
    try {
      const response = await api.getLatestScan();
      setLatestScan(response.data);
      setError("");
      if (response.data?.status === "running") {
        setActiveScanId(response.data.scan_run_id);
      }
    } catch (scanError) {
      setError(scanError instanceof Error ? scanError.message : "Unable to load scan status.");
    } finally {
      setLoading(false);
    }
  };

  const triggerScan = async () => {
    const response = await api.triggerScan();
    const scanId = response.data.scan_run_id;
    setLatestScan({
      id: 0,
      scan_run_id: scanId,
      triggered_by: "manual",
      status: response.data.status,
      started_at: response.data.started_at,
      completed_at: null,
      duration_secs: null,
      stocks_scanned: 0,
      signals_found: 0,
      error_message: null,
    });
    setActiveScanId(scanId);
    return scanId;
  };

  return { latestScan, loading, error, triggerScan, refreshLatest };
}
