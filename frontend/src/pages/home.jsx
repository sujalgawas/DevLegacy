import React, { useState, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Github, Sparkles } from 'lucide-react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, MeshDistortMaterial } from '@react-three/drei';

/* ── 3D Floating Gem (subtle, ambient) ── */
function FloatingGem() {
  const meshRef = useRef();

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.elapsedTime * 0.12;
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.18;
    }
  });

  return (
    <Float speed={1.2} rotationIntensity={0.3} floatIntensity={0.8}>
      <mesh ref={meshRef} scale={2.4}>
        <icosahedronGeometry args={[1, 1]} />
        <MeshDistortMaterial
          color="#8B5CF6"
          emissive="#FF6B9D"
          emissiveIntensity={0.15}
          roughness={0.3}
          metalness={0.9}
          distort={0.25}
          speed={1.5}
          transparent
          opacity={0.6}
        />
      </mesh>
      <mesh scale={1.8}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshBasicMaterial color="#FF6B9D" transparent opacity={0.04} />
      </mesh>
    </Float>
  );
}

/* ── Floating Particles ── */
function Particles() {
  const count = 30;
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count * 3; i += 3) {
      pos[i] = (Math.random() - 0.5) * 14;
      pos[i + 1] = (Math.random() - 0.5) * 14;
      pos[i + 2] = (Math.random() - 0.5) * 4;
    }
    return pos;
  }, []);

  const ref = useRef();
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.015;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.035} color="#FF6B9D" transparent opacity={0.5} sizeAttenuation />
    </points>
  );
}

/* ── Home Page ── */
function Home() {
  const [username, setUsername] = useState('');
  const navigate = useNavigate();

  const handleAnalyze = () => {
    if (username.trim()) {
      const gitname = username.includes('github.com/')
        ? username.split('github.com/')[1].split('/')[0]
        : username.trim();
      navigate(`/analysis/${gitname}`);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleAnalyze();
  };

  return (
    <div className="min-h-screen bg-void text-white font-sans relative overflow-hidden">

      {/* Ambient gradient blobs — sunset feel */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-30%] right-[-15%] w-[60%] h-[60%] bg-sunset-pink rounded-full blur-[200px] opacity-[0.08] animate-blob"></div>
        <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] bg-sunset-purple rounded-full blur-[180px] opacity-[0.1] animate-blob animation-delay-4000"></div>
        <div className="absolute top-[30%] left-[40%] w-[30%] h-[30%] bg-sunset-magenta rounded-full blur-[160px] opacity-[0.06] animate-blob animation-delay-2000"></div>
      </div>

      {/* 3D Canvas — ambient background element */}
      <div className="fixed inset-0 pointer-events-none opacity-60">
        <Canvas camera={{ position: [0, 0, 7], fov: 40 }}>
          <ambientLight intensity={0.3} />
          <directionalLight position={[5, 5, 5]} intensity={0.6} color="#FF6B9D" />
          <pointLight position={[-4, -4, 3]} intensity={0.4} color="#8B5CF6" />
          <pointLight position={[3, 2, 2]} intensity={0.2} color="#22D3EE" />
          <FloatingGem />
          <Particles />
        </Canvas>
      </div>

      {/* Navbar — minimal, clean */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-6xl mx-auto">
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="w-9 h-9 bg-gradient-to-br from-sunset-pink to-sunset-purple rounded-lg flex items-center justify-center font-mono font-bold text-sm text-white group-hover:scale-110 transition-transform duration-300">
            D
          </div>
          <span className="font-mono font-bold text-sm tracking-wide text-white/80">
            DevProfile
          </span>
        </div>
        <div className="flex gap-6 items-center">
          <button className="text-white/40 hover:text-white/80 transition-colors text-sm font-medium">Log in</button>
          <button className="glass-panel px-5 py-2 text-sm font-medium text-white/80 hover:text-white hover:border-neon-cyan/30 transition-all duration-300">
            Sign up
          </button>
        </div>
      </nav>

      {/* Main — centered, spacious */}
      <main className="relative z-10 flex flex-col items-center justify-center px-6 pt-32 pb-32 max-w-3xl mx-auto text-center">

        {/* Subtle badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-sunset-purple/20 bg-sunset-purple/5 text-xs font-mono text-sunset-pink mb-12 animate-float">
          <Sparkles size={12} />
          <span>AI-Powered Analysis</span>
        </div>

        {/* Heading — clean, big, breathing */}
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-[1.1]">
          <span className="text-white/90">Decode Your</span>
          <br />
          <span className="text-gradient-sunset">Developer DNA</span>
        </h1>

        <p className="text-white/35 text-base md:text-lg max-w-lg mx-auto mb-16 leading-relaxed font-normal">
          Instant insights into any GitHub profile. Code quality, tech stack, and open-source impact — all in one view.
        </p>

        {/* Search — clean glass panel */}
        <div className="w-full max-w-xl">
          <div className="glass-panel flex items-center p-1.5 group hover:border-neon-cyan/25 transition-all duration-500">
            <div className="pl-4 text-white/20">
              <Github size={20} />
            </div>

            <input
              type="text"
              placeholder="github username or url"
              className="w-full bg-transparent text-white placeholder-white/20 px-4 py-3.5 outline-none text-sm font-mono"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyDown={handleKeyDown}
            />

            <button
              onClick={handleAnalyze}
              className="bg-gradient-to-r from-sunset-pink to-sunset-purple text-white font-semibold px-6 py-3.5 rounded-xl text-sm transition-all duration-300 hover:shadow-[0_0_25px_rgba(255,107,157,0.25)] active:scale-95 whitespace-nowrap flex items-center gap-2"
            >
              Analyze <Search size={15} />
            </button>
          </div>
        </div>

        {/* Minimal feature hints */}
        <div className="flex items-center gap-8 mt-16 text-white/20 text-xs font-mono">
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-sunset-pink"></span>
            Code Quality
          </span>
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-sunset-purple"></span>
            Commit Analysis
          </span>
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-neon-cyan"></span>
            AI Detection
          </span>
        </div>

      </main>
    </div>
  );
}

export default Home;