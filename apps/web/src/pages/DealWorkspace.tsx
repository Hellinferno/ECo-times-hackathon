import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchCurrentUser, fetchDeal, type CurrentUserInfo, type Deal } from '../lib/api'
import { ArrowLeft, FileText, Bot, Download, LayoutDashboard, CheckSquare } from 'lucide-react'
import DocumentsTab from '../components/workspace/DocumentsTab'
import AgentsTab from '../components/workspace/AgentsTab'
import OutputsTab from '../components/workspace/OutputsTab'
import TasksTab from '../components/workspace/TasksTab'

type TabKey = 'overview' | 'documents' | 'agents' | 'outputs' | 'tasks'

const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
    { key: 'overview', label: 'Overview', icon: <LayoutDashboard size={14} /> },
    { key: 'documents', label: 'Data Room', icon: <FileText size={14} /> },
    { key: 'agents', label: 'Agents', icon: <Bot size={14} /> },
    { key: 'outputs', label: 'Outputs', icon: <Download size={14} /> },
    { key: 'tasks', label: 'Tasks', icon: <CheckSquare size={14} /> },
]

export default function DealWorkspace() {
    const { dealId } = useParams<{ dealId: string }>()
    const navigate = useNavigate()
    const [deal, setDeal] = useState<Deal | null>(null)
    const [currentUser, setCurrentUser] = useState<CurrentUserInfo | null>(null)
    const [loading, setLoading] = useState(true)
    const [activeTab, setActiveTab] = useState<TabKey>('overview')

    const loadDeal = useCallback(async () => {
        if (!dealId) return
        try {
            const [d, user] = await Promise.all([
                fetchDeal(dealId),
                fetchCurrentUser(),
            ])
            setDeal(d)
            setCurrentUser(user)
        } catch {
            console.error('Failed to load deal')
        } finally {
            setLoading(false)
        }
    }, [dealId])

    useEffect(() => { loadDeal() }, [loadDeal])

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-black text-neutral-500">
                <div className="spinner mb-4 border-t-white mix-blend-difference" />
                <span className="font-mono text-xs uppercase tracking-widest text-neutral-400">Loading Workspace...</span>
            </div>
        )
    }

    if (!deal) {
        return (
            <div className="min-h-screen bg-black flex flex-col items-center justify-center text-white">
                <p className="font-mono text-xs uppercase tracking-widest text-neutral-500 mb-4">Deal not found</p>
                <button 
                    className="border border-neutral-700 px-6 py-2 hover:bg-white hover:text-black transition-colors font-mono uppercase text-xs tracking-widest"
                    onClick={() => navigate('/')}
                >
                    Return to Pipeline
                </button>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-black text-white font-sans selection:bg-white selection:text-black">
            {/* Top Bar */}
            <div className="px-6 md:px-10 py-5 border-b border-neutral-800 flex items-start md:items-center justify-between flex-col md:flex-row gap-4 bg-black sticky top-0 z-10">
                <div className="flex items-center gap-4">
                    <button 
                        className="text-neutral-500 hover:text-white transition-colors border border-transparent hover:border-neutral-800 p-2 -ml-2" 
                        onClick={() => navigate('/')}
                        title="Back to Pipeline"
                    >
                        <ArrowLeft size={16} />
                    </button>
                    <div>
                        <h1 className="text-xl font-medium tracking-tight m-0 text-white flex items-center gap-3">
                            {deal.name}
                        </h1>
                        <p className="text-neutral-500 text-xs font-mono uppercase tracking-widest mt-1">
                            {deal.company_name} <span className="mx-1 opacity-50">·</span> {deal.deal_type}
                        </p>
                    </div>
                </div>
                
                <div className="flex flex-wrap gap-2 md:gap-3">
                    {currentUser && <span className="badge badge-amber">{currentUser.role}</span>}
                    <span className="badge badge-indigo">{deal.deal_type}</span>
                    <span className="badge badge-emerald">{deal.deal_stage}</span>
                </div>
            </div>

            {/* Tab Nav Grid Box */}
            <div className="border-b border-neutral-800 bg-black overflow-x-auto">
                <div className="flex px-6 md:px-10 min-w-max">
                    {TABS.map(tab => (
                        <button
                            key={tab.key}
                            className={`flex items-center gap-2 px-6 py-4 text-[10px] font-mono uppercase tracking-widest transition-colors border-b-2
                                ${activeTab === tab.key 
                                    ? 'text-white border-white' 
                                    : 'text-neutral-500 border-transparent hover:text-neutral-300 hover:border-neutral-800'
                                }`}
                            onClick={() => setActiveTab(tab.key)}
                        >
                            {tab.icon} {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Tab Content Box */}
            <div className="p-6 md:p-10 max-w-[1400px] mx-auto min-h-[calc(100vh-140px)] flex flex-col">
                {activeTab === 'overview' && (
                    <div className="animate-fade-in flex-1">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-neutral-800 border border-neutral-800 mb-8">
                            {[
                                { label: 'INDUSTRY', value: deal.industry },
                                { label: 'STAGE', value: deal.deal_stage },
                                { label: 'CREATED', value: new Date(deal.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) },
                            ].map((item, i) => (
                                <div key={i} className="bg-black p-6 md:p-8 flex flex-col justify-between group hover:bg-neutral-950 transition-colors">
                                    <div className="text-neutral-500 text-[10px] uppercase font-mono tracking-widest mb-4">
                                        {item.label}
                                    </div>
                                    <div className="text-xl md:text-2xl font-light tracking-tight text-white">
                                        {item.value}
                                    </div>
                                </div>
                            ))}
                        </div>
                        
                        {deal.notes && (
                            <div className="bg-black border border-neutral-800 p-6 md:p-8">
                                <div className="text-neutral-500 text-[10px] uppercase font-mono tracking-widest mb-4">
                                    INTERNAL NOTES
                                </div>
                                <p className="text-neutral-300 text-sm leading-relaxed whitespace-pre-wrap font-sans max-w-4xl">
                                    {deal.notes}
                                </p>
                            </div>
                        )}
                    </div>
                )}
                
                {activeTab === 'documents' && <div className="animate-fade-in flex-1"><DocumentsTab dealId={dealId!} /></div>}
                {activeTab === 'agents' && <div className="animate-fade-in flex-1"><AgentsTab dealId={dealId!} /></div>}
                {activeTab === 'outputs' && <div className="animate-fade-in flex-1"><OutputsTab dealId={dealId!} /></div>}
                {activeTab === 'tasks' && <div className="animate-fade-in flex-1"><TasksTab dealId={dealId!} /></div>}
            </div>
        </div>
    )
}
