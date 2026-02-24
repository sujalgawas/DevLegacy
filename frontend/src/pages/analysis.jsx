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
    ExternalLink
} from 'lucide-react';
import { fetchAnalysis } from '../services/analysisApi';

const StatCard = ({ icon: Icon, title, value, label, children, className = "" }) => (
    <div className={`bg-[#121215] border border-[#27272a] rounded-2xl p-6 hover:border-purple-500/50 transition-all duration-300 group ${className}`}>
        <div className="flex items-start justify-between mb-4">
            <div className="p-2.5 bg-purple-500/10 rounded-xl text-purple-400 group-hover:scale-110 transition-transform">
                {Icon && <Icon size={22} />}
            </div>
            {value !== undefined && <span className="text-2xl font-bold text-white tracking-tight">{String(value)}</span>}
        </div>
        <h3 className="text-gray-400 text-sm font-medium mb-1">{title}</h3>
        {label && <p className="text-white font-semibold">{label}</p>}
        <div className="mt-4">{children}</div>
    </div>
);

const ScoreRing = ({ score, role }) => {
    const s = parseFloat(score) || 0;
    const percentage = (s / 10) * 100;
    const radius = 70;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;

    return (
        <div className="relative flex flex-col items-center justify-center p-8 bg-[#121215] border border-purple-500/20 rounded-3xl overflow-hidden group">
            <div className="absolute -inset-10 bg-purple-600/10 blur-3xl rounded-full opacity-50 group-hover:opacity-100 transition-opacity"></div>
            <div className="relative h-48 w-48 flex items-center justify-center">
                <svg className="h-full w-full transform -rotate-90">
                    <circle
                        cx="96"
                        cy="96"
                        r={radius}
                        stroke="currentColor"
                        strokeWidth="12"
                        fill="transparent"
                        className="text-[#1a1a1e]"
                    />
                    <circle
                        cx="96"
                        cy="96"
                        r={radius}
                        stroke="currentColor"
                        strokeWidth="12"
                        fill="transparent"
                        strokeDasharray={circumference}
                        className="text-purple-500 transition-all duration-1000 ease-out focus:outline-none"
                        strokeLinecap="round"
                        style={{ strokeDashoffset: isNaN(offset) ? circumference : offset }}
                    />
                </svg>
                <div className="absolute flex flex-col items-center">
                    <span className="text-5xl font-black text-white">{score || 0}</span>
                    <span className="text-xs text-gray-500 font-bold uppercase tracking-wider">Overall Score</span>
                </div>
            </div>

            <div className="mt-6 flex flex-col items-center">
                <span className="px-4 py-1.5 bg-purple-500/20 text-purple-300 rounded-full text-xs font-bold uppercase tracking-widest border border-purple-500/30 mb-2">
                    Recommended Role
                </span>
                <h4 className="text-xl font-bold text-white text-center">{role || 'N/A'}</h4>
            </div>
        </div>
    );
};

