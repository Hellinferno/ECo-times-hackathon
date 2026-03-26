import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "./api/client";
import type { AlertEntry } from "./api/client";
import { Bell, CheckCheck, Eye } from "lucide-react";

export default function Alerts() {
  const [alerts, setAlerts] = useState<AlertEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  const fetchAlerts = (unreadOnly: boolean) => {
    setLoading(true);
    api
      .getAlerts(unreadOnly)
      .then((res) => setAlerts(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchAlerts(filter === "unread");
  }, [filter]);

  const markAllRead = async () => {
    try {
      await api.markAlertsRead();
      setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
    } catch (e) {
      console.error(e);
    }
  };

  const unreadCount = alerts.filter((a) => !a.is_read).length;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-black text-white flex items-center gap-2">
          <Bell className="text-blue-400" size={24} />
          Alerts
          {unreadCount > 0 && (
            <span className="bg-blue-600 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              {unreadCount}
            </span>
          )}
        </h1>
        <div className="flex gap-2">
          <div className="flex bg-gray-800 rounded-lg p-0.5 border border-gray-700">
            <button
              onClick={() => setFilter("all")}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                filter === "all"
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter("unread")}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                filter === "unread"
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              Unread
            </button>
          </div>
          {unreadCount > 0 && (
            <button
              onClick={markAllRead}
              className="flex items-center gap-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 px-3 py-1.5 rounded-lg text-sm transition-colors"
            >
              <CheckCheck size={14} />
              Mark all read
            </button>
          )}
        </div>
      </div>

      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-10">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <Bell size={40} className="mx-auto mb-3 opacity-30" />
            <p className="font-medium">No alerts</p>
            <p className="text-sm mt-1">
              Alerts will appear here when the system detects opportunities
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-700/50">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`px-5 py-4 flex items-start gap-4 transition-colors ${
                  alert.is_read ? "opacity-60" : "bg-gray-800"
                }`}
              >
                <div
                  className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${
                    alert.is_read ? "bg-gray-600" : "bg-blue-500"
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Link
                      to={`/stock/${alert.symbol}`}
                      className="font-bold text-white hover:text-blue-400 transition-colors"
                    >
                      {alert.symbol}
                    </Link>
                    {alert.action && (
                      <span
                        className={`px-2 py-0.5 text-xs font-bold rounded ${
                          alert.action === "BUY"
                            ? "bg-green-900/50 text-green-400"
                            : alert.action === "WATCH"
                            ? "bg-yellow-900/50 text-yellow-400"
                            : "bg-red-900/50 text-red-400"
                        }`}
                      >
                        {alert.action}
                      </span>
                    )}
                    <span className="text-xs bg-gray-700 text-gray-400 px-2 py-0.5 rounded">
                      {alert.alert_type}
                    </span>
                  </div>
                  <p className="text-gray-300 text-sm">{alert.message}</p>
                  <p className="text-gray-500 text-xs mt-1">
                    {new Date(alert.created_at).toLocaleString()}
                    {alert.confidence != null && (
                      <span className="ml-2 text-blue-400">
                        {alert.confidence}% confidence
                      </span>
                    )}
                  </p>
                </div>
                <Link
                  to={`/stock/${alert.symbol}`}
                  className="text-gray-400 hover:text-blue-400 transition-colors p-1 flex-shrink-0"
                >
                  <Eye size={16} />
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
