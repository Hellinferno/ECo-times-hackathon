import { useState, useEffect, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { fetchDeals, createDeal, deleteDeal, type Deal, type DealCreatePayload } from '../lib/api'
import { Plus, Search, Trash2, X, Settings, ArrowUpRight } from 'lucide-react'

const DEAL_TYPES: { label: string; value: string }[] = [
    { label: 'M&A',          value: 'ma' },
    { label: 'IPO',          value: 'ipo' },
    { label: 'LBO',          value: 'lbo' },
    { label: 'Debt Raise',   value: 'debt_raise' },
    { label: 'Equity Raise', value: 'equity_raise' },
    { label: 'Restructuring',value: 'restructuring' },
    { label: 'Other',        value: 'other' },
]
const INDUSTRIES = ['Technology', 'Healthcare', 'Financial Services', 'Consumer', 'Energy', 'Industrials', 'Real Estate', 'Telecom', 'Other']

export default function Dashboard() {
    const navigate = useNavigate()
    const [deals, setDeals] = useState<Deal[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [showModal, setShowModal] = useState(false)
    const [form, setForm] = useState<DealCreatePayload>({
        name: '', company_name: '', deal_type: 'ma', industry: 'Technology', deal_stage: 'preliminary'
    })
    const [creating, setCreating] = useState(false)
    const [createError, setCreateError] = useState<string | null>(null)

    const load = useCallback(async () => {
        try {
            const data = await fetchDeals()
            setDeals(data)
        } catch (err) {
            console.error('Failed to load deals', err)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => { load() }, [load])

    const handleCreate = async () => {
        if (!form.name.trim() || !form.company_name.trim()) return
        setCreating(true)
        setCreateError(null)
        try {
            const newDeal = await createDeal(form)
            setShowModal(false)
            setForm({ name: '', company_name: '', deal_type: 'ma', industry: 'Technology', deal_stage: 'preliminary' })
            setCreateError(null)
            navigate(`/deals/${newDeal.id}`)
        } catch (err: unknown) {
            const axErr = err as { response?: { data?: { detail?: string } }; message?: string }
            const msg = axErr?.response?.data?.detail || axErr?.message || 'Failed to create deal'
            setCreateError(typeof msg === 'string' ? msg : JSON.stringify(msg))
            console.error('Create deal failed', err)
        } finally {
            setCreating(false)
        }
    }

    const handleDelete = async (id: string) => {
        try {
            await deleteDeal(id)
            setDeals(prev => prev.filter(d => d.id !== id))
        } catch (err) {
            console.error('Delete failed', err)
        }
    }

    const filtered = deals.filter(d =>
        d.name.toLowerCase().includes(search.toLowerCase()) ||
        d.company_name.toLowerCase().includes(search.toLowerCase())
    )

    return (
        <div className="min-h-screen bg-black text-white p-6 md:p-12 font-sans selection:bg-white selection:text-black">
            <div className="max-w-[1400px] mx-auto">
                {/* Header */}
                <header className="flex flex-col md:flex-row md:items-end justify-between border-b border-neutral-800 pb-8 mb-10">
                    <div>
                        <h1 className="text-3xl font-medium tracking-tight text-white m-0">
                            AIBAA
                        </h1>
                        <p className="text-neutral-500 text-xs font-mono uppercase tracking-widest mt-2">
                            AI Investment Banking Analyst Agent
                        </p>
                    </div>
                    <div className="flex items-center gap-4 mt-6 md:mt-0">
                        <Link
                            to="/settings"
                            className="flex items-center gap-2 text-neutral-400 text-xs font-mono uppercase tracking-wider hover:text-white transition-colors border border-transparent hover:border-neutral-800 px-3 py-2"
                        >
                            <Settings size={14} /> Settings
                        </Link>
                        <button className="btn-primary group flex items-center gap-2" onClick={() => setShowModal(true)}>
                            <Plus size={14} className="group-hover:rotate-90 transition-transform duration-300" /> NEW DEAL
                        </button>
                    </div>
                </header>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-[1px] bg-neutral-800 border border-neutral-800 mb-10">
                    {[
                        { label: 'Total Deals', value: deals.length },
                        { label: 'Active Pipeline', value: deals.filter(d => d.deal_stage === 'preliminary' || d.deal_stage === 'active').length },
                        { label: 'Indexed Docs', value: deals.reduce((s, d) => s + (d.document_count || 0), 0) },
                        { label: 'AI Outputs', value: deals.reduce((s, d) => s + (d.output_count || 0), 0) },
                    ].map((stat, i) => (
                        <div key={i} className="bg-black p-6 flex flex-col justify-between group hover:bg-neutral-950 transition-colors">
                            <div className="text-neutral-500 text-[10px] uppercase font-mono tracking-widest mb-4">
                                {stat.label}
                            </div>
                            <div className="text-4xl font-light font-mono text-white tracking-tighter">
                                {stat.value}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Main Content Area */}
                <div className="flex flex-col md:flex-row justify-between items-end mb-6 border-b border-neutral-800 pb-4 gap-4">
                    <h2 className="text-lg font-medium tracking-tight">Deal Pipeline</h2>
                    <div className="relative w-full md:w-80">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" />
                        <input
                            className="w-full bg-black border border-neutral-800 text-sm font-mono text-white py-2 pl-9 pr-3 focus:border-white focus:outline-none transition-colors placeholder:text-neutral-600"
                            placeholder="Search pipeline..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                        />
                    </div>
                </div>

                {/* Deal List */}
                {loading ? (
                    <div className="py-20 flex flex-col items-center justify-center border border-neutral-800 border-dashed text-neutral-500">
                        <div className="spinner mb-4" />
                        <span className="font-mono text-xs uppercase tracking-widest">Loading Deals</span>
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="py-20 flex flex-col items-center justify-center border border-neutral-800 border-dashed text-neutral-500">
                        <p className="font-mono text-xs uppercase tracking-widest mb-2">No deals found</p>
                        <button onClick={() => setShowModal(true)} className="text-white text-sm hover:underline underline-offset-4 border-b border-transparent hover:border-white transition-all">Start a new deal</button>
                    </div>
                ) : (
                    <div className="border border-neutral-800 border-b-0">
                        {filtered.map((deal) => (
                            <div
                                key={deal.id}
                                onClick={() => navigate(`/deals/${deal.id}`)}
                                className="group flex flex-col md:flex-row md:items-center p-4 md:p-5 border-b border-neutral-800 hover:bg-neutral-900 cursor-pointer transition-colors"
                            >
                                <div className="flex-1 min-w-0 mb-4 md:mb-0">
                                    <div className="flex items-center gap-3 mb-1">
                                        <div className="text-base font-medium text-white truncate group-hover:underline underline-offset-4 decoration-neutral-600">{deal.name}</div>
                                    </div>
                                    <div className="text-sm text-neutral-500 truncate">{deal.company_name}</div>
                                </div>
                                <div className="flex flex-wrap md:flex-nowrap gap-3 items-center md:justify-end md:w-1/2">
                                    <span className="border border-neutral-700 text-neutral-400 text-[10px] tracking-widest uppercase px-2 py-0.5 font-mono whitespace-nowrap">
                                        {deal.deal_type}
                                    </span>
                                    <span className={`border ${deal.deal_stage === 'active' || deal.deal_stage === 'closed' ? 'border-white text-white' : 'border-neutral-700 text-neutral-400'} text-[10px] tracking-widest uppercase px-2 py-0.5 font-mono whitespace-nowrap`}>
                                        {deal.deal_stage}
                                    </span>
                                    <span className="text-[11px] text-neutral-600 font-mono whitespace-nowrap hidden md:block w-24 text-right">
                                        {new Date(deal.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                                    </span>
                                    <div className="flex items-center gap-1 ml-auto md:ml-4">
                                        <button
                                            className="p-2 text-neutral-600 hover:text-white hover:bg-neutral-800 transition-colors"
                                            onClick={e => { e.stopPropagation(); handleDelete(deal.id) }}
                                            title="Delete Deal"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                        <div className="p-2 text-neutral-600 group-hover:text-white transition-colors">
                                            <ArrowUpRight size={16} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Strict B&W Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-black border border-white w-full max-w-[500px]" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center p-5 border-b border-neutral-800">
                            <h2 className="text-sm font-mono tracking-widest uppercase text-white">Create New Deal</h2>
                            <button className="text-neutral-500 hover:text-white transition-colors" onClick={() => setShowModal(false)}>
                                <X size={18} />
                            </button>
                        </div>

                        <div className="p-6 space-y-6">
                            <div>
                                <label className="block text-[10px] text-neutral-500 font-mono uppercase tracking-widest mb-2">Deal Name *</label>
                                <input 
                                    className="w-full bg-black border border-neutral-800 text-sm font-mono text-white p-3 focus:border-white focus:outline-none transition-colors" 
                                    placeholder="Project Alpha" 
                                    value={form.name}
                                    onChange={e => setForm(p => ({ ...p, name: e.target.value }))} 
                                    autoFocus
                                />
                            </div>
                            <div>
                                <label className="block text-[10px] text-neutral-500 font-mono uppercase tracking-widest mb-2">Company Name *</label>
                                <input 
                                    className="w-full bg-black border border-neutral-800 text-sm font-mono text-white p-3 focus:border-white focus:outline-none transition-colors" 
                                    placeholder="Acme Corp" 
                                    value={form.company_name}
                                    onChange={e => setForm(p => ({ ...p, company_name: e.target.value }))} 
                                />
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] text-neutral-500 font-mono uppercase tracking-widest mb-2">Transaction Type</label>
                                    <select 
                                        className="w-full bg-black border border-neutral-800 text-sm font-mono text-white p-3 focus:border-white focus:outline-none appearance-none rounded-none transition-colors cursor-pointer" 
                                        value={form.deal_type}
                                        onChange={e => setForm(p => ({ ...p, deal_type: e.target.value }))}
                                        style={{ backgroundImage: 'url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23525252%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.4-12.8z%22%2F%3E%3C%2Fsvg%3E")', backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px top 50%', backgroundSize: '8px auto' }}
                                    >
                                        {DEAL_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-[10px] text-neutral-500 font-mono uppercase tracking-widest mb-2">Industry</label>
                                    <select 
                                        className="w-full bg-black border border-neutral-800 text-sm font-mono text-white p-3 focus:border-white focus:outline-none appearance-none rounded-none transition-colors cursor-pointer" 
                                        value={form.industry}
                                        onChange={e => setForm(p => ({ ...p, industry: e.target.value }))}
                                        style={{ backgroundImage: 'url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23525252%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.4-12.8z%22%2F%3E%3C%2Fsvg%3E")', backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px top 50%', backgroundSize: '8px auto' }}
                                    >
                                        {INDUSTRIES.map(ind => <option key={ind} value={ind}>{ind}</option>)}
                                    </select>
                                </div>
                            </div>
                            
                            <div>
                                <label className="block text-[10px] text-neutral-500 font-mono uppercase tracking-widest mb-2">Internal Notes</label>
                                <textarea 
                                    className="w-full bg-black border border-neutral-800 text-sm text-white p-3 focus:border-white focus:outline-none transition-colors resize-y min-h-[80px]" 
                                    placeholder="Strategy background, key stakeholders..."
                                    value={form.notes || ''}
                                    onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} 
                                />
                            </div>
                        </div>

                        <div className="p-5 border-t border-neutral-800 flex justify-between items-center">
                            <div className="flex-1">
                                {createError && (
                                    <div className="text-white border border-neutral-700 bg-neutral-900 px-3 py-2 text-xs font-mono">
                                        Error: {createError}
                                    </div>
                                )}
                            </div>
                            <div className="flex gap-3">
                                <button className="px-5 py-2 text-xs font-mono uppercase tracking-widest text-neutral-400 hover:text-white transition-colors border border-transparent hover:border-neutral-800" onClick={() => { setShowModal(false); setCreateError(null) }}>
                                    Cancel
                                </button>
                                <button 
                                    className="bg-white text-black px-6 py-2 text-xs font-mono uppercase tracking-widest hover:bg-neutral-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[120px]" 
                                    onClick={handleCreate} 
                                    disabled={creating || !form.name.trim() || !form.company_name.trim()}
                                >
                                    {creating ? <div className="spinner border-black border-t-transparent w-4 h-4" /> : 'Create Deal'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
