import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Github,
    Users,
    BookOpen,
    GitPullRequest,
    AlertCircle,
    Flame,
    BarChart3,
    Code2,
    FileJson,
    ArrowLeft,
    Loader2,
    Trophy,
    ExternalLink,
    Sparkles,
    Activity
} from 'lucide-react';
import { fetchAnalysis } from '../services/analysisApi';

/* ── Stat Card ── */
const StatCard = ({ icon: Icon, title, value, label, children, iconColor = "text-sunset-pink" }) => (
    <div className="glass-panel glass-panel-hover p-6 group">
        <div className="flex items-start justify-between mb-5">
            <div className={`p-2.5 rounded-xl bg-white/[0.04] ${iconColor}`}>
                {Icon && <Icon size={20} />}
            </div>
            {value !== undefined && (
                <span className="text-2xl font-bold text-white/90 font-mono">{String(value)}</span>
            )}
        </div>
        <h3 className="text-white/30 text-[11px] font-mono uppercase tracking-widest mb-1">{title}</h3>
        {label && <p className="text-white/80 font-semibold text-base">{label}</p>}
        {children && <div className="mt-5">{children}</div>}
    </div>
);

/* ── Score Ring ── */
const ScoreRing = ({ score, role }) => {
    const s = parseFloat(score) || 0;
    const percentage = (s / 10) * 100;
    const radius = 65;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;

    return (
        <div className="glass-panel p-8 flex flex-col items-center">
            <div className="relative h-48 w-48 flex items-center justify-center mb-8">
                <svg className="h-full w-full transform -rotate-90" viewBox="0 0 200 200">
                    <circle
                        cx="100" cy="100" r={radius}
                        stroke="rgba(255,255,255,0.04)"
                        strokeWidth="10" fill="transparent"
                    />
                    <circle
                        cx="100" cy="100" r={radius}
                        stroke="url(#omarchy-gradient)"
                        strokeWidth="10" fill="transparent"
                        strokeDasharray={circumference}
                        strokeLinecap="round"
                        className="transition-all duration-1000 ease-out"
                        style={{ strokeDashoffset: isNaN(offset) ? circumference : offset }}
                    />
                    <defs>
                        <linearGradient id="omarchy-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#FF6B9D" />
                            <stop offset="50%" stopColor="#8B5CF6" />
                            <stop offset="100%" stopColor="#22D3EE" />
                        </linearGradient>
                    </defs>
                </svg>
                <div className="absolute flex flex-col items-center">
                    <span className="text-5xl font-bold text-white font-mono">{score || 0}</span>
                    <span className="text-[10px] text-white/30 font-mono uppercase tracking-widest mt-1">score</span>
                </div>
            </div>

            <div className="w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-6"></div>
            <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest mb-2 flex items-center gap-1.5">
                <Sparkles size={10} className="text-sunset-pink" />
                recommended role
            </span>
            <h4 className="text-xl font-bold text-gradient-sunset text-center">{role || 'N/A'}</h4>
        </div>
    );
};

const safeRender = (item) => {
    if (!item) return '';
    if (typeof item === 'string' || typeof item === 'number') return item;
    return item.name || item.language || item.id || JSON.stringify(item);
};

