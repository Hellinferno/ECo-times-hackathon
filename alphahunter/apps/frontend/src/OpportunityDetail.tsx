import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Target, ShieldAlert, Binary, MessageSquare, Zap } from 'lucide-react';
import { api } from './api/client';
import type { OpportunityDetail as OpportunityDetailResponse } from './api/client';

function OpportunityDetail() {
  const { id } = useParams();
  const [data, setData] = useState<OpportunityDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) {
      setError("Opportunity not found.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    api
      .getOpportunityDetail(id)
      .then((res) => setData(res.data))
      .catch((err: Error) => setError(err.message || "Failed to load opportunity."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center py-20 text-gray-400">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-center py-20 text-red-400">{error}</div>;
  }

  if (!data) {
    return <div className="text-center py-20 text-gray-400">Opportunity not found.</div>;
  }

  const { decision, signals, reasoning } = data;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      <Link to="/" className="inline-flex items-center text-gray-400 hover:text-white transition-colors">
        <ArrowLeft size={20} className="mr-2" /> Back to Dashboard
      </Link>

      <div className="bg-gray-800 p-8 rounded-xl shadow-lg border border-gray-700 relative overflow-hidden">
        <div className={`absolute top-0 left-0 w-2 h-full ${decision.action === 'BUY' ? 'bg-green-500' : 'bg-yellow-500'}`} />
        
        <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-gray-700 pb-6 mb-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-4xl font-black text-white">{decision.symbol}</h1>
              <span className={`px-3 py-1 text-sm font-black tracking-wider rounded-lg ${ 
                  decision.action === 'BUY' ? 'bg-green-900/50 text-green-400' : 'bg-yellow-900/50 text-yellow-400'
              }`}>
                  {decision.action}
              </span>
            </div>
            <p className="text-gray-400 mt-2 flex items-center gap-2">
              <ClockIcon size={16} /> Extracted {new Date(decision.timestamp).toLocaleString()}
            </p>
          </div>
          
          <div className="flex gap-4">
            <div className="text-center bg-gray-900 px-6 py-3 rounded-lg border border-gray-700">
              <span className="block text-gray-500 text-xs font-bold uppercase tracking-wider">Confidence</span>
              <span className="text-2xl font-mono font-black text-blue-400">{decision.confidence}%</span>
            </div>
            <div className="text-center bg-gray-900 px-6 py-3 rounded-lg border border-gray-700">
              <span className="block text-gray-500 text-xs font-bold uppercase tracking-wider">RR Ratio</span>
              <span className="text-2xl font-mono font-black text-purple-400">{decision.rr_ratio}x</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-900 p-5 rounded-xl border border-gray-700 flex items-start gap-4">
            <div className="bg-blue-900/30 p-3 rounded-lg"><Zap className="text-blue-400" size={24} /></div>
            <div>
              <p className="text-gray-500 text-sm font-medium">Entry Price</p>
              <p className="text-2xl font-mono text-white">₹{decision.entry_price}</p>
            </div>
          </div>
          <div className="bg-gray-900 p-5 rounded-xl border border-green-900/30 flex items-start gap-4">
            <div className="bg-green-900/30 p-3 rounded-lg"><Target className="text-green-400" size={24} /></div>
            <div>
              <p className="text-green-500/70 text-sm font-medium">Target Price</p>
              <p className="text-2xl font-mono text-green-400">₹{decision.target}</p>
            </div>
          </div>
          <div className="bg-gray-900 p-5 rounded-xl border border-red-900/30 flex items-start gap-4">
            <div className="bg-red-900/30 p-3 rounded-lg"><ShieldAlert className="text-red-400" size={24} /></div>
            <div>
              <p className="text-red-500/70 text-sm font-medium">Stop Loss</p>
              <p className="text-2xl font-mono text-red-400">₹{decision.stop_loss}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Signal Breakdown */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold flex items-center gap-2 text-gray-200">
              <Binary size={20} className="text-blue-400"/> Quantitative Signals
            </h3>
            <div className="bg-gray-900 rounded-xl p-5 border border-gray-700 space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-gray-800">
                <span className="text-gray-300">Breakout Triggered</span>
                <span className={signals.breakout ? "text-green-400 font-bold" : "text-gray-500"}>
                  {signals.breakout ? "YES" : "NO"}
                </span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b border-gray-800">
                <span className="text-gray-300">Volume Spike</span>
                <span className={signals.volume ? "text-green-400 font-bold" : "text-gray-500"}>
                  {signals.volume ? `YES (${signals.volume_details?.volume_ratio}x)` : "NO"}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-300">Bulk Deal Supported</span>
                <span className={signals.bulk ? "text-green-400 font-bold" : "text-gray-500"}>
                  {signals.bulk ? "YES" : "NO"}
                </span>
              </div>
            </div>
          </div>

          {/* AI Reasoning */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold flex items-center gap-2 text-gray-200">
              <MessageSquare size={20} className="text-emerald-400"/> LLM Rationale
            </h3>
            <div className="bg-gray-900 rounded-xl p-5 border border-gray-700">
              <p className="text-gray-300 leading-relaxed">
                {reasoning.llm_summary || "No textual reasoning recorded."}
              </p>
              
              {reasoning.key_factors && (
                <div className="mt-4">
                  <h4 className="text-sm font-semibold text-gray-400 mb-2">Key Factors:</h4>
                  <ul className="list-disc pl-5 text-sm text-emerald-400/80 space-y-1">
                    {reasoning.key_factors.map((f: string, i: number) => <li key={i}>{f}</li>)}
                  </ul>
                </div>
              )}
              {reasoning.risk_warnings && (
                <div className="mt-4 pt-4 border-t border-gray-800">
                  <h4 className="text-sm font-semibold text-gray-400 mb-2">Risk Warnings:</h4>
                  <ul className="list-disc pl-5 text-sm text-red-400/80 space-y-1">
                    {reasoning.risk_warnings.map((f: string, i: number) => <li key={i}>{f}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ClockIcon(props: any) {
  return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinelinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>;
}

export default OpportunityDetail;
