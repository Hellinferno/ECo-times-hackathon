import { useState, useEffect, useCallback, useRef } from 'react'
import { fetchWMHealth } from '../lib/api'

interface UseWorldMonitorResult<T> {
    data: T | null
    loading: boolean
    connected: boolean
    refresh: () => void
}

/**
 * Shared hook for WorldMonitor data fetching.
 *
 * Handles the health-check + fetch + cancellation pattern used by
 * MacroContextPanel and RiskHeatmapPanel. Returns a `refresh` callback
 * so panels can add a manual refresh button.
 *
 * @param fetchFn   Async function that fetches panel data (called only when WM is connected).
 * @param deps      Additional deps to re-run the effect (default: none — manual refresh only).
 * @param refreshInterval  Optional auto-refresh interval in ms. Undefined = no auto-refresh.
 */
export function useWorldMonitor<T>(
    fetchFn: () => Promise<T>,
    deps: unknown[] = [],
    refreshInterval?: number,
): UseWorldMonitorResult<T> {
    const [data, setData] = useState<T | null>(null)
    const [loading, setLoading] = useState(true)
    const [connected, setConnected] = useState(false)
    const [tick, setTick] = useState(0)

    const fetchFnRef = useRef(fetchFn)
    fetchFnRef.current = fetchFn

    useEffect(() => {
        let cancelled = false

        async function load() {
            setLoading(true)
            try {
                const health = await fetchWMHealth()
                if (cancelled) return
                const isConnected = health.connected && health.enabled !== false
                setConnected(isConnected)

                if (!isConnected) {
                    setLoading(false)
                    return
                }

                const result = await fetchFnRef.current()
                if (cancelled) return
                setData(result)
            } catch {
                if (!cancelled) setConnected(false)
            } finally {
                if (!cancelled) setLoading(false)
            }
        }

        load()
        return () => { cancelled = true }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [tick, ...deps])

    useEffect(() => {
        if (!refreshInterval) return
        const id = setInterval(() => setTick(t => t + 1), refreshInterval)
        return () => clearInterval(id)
    }, [refreshInterval])

    const refresh = useCallback(() => setTick(t => t + 1), [])

    return { data, loading, connected, refresh }
}
