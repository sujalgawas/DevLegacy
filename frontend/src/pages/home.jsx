import React, { useState } from 'react';
import { Search, Code2, Terminal, Cpu, Github } from 'lucide-react';

function Home() {
  const [username, setUsername] = useState('');

  // Added icons to the tags for a more polished look
  const tags = [
    { label: 'Code Quality', icon: <Code2 size={16} /> },
    { label: 'Commit Analysis', icon: <Terminal size={16} /> },
    { label: 'AI Detection', icon: <Cpu size={16} /> }
  ];

  return (
    <div className="min-h-screen bg-[#09090b] text-white font-sans selection:bg-purple-500 selection:text-white">
      
      {/* Navbar - Simple layout */}
      <nav className="flex items-center justify-between px-6 py-6 max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center font-bold text-xl">D</div>
          <span className="font-bold text-lg tracking-tight">DevProfile</span>
        </div>
        <div className="flex gap-4">
          <button className="text-gray-400 hover:text-white transition-colors text-sm font-medium">Log in</button>
          <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors">
            Sign up
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex flex-col items-center justify-center px-4 pt-20 pb-20 w-full max-w-4xl mx-auto text-center">
        
        {/* Small Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-purple-500/20 bg-purple-500/10 text-purple-300 text-xs font-medium mb-8">
          <Cpu size={14} />
          <span>AI-Powered Developer Analysis</span>
        </div>

        {/* Hero Heading - No gradients, just solid high contrast */}
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 leading-tight">
          Decode Your <span className="text-purple-500">Developer DNA</span>
        </h1>

        {/* Subtitle */}
        <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
          Get instant insights into any GitHub profile. Discover code quality, 
          developer level, and AI-written code detection.
        </p>

        {/* Tags Row */}
        <div className="flex flex-wrap items-center justify-center gap-3 mb-12">
          {tags.map((tag, index) => (
            <div 
              key={index} 
              className="flex items-center gap-2 px-4 py-2 bg-[#18181b] border border-[#27272a] rounded-full text-gray-300 text-sm hover:border-purple-500/50 transition-colors cursor-default"
            >
              <span className="text-purple-400">{tag.icon}</span>
              <span>{tag.label}</span>
            </div>
          ))}
        </div>

        {/* Search Input Area */}
        <div className="w-full max-w-xl relative group">
          {/* Subtle glow effect behind input (optional) */}
          <div className="absolute -inset-0.5 bg-purple-500 rounded-xl opacity-20 blur-lg group-hover:opacity-40 transition duration-500"></div>
          
          <div className="relative flex items-center bg-[#121215] border border-[#27272a] rounded-xl p-1.5 focus-within:border-purple-500/50 transition-colors shadow-2xl">
            {/* Icon */}
            <div className="pl-4 text-gray-500">
              <Github size={20} />
            </div>
            
            {/* Input */}
            <input 
              type="text" 
              placeholder="Enter GitHub username or URL" 
              className="w-full bg-transparent text-white placeholder-gray-500 px-4 py-3 outline-none border-none text-base"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            
            {/* Button */}
            <button className="bg-purple-600 hover:bg-purple-700 text-white font-medium px-6 py-3 rounded-lg transition-all transform active:scale-95 whitespace-nowrap">
              Analyze →
            </button>
          </div>
          
          <p className="text-gray-500 text-xs mt-4">
            Try it free • One free analysis per session
          </p>
        </div>

      </main>
    </div>
  );
}

export default Home;