// Helper function to safely render array items (prevents React object crash)
const safeRender = (item) => {
    if (!item) return '';
    if (typeof item === 'string' || typeof item === 'number') return item;
    return item.name || item.language || item.id || JSON.stringify(item);
};

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

    if (loading) {
        return (
            <div className="min-h-screen bg-[#09090b] flex flex-col items-center justify-center gap-6">
                <div className="relative">
                    <Loader2 className="animate-spin text-purple-500" size={48} />
                    <div className="absolute inset-0 bg-purple-500/20 blur-xl rounded-full"></div>
                </div>
                <div className="text-center">
                    <h2 className="text-xl font-bold text-white mb-2">Decoding Developer DNA...</h2>
                    <p className="text-gray-500 animate-pulse">Analyzing repositories, commits, and code quality</p>
                </div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="min-h-screen bg-[#09090b] flex flex-col items-center justify-center p-4">
                <div className="bg-[#121215] border border-red-500/20 rounded-3xl p-8 max-w-md w-full text-center">
                    <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center text-red-500 mx-auto mb-6">
                        <AlertCircle size={32} />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-3">Analysis Failed</h2>
                    <p className="text-gray-400 mb-8">{error || "Data could not be loaded."}</p>
                    <button
                        onClick={() => navigate('/')}
                        className="w-full bg-white text-black font-bold py-3 rounded-xl hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
                    >
                        <ArrowLeft size={18} />
                        Back to Search
                    </button>
                </div>
            </div>
        );
    }

    // Safely fallback arrays to prevent .map crashes
    const topRepos = Array.isArray(data.top_3_repo) ? data.top_3_repo : [];
    const mainLangs = Array.isArray(data.most_used_language) ? data.most_used_language : [];
    const allLangs = Array.isArray(data.all_languages) ? data.all_languages : [];

    return (
        <div className="min-h-screen bg-[#09090b] text-white selection:bg-purple-500/30">
            {/* Navbar Overlay */}
            <nav className="sticky top-0 z-50 bg-[#09090b]/80 backdrop-blur-md border-b border-[#27272a]">
                <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                    >
                        <ArrowLeft size={20} />
                        <span className="text-sm font-medium">Back</span>
                    </button>
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-purple-600 rounded flex items-center justify-center font-bold text-sm text-white">D</div>
                        <span className="font-bold text-sm tracking-tight text-white">DevProfile</span>
                    </div>
                    <div className="w-10"></div> {/* Spacer */}
                </div>
            </nav>

            <main className="max-w-7xl mx-auto px-4 py-12">
                {/* Profile Header */}
                <section className="flex flex-col md:flex-row items-center gap-8 mb-16">
                    <div className="relative group shrink-0">
                        <div className="absolute -inset-1 bg-purple-500 rounded-full opacity-20 blur group-hover:opacity-40 transition-opacity"></div>
                        <img
                            src={data.profile_picture || `https://github.com/${gitname}.png`}
                            alt={data.name || gitname}
                            onError={(e) => { e.target.src = 'https://github.com/ghost.png' }}
                            className="relative w-32 h-32 md:w-40 md:h-40 rounded-full border-2 border-purple-500/20 object-cover"
                        />
                        <div className="absolute -bottom-2 -right-2 bg-purple-600 p-2 rounded-xl shadow-xl">
                            <Github size={20} />
                        </div>
                    </div>

                    <div className="flex-1 text-center md:text-left overflow-hidden">
                        <h1 className="text-4xl md:text-5xl font-black mb-4 tracking-tight truncate">{data.name || gitname}</h1>
                        <div className="flex flex-wrap justify-center md:justify-start gap-6 text-sm">
                            <div className="flex items-center gap-2 text-gray-400">
                                <Users size={16} className="text-purple-400 shrink-0" />
                                <span className="font-bold text-white">{data.followers || 0}</span> Followers
                            </div>
                            <div className="flex items-center gap-2 text-gray-400">
                                <Users size={16} className="text-purple-400 shrink-0" />
                                <span className="font-bold text-white">{data.following || 0}</span> Following
                            </div>
                            <div className="flex items-center gap-2 text-gray-400">
                                <BookOpen size={16} className="text-purple-400 shrink-0" />
                                <span className="font-bold text-white">{data.public_repos || 0}</span> Public Repos
                            </div>
                        </div>

                        <a
                            href={`https://github.com/${gitname}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-6 inline-flex items-center gap-2 text-purple-400 hover:text-purple-300 transition-colors text-sm font-bold"
                        >
                            View GitHub Profile <ExternalLink size={14} />
                        </a>
                    </div>
                </section>

                {/* Dashboard Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* Left Column - Stats */}
                    <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">

                        {/* Commits */}
                        <StatCard
                            icon={BarChart3}
                            title="Total Commits"
                            value={data.total_commits || 0}
                        >
                            <div className="space-y-3">
                                <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Top Repositories</p>
                                <div className="flex flex-wrap gap-2">
                                    {topRepos.length > 0 ? topRepos.map((repo, idx) => (
                                        <span key={idx} className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-xs font-semibold text-gray-300">
                                            {safeRender(repo)}
                                        </span>
                                    )) : <span className="text-xs text-gray-600">No recent repositories</span>}
                                </div>
                            </div>
                        </StatCard>

                        {/* Consistency */}
                        <StatCard
                            icon={Flame}
                            title="Consistency"
                            value={`${data.current_streak || 0} days`}
                            label="Current Streak"
                        >
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-3 bg-white/5 border border-white/10 rounded-xl">
                                    <p className="text-[10px] text-gray-500 font-bold uppercase mb-1">Longest</p>
                                    <p className="text-lg font-bold text-white tracking-tight">{data.longest_streak || 0}d</p>
                                </div>
                                <div className="p-3 bg-white/5 border border-white/10 rounded-xl">
                                    <p className="text-[10px] text-gray-500 font-bold uppercase mb-1">Active</p>
                                    <p className="text-lg font-bold text-white tracking-tight">{data.active_days || 0}d</p>
                                </div>
                            </div>
                        </StatCard>

                        {/* Open Source */}
                        <StatCard icon={GitPullRequest} title="Open Source Impact">
                            <div className="grid grid-cols-2 gap-y-6">
                                <div className="flex flex-col">
                                    <span className="text-2xl font-bold text-white">{String(data.pull_requests || 0)}</span>
                                    <span className="text-xs text-gray-500 font-medium">Pull Requests</span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-2xl font-bold text-white">{String(data.issues || 0)}</span>
                                    <span className="text-xs text-gray-500 font-medium">Issues Opened</span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-2xl font-bold text-white">{String(data.repositories_contributed_to || 0)}</span>
                                    <span className="text-xs text-gray-500 font-medium">Repos Contributed</span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-2xl font-bold text-white">{String(data.code_reviews || 0)}</span>
                                    <span className="text-xs text-gray-500 font-medium">Code Reviews</span>
                                </div>
                            </div>
                        </StatCard>

                        {/* Code Quality */}
                        <StatCard icon={Code2} title="Code Intelligence">
                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-3 bg-purple-500/5 border border-purple-500/10 rounded-xl">
                                    <span className="text-xs font-bold uppercase tracking-wider text-purple-300">Level</span>
                                    <span className="text-sm font-black text-white">{data.code_quality || 'N/A'}</span>
                                </div>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-end">
                                        <span className="text-xs text-gray-400">File Structure</span>
                                        <span className="text-xs font-bold text-white">{data.file_structure || 0}/10</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-purple-500 transition-all duration-500"
                                            style={{ width: `${Math.min(100, (parseFloat(data.file_structure) || 0) * 10)}%` }}
                                        ></div>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <div className="flex-1">
                                        <p className="text-[10px] text-gray-500 font-bold uppercase mb-1">Comments</p>
                                        <p className="text-base font-bold text-white">{data.comment_percentage || 0}%</p>
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-[10px] text-gray-500 font-bold uppercase mb-1">README Depth</p>
                                        <p className="text-base font-bold text-white">{data.average_lines_readme || 0} lines</p>
                                    </div>
                                </div>
                            </div>
                        </StatCard>

                    </div>

                    {/* Right Column - Score & Stack */}
                    <div className="space-y-8">
                        <ScoreRing
                            score={data.final_score}
                            role={
                                Array.isArray(data.recommended_role) && data.recommended_role.length > 0
                                    ? data.recommended_role[0].role
                                    : (typeof data.recommended_role === 'string' ? data.recommended_role : 'N/A')
                            }
                        />

                        {/* Tech Stack */}
                        <div className="bg-[#121215] border border-[#27272a] rounded-3xl p-8">
                            <div className="flex items-center gap-3 mb-6">
                                <FileJson className="text-purple-400" size={20} />
                                <h3 className="text-lg font-bold">Tech Stack</h3>
                            </div>

                            <div className="space-y-3 mb-8">
                                <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Primarily Built With</p>
                                <div className="flex flex-wrap gap-2">
                                    {mainLangs.length > 0 ? mainLangs.map((lang, idx) => (
                                        <span key={idx} className="px-4 py-2 bg-purple-500 text-white rounded-xl text-xs font-black shadow-lg shadow-purple-500/20">
                                            {safeRender(lang)}
                                        </span>
                                    )) : <span className="text-xs text-gray-600">None detected</span>}
                                </div>
                            </div>

                            <div className="space-y-3">
                                <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">All Technologies</p>
                                <div className="flex flex-wrap gap-1.5">
                                    {allLangs.length > 0 ? allLangs.map((lang, idx) => (
                                        <span key={idx} className="px-2.5 py-1 bg-white/5 border border-white/10 rounded-lg text-[10px] font-bold text-gray-400">
                                            {safeRender(lang)}
                                        </span>
                                    )) : <span className="text-xs text-gray-600">None detected</span>}
                                </div>
                            </div>
                        </div>

                        {/* Achievement Badge */}
                        <div className="relative group overflow-hidden bg-gradient-to-br from-purple-600 to-indigo-700 rounded-3xl p-6 text-center">
                            <div className="absolute top-0 right-0 -mr-8 -mt-8 w-32 h-32 bg-white/10 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700"></div>
                            <Trophy className="mx-auto mb-4 text-white/50 group-hover:scale-110 transition-transform" size={40} />
                            <h4 className="text-xl font-black text-white mb-2">DevDNA Verified</h4>
                            <p className="text-purple-100 text-xs font-medium leading-relaxed opacity-80">
                                This developer's profile has been decoded by our AI engine with {data.final_score || 0}/10 points.
                            </p>
                        </div>
                    </div>

                </div>
            </main>

            {/* Footer */}
            <footer className="mt-20 border-t border-[#27272a] py-12 px-4">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 opacity-40 grayscale">
                    <div className="flex items-center gap-2">
                        <div className="w-5 h-5 bg-white rounded flex items-center justify-center font-bold text-[10px] text-black">D</div>
                        <span className="font-bold text-xs">DevProfile Analysis Engine v1.0</span>
                    </div>
                    <p className="text-[10px] font-medium">© 2026 AI-Powered Analysis. For demonstration purposes only.</p>
                </div>
            </footer>
        </div>
    );
};

export default Analysis;