/* ── Analysis Page ── */
const Analysis = () => {
    const { gitname } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadData = async () => {
            if (!gitname) {
                setError("No GitHub username provided in the URL.");
                setLoading(false);
                return;
            }
            try {
                setLoading(true);
                const result = await fetchAnalysis(gitname);
                if (!result || typeof result !== 'object' || Array.isArray(result)) {
                    throw new Error('Received invalid data format from server');
                }
                if (!result.final_score && !result.name) {
                    throw new Error('Analysis completed but returned empty results');
                }
                setData(result);
                setError(null);
            } catch (err) {
                console.error("Analysis Fetch Error:", err);
                setError(err.message || 'Something went wrong fetching the analysis.');
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, [gitname]);

    /* Loading */
    if (loading) {
        return (
            <div className="min-h-screen bg-void flex flex-col items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute top-[40%] left-[45%] w-[30%] h-[30%] bg-sunset-purple rounded-full blur-[150px] opacity-[0.08] animate-blob"></div>
                </div>
                <div className="relative z-10 glass-panel p-12 flex flex-col items-center">
                    <Loader2 className="animate-spin text-sunset-pink mb-6" size={40} />
                    <h2 className="text-lg font-semibold text-white/80 mb-2">Analyzing profile...</h2>
                    <p className="text-white/25 font-mono text-xs uppercase tracking-widest">processing repositories</p>
                </div>
            </div>
        );
    }

    /* Error */
    if (error || !data) {
        return (
            <div className="min-h-screen bg-void flex flex-col items-center justify-center p-6 relative overflow-hidden">
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute top-[40%] left-[45%] w-[30%] h-[30%] bg-sunset-pink rounded-full blur-[150px] opacity-[0.06]"></div>
                </div>
                <div className="glass-panel p-10 max-w-sm w-full text-center relative z-10">
                    <div className="w-14 h-14 bg-gradient-to-br from-sunset-pink to-sunset-purple rounded-xl flex items-center justify-center text-white mx-auto mb-6">
                        <AlertCircle size={28} />
                    </div>
                    <h2 className="text-xl font-bold text-white/90 mb-3">Analysis Failed</h2>
                    <p className="text-white/35 mb-8 text-sm font-mono">{error || "Data could not be loaded."}</p>
                    <button
                        onClick={() => navigate('/')}
                        className="w-full bg-gradient-to-r from-sunset-pink to-sunset-purple text-white font-semibold py-3 rounded-xl hover:shadow-[0_0_20px_rgba(255,107,157,0.2)] transition-all flex items-center justify-center gap-2 text-sm"
                    >
                        <ArrowLeft size={16} /> Back to Search
                    </button>
                </div>
            </div>
        );
    }

    const topRepos = Array.isArray(data.top_3_repo) ? data.top_3_repo : [];
    const mainLangs = Array.isArray(data.most_used_language) ? data.most_used_language : [];
    const allLangs = Array.isArray(data.all_languages) ? data.all_languages : [];

    return (
        <div className="min-h-screen bg-void text-white/90 relative overflow-hidden pb-16">
            {/* Background */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-[-15%] right-[-5%] w-[40%] h-[40%] bg-sunset-pink rounded-full blur-[200px] opacity-[0.06] animate-blob"></div>
                <div className="absolute bottom-[-10%] left-[-5%] w-[45%] h-[45%] bg-sunset-purple rounded-full blur-[200px] opacity-[0.08] animate-blob animation-delay-4000"></div>
            </div>

            {/* Navbar */}
            <nav className="sticky top-0 z-50 bg-void/70 backdrop-blur-xl border-b border-white/[0.05]">
                <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 text-white/30 hover:text-white/70 transition-colors text-sm font-mono"
                    >
                        <ArrowLeft size={16} />
                        <span>back</span>
                    </button>
                    <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 bg-gradient-to-br from-sunset-pink to-sunset-purple rounded-lg flex items-center justify-center font-mono font-bold text-[10px] text-white">D</div>
                        <span className="font-mono font-bold text-xs text-white/60 hidden sm:block">DevProfile</span>
                    </div>
                    <div className="w-16"></div>
                </div>
            </nav>

            <main className="max-w-6xl mx-auto px-6 py-10 relative z-10">

                {/* Profile Header */}
                <section className="flex flex-col md:flex-row items-center gap-8 mb-12 glass-panel p-8">
                    <div className="relative group shrink-0">
                        <div className="absolute -inset-2 bg-gradient-to-r from-sunset-pink via-sunset-purple to-neon-cyan rounded-full opacity-20 blur-lg group-hover:opacity-40 transition-opacity duration-500"></div>
                        <img
                            src={data.profile_picture || `https://github.com/${gitname}.png`}
                            alt={data.name || gitname}
                            onError={(e) => { e.target.src = 'https://github.com/ghost.png' }}
                            className="relative w-28 h-28 md:w-32 md:h-32 rounded-full border border-white/10 object-cover"
                        />
                        <div className="absolute -bottom-2 -right-2 bg-gradient-to-br from-sunset-pink to-sunset-purple text-white p-2 rounded-xl">
                            <Github size={16} />
                        </div>
                    </div>

                    <div className="flex-1 text-center md:text-left overflow-hidden">
                        <h1 className="text-3xl md:text-4xl font-bold mb-4 tracking-tight truncate">{data.name || gitname}</h1>
                        <div className="flex flex-wrap justify-center md:justify-start gap-4 text-sm font-mono">
                            <span className="flex items-center gap-2 text-white/40">
                                <Users size={14} className="text-sunset-pink" />
                                <span className="text-white/70 font-semibold">{data.followers || 0}</span> followers
                            </span>
                            <span className="flex items-center gap-2 text-white/40">
                                <Activity size={14} className="text-sunset-purple" />
                                <span className="text-white/70 font-semibold">{data.following || 0}</span> following
                            </span>
                            <span className="flex items-center gap-2 text-white/40">
                                <BookOpen size={14} className="text-neon-cyan" />
                                <span className="text-white/70 font-semibold">{data.public_repos || 0}</span> repos
                            </span>
                        </div>

                        <a
                            href={`https://github.com/${gitname}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-6 inline-flex items-center gap-2 text-sunset-pink hover:text-sunset-pink/80 transition-colors text-xs font-mono uppercase tracking-wider"
                        >
                            view profile <ExternalLink size={12} />
                        </a>
                    </div>
                </section>

                {/* Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* Left — Stats */}
                    <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">

                        <StatCard icon={BarChart3} title="Total Commits" value={data.total_commits || 0} iconColor="text-sunset-pink">
                            <div>
                                <p className="text-[10px] font-mono uppercase tracking-widest text-white/25 mb-3">Top Repos</p>
                                <div className="flex flex-wrap gap-2">
                                    {topRepos.length > 0 ? topRepos.map((repo, idx) => (
                                        <span key={idx} className="px-3 py-1 bg-white/[0.04] border border-white/[0.06] rounded-lg text-xs font-mono text-white/50">
                                            {safeRender(repo)}
                                        </span>
                                    )) : <span className="text-xs text-white/15 font-mono">none</span>}
                                </div>
                            </div>
                        </StatCard>

                        <StatCard icon={Flame} title="Consistency" value={`${data.current_streak || 0}d`} label="Current Streak" iconColor="text-amber-400">
                            <div className="grid grid-cols-2 gap-3">
                                <div className="p-3 bg-white/[0.03] border border-white/[0.05] rounded-xl">
                                    <p className="text-[10px] text-white/25 font-mono uppercase mb-1">Longest</p>
                                    <p className="text-lg font-bold text-white/80 font-mono">{data.longest_streak || 0}d</p>
                                </div>
                                <div className="p-3 bg-white/[0.03] border border-white/[0.05] rounded-xl">
                                    <p className="text-[10px] text-white/25 font-mono uppercase mb-1">Active</p>
                                    <p className="text-lg font-bold text-white/80 font-mono">{data.active_days || 0}d</p>
                                </div>
                            </div>
                        </StatCard>

                        <StatCard icon={GitPullRequest} title="Open Source Impact" iconColor="text-neon-cyan">
                            <div className="grid grid-cols-2 gap-y-5 gap-x-4">
                                {[
                                    { val: data.pull_requests, label: 'PRs' },
                                    { val: data.issues, label: 'Issues' },
                                    { val: data.repositories_contributed_to, label: 'Contributed' },
                                    { val: data.code_reviews, label: 'Reviews' },
                                ].map((item, idx) => {
                                    let display = '-';
                                    const v = item.val;
                                    if (v != null) {
                                        if (typeof v === 'number' || typeof v === 'string') {
                                            display = String(v);
                                        } else if (Array.isArray(v)) {
                                            display = String(v.length);
                                        } else if (typeof v === 'object') {
                                            const total = Object.values(v).reduce((sum, n) => sum + (Number(n) || 0), 0);
                                            display = total > 0 ? String(total) : '-';
                                        }
                                    }
                                    return (
                                        <div key={idx}>
                                            <span className="text-xl font-bold text-white/80 font-mono">{display}</span>
                                            <p className="text-[10px] text-white/25 font-mono uppercase mt-0.5">{item.label}</p>
                                        </div>
                                    );
                                })}
                            </div>
                        </StatCard>

                        <StatCard icon={Code2} title="Code Intelligence" iconColor="text-sunset-purple">
                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-3 bg-white/[0.03] border border-white/[0.05] rounded-xl">
                                    <span className="text-[10px] font-mono uppercase tracking-wider text-white/30">Level</span>
                                    <span className="text-sm font-bold text-gradient-pink">{data.code_quality || 'N/A'}</span>
                                </div>
                                <div>
                                    <div className="flex justify-between items-end mb-2">
                                        <span className="text-[10px] font-mono text-white/25 uppercase">Structure</span>
                                        <span className="text-xs font-mono font-bold text-white/50">{data.file_structure || 0}/10</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-white/[0.04] rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-sunset-pink to-sunset-purple rounded-full"
                                            style={{ width: `${Math.min(100, (parseFloat(data.file_structure) || 0) * 10)}%` }}
                                        ></div>
                                    </div>
                                </div>
                                <div className="flex gap-3">
                                    <div className="flex-1 p-3 bg-white/[0.03] rounded-xl border border-white/[0.04]">
                                        <p className="text-[9px] text-white/20 font-mono uppercase mb-1">Docs</p>
                                        <p className="text-base font-bold text-white/70 font-mono">{data.comment_percentage || 0}%</p>
                                    </div>
                                    <div className="flex-1 p-3 bg-white/[0.03] rounded-xl border border-white/[0.04]">
                                        <p className="text-[9px] text-white/20 font-mono uppercase mb-1">README</p>
                                        <p className="text-base font-bold text-white/70 font-mono">{data.average_lines_readme || 0}L</p>
                                    </div>
                                </div>
                            </div>
                        </StatCard>

                    </div>

                    {/* Right — Score & Stack */}
                    <div className="space-y-6">
                        <ScoreRing
                            score={data.final_score}
                            role={
                                Array.isArray(data.recommended_role) && data.recommended_role.length > 0
                                    ? data.recommended_role[0].role
                                    : (typeof data.recommended_role === 'string' ? data.recommended_role : 'N/A')
                            }
                        />

                        {/* Tech Stack */}
                        <div className="glass-panel p-6">
                            <div className="flex items-center gap-2.5 mb-6">
                                <FileJson className="text-amber-400" size={18} />
                                <h3 className="text-sm font-bold text-white/70">Tech Stack</h3>
                            </div>

                            <div className="mb-6">
                                <p className="text-[10px] font-mono uppercase tracking-widest text-white/20 mb-3">Primary</p>
                                <div className="flex flex-wrap gap-2">
                                    {mainLangs.length > 0 ? mainLangs.map((lang, idx) => (
                                        <span key={idx} className="px-3 py-1.5 bg-gradient-to-r from-sunset-pink/20 to-sunset-purple/20 border border-sunset-pink/20 text-white/80 rounded-lg text-xs font-mono font-semibold">
                                            {safeRender(lang)}
                                        </span>
                                    )) : <span className="text-xs font-mono text-white/15">none detected</span>}
                                </div>
                            </div>

                            <div>
                                <p className="text-[10px] font-mono uppercase tracking-widest text-white/20 mb-3">All</p>
                                <div className="flex flex-wrap gap-1.5">
                                    {allLangs.length > 0 ? allLangs.map((lang, idx) => (
                                        <span key={idx} className="px-2.5 py-1 bg-white/[0.03] border border-white/[0.06] rounded-md text-[11px] font-mono text-white/35 hover:text-white/60 transition-colors">
                                            {safeRender(lang)}
                                        </span>
                                    )) : <span className="text-[11px] font-mono text-white/15">none detected</span>}
                                </div>
                            </div>
                        </div>

                        {/* Verified Badge */}
                        <div className="glass-panel p-6 text-center border-sunset-pink/10 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-24 h-24 bg-sunset-pink/5 rounded-full blur-2xl group-hover:bg-sunset-pink/10 transition-all duration-700"></div>
                            <div className="relative z-10">
                                <div className="mx-auto w-12 h-12 bg-gradient-to-br from-sunset-pink/20 to-sunset-purple/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                                    <Trophy className="text-sunset-pink" size={24} />
                                </div>
                                <h4 className="text-sm font-bold text-white/70 mb-1">DevDNA Verified</h4>
                                <p className="text-white/25 text-xs font-mono">
                                    Score: <span className="text-sunset-pink font-bold">{data.final_score || 0}/10</span>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <footer className="mt-16 border-t border-white/[0.04] py-8 px-6 relative z-10">
                <div className="max-w-6xl mx-auto flex items-center justify-between opacity-25 hover:opacity-50 transition-opacity">
                    <div className="flex items-center gap-2">
                        <div className="w-5 h-5 bg-gradient-to-br from-sunset-pink to-sunset-purple rounded flex items-center justify-center font-mono font-bold text-[8px] text-white">D</div>
                        <span className="font-mono text-[10px] tracking-widest uppercase">DevProfile v2.0</span>
                    </div>
                    <p className="text-[10px] font-mono tracking-widest uppercase">© 2026</p>
                </div>
            </footer>
        </div>
    );
};

export default Analysis;