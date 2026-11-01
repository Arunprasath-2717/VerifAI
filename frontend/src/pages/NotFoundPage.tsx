import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'motion/react';
import { 
  ShieldAlert, 
  ArrowLeft, 
  Home, 
  Search, 
  MessageSquare, 
  BookOpen, 
  Trophy, 
  Terminal,
  Compass,
  CornerDownLeft
} from 'lucide-react';

interface NotFoundPageProps {
  isAuthenticated?: boolean;
}

export const NotFoundPage: React.FC<NotFoundPageProps> = ({ isAuthenticated }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // Quick navigation shortcuts for developer ease
  const quickLinks = [
    {
      title: 'Fact Verification',
      desc: 'Audit claims, cross-examine evidence, and detect deepfakes.',
      path: '/verify',
      icon: Search,
      tag: 'Tool'
    },
    {
      title: 'AI Consensus Chat',
      desc: 'Collaborate with GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro.',
      path: '/chat',
      icon: MessageSquare,
      tag: 'Console'
    },
    {
      title: 'Knowledge Base',
      desc: 'Ground models in verified institutional source documents.',
      path: '/knowledge-base',
      icon: BookOpen,
      tag: 'Sources'
    },
    {
      title: 'Model Leaderboard',
      desc: 'Compare hallucination benchmarks across frontier LLMs.',
      path: '/leaderboard',
      icon: Trophy,
      tag: 'Bench'
    },
  ];

  return (
    <div className="relative min-h-screen w-full flex flex-col items-center justify-between bg-[#050508] text-white overflow-hidden select-none px-4 py-8 sm:py-12">
      
      {/* Background ambient iridescent glow matching auth ribbons */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-32 left-1/4 w-[500px] h-[500px] rounded-full bg-fuchsia-600/10 blur-[140px]" />
        <div className="absolute top-1/2 -right-32 w-[550px] h-[550px] rounded-full bg-cyan-500/10 blur-[150px]" />
        <div className="absolute -bottom-32 left-1/3 w-[600px] h-[600px] rounded-full bg-indigo-600/10 blur-[160px]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_20%,rgba(5,5,8,0.9)_100%)]" />
        
        {/* Subtle developer grid lines */}
        <div 
          className="absolute inset-0 opacity-[0.03]" 
          style={{ 
            backgroundImage: 'linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)',
            backgroundSize: '48px 48px'
          }} 
        />
      </div>

      {/* Top Header Bar */}
      <header className="relative z-10 w-full max-w-5xl flex items-center justify-between border-b border-white/[0.08] pb-5">
        <div 
          onClick={() => navigate(isAuthenticated ? '/dashboard' : '/')}
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          {/* Logo Glyph */}
          <div className="w-8 h-8 rounded-xl bg-white flex items-center justify-center text-black font-black text-sm shadow-md group-hover:scale-105 transition-transform">
            V
          </div>
          <span className="font-['Playfair_Display',Georgia,serif] text-lg font-bold tracking-tight text-white">
            VerifAI
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-white/[0.07] border border-white/10 text-cyan-300 ml-1">
            404_DIAGNOSTIC
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate(-1)}
            className="px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 text-xs font-mono text-white/80 hover:text-white flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <CornerDownLeft size={13} className="text-cyan-400" />
            <span>cd .. (Back)</span>
          </button>
        </div>
      </header>

      {/* Main 404 Hero Container */}
      <main className="relative z-10 w-full max-w-3xl flex flex-col items-center text-center my-auto py-8">
        
        {/* Holographic Glowing 404 Display */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="relative inline-flex items-center justify-center mb-4"
        >
          <span className="text-8xl sm:text-9xl md:text-[130px] font-black tracking-tighter bg-gradient-to-r from-cyan-400 via-fuchsia-400 to-indigo-400 bg-clip-text text-transparent select-none drop-shadow-[0_0_35px_rgba(217,70,239,0.3)]">
            404
          </span>
          
          <div className="absolute -bottom-2 px-3 py-0.5 rounded-full bg-[#0d0e17] border border-white/15 backdrop-blur-md flex items-center gap-1.5 shadow-lg">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
            <span className="text-[10px] font-mono tracking-wider uppercase text-white/80">
              UNRESOLVED_ROUTE: {location.pathname}
            </span>
          </div>
        </motion.div>

        {/* Editorial Headline */}
        <motion.h1 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="text-2xl sm:text-3xl md:text-4xl font-['Playfair_Display',Georgia,serif] font-medium tracking-tight text-white mb-3"
        >
          Vector Coordinate Lost in Latent Space
        </motion.h1>

        {/* Human-Readable Developer Explanation */}
        <motion.p 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="text-sm sm:text-[15px] text-white/60 max-w-lg mb-8 leading-relaxed font-normal"
        >
          The route or document node you attempted to access does not exist on this cluster, has been pruned, or requires updated verification credentials.
        </motion.p>

        {/* Primary Call to Action Buttons */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="flex flex-wrap items-center justify-center gap-3.5 mb-12"
        >
          <button
            onClick={() => navigate(isAuthenticated ? '/dashboard' : '/')}
            className="px-6 py-3 rounded-xl bg-white hover:bg-neutral-200 active:scale-[0.98] text-black font-semibold text-xs sm:text-sm flex items-center gap-2 shadow-[0_0_24px_rgba(255,255,255,0.2)] transition-all cursor-pointer"
          >
            <Home size={16} />
            <span>{isAuthenticated ? 'Return to Dashboard' : 'Return to Sign In'}</span>
          </button>

          <button
            onClick={() => navigate('/verify')}
            className="px-6 py-3 rounded-xl bg-white/[0.08] hover:bg-white/[0.14] active:scale-[0.98] border border-white/15 text-white font-medium text-xs sm:text-sm flex items-center gap-2 transition-all cursor-pointer"
          >
            <Search size={16} className="text-cyan-400" />
            <span>Launch Fact Verifier</span>
          </button>

          <button
            onClick={() => navigate(-1)}
            className="px-5 py-3 rounded-xl bg-transparent hover:bg-white/[0.05] text-white/70 hover:text-white font-medium text-xs sm:text-sm flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <ArrowLeft size={15} />
            <span>Go Back</span>
          </button>
        </motion.div>

        {/* Quick Navigation Card Matrix */}
        <div className="w-full text-left">
          <div className="flex items-center gap-2 mb-3 px-1 text-white/40 text-[11px] font-mono uppercase tracking-wider">
            <Compass size={13} className="text-cyan-400" />
            <span>Valid Cluster Destinations</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {quickLinks.map((link) => {
              const Icon = link.icon;
              return (
                <div
                  key={link.path}
                  onClick={() => navigate(link.path)}
                  className="p-3.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.06] hover:border-cyan-500/30 transition-all cursor-pointer group flex items-start gap-3"
                >
                  <div className="w-8 h-8 rounded-lg bg-white/[0.06] group-hover:bg-cyan-500/20 text-white/80 group-hover:text-cyan-300 flex items-center justify-center shrink-0 transition-colors mt-0.5">
                    <Icon size={16} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white group-hover:text-cyan-200 transition-colors">
                        {link.title}
                      </span>
                      <span className="text-[10px] font-mono text-white/30 uppercase">
                        {link.tag}
                      </span>
                    </div>
                    <p className="text-[11px] text-white/50 truncate mt-0.5">
                      {link.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </main>

      {/* Developer Telemetry & Status Footer */}
      <footer className="relative z-10 w-full max-w-5xl border-t border-white/[0.08] pt-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] font-mono text-white/40">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
          <span>VERIFAI_OS 2.4.0 • ALL VERIFICATION CLUSTERS NORMAL</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="hover:text-white cursor-pointer transition-colors" onClick={() => navigate('/terms')}>
            Terms
          </span>
          <span>•</span>
          <span className="hover:text-white cursor-pointer transition-colors" onClick={() => navigate('/privacy')}>
            Privacy
          </span>
          <span>•</span>
          <span>HTTP 404 NOT FOUND</span>
        </div>
      </footer>

    </div>
  );
};

export default NotFoundPage;
