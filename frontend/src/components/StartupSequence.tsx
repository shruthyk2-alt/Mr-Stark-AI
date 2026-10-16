import React, { useState, useEffect } from 'react';
import { ArcReactor } from './ArcReactor';
import { sound } from '../services/sound';
import { fetchGreeting } from '../services/api';
import { Sparkles, Terminal, Shield } from 'lucide-react';

interface StartupSequenceProps {
  onInitialize: () => void;
}

export const StartupSequence: React.FC<StartupSequenceProps> = ({ onInitialize }) => {
  const [greeting, setGreeting] = useState<string>('Initializing neural matrix...');
  const [isFiring, setIsFiring] = useState<boolean>(false);
  const [displayedText, setDisplayedText] = useState<string>('');

  useEffect(() => {
    let isMounted = true;
    fetchGreeting().then((text) => {
      if (isMounted) {
        setGreeting(text);
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  // Typewriter effect for greeting
  useEffect(() => {
    let index = 0;
    setDisplayedText('');
    const timer = setInterval(() => {
      if (index < greeting.length) {
        setDisplayedText(greeting.slice(0, index + 1));
        index++;
      } else {
        clearInterval(timer);
      }
    }, 28);
    return () => clearInterval(timer);
  }, [greeting]);

  const handleLaunch = () => {
    if (isFiring) return;
    setIsFiring(true);
    // Play the signature Chak-Kshing sound sequence!
    sound.playBootSequence();

    // Allow 850ms for sound + visual energy surge before entering main view
    setTimeout(() => {
      onInitialize();
    }, 850);
  };

  return (
    <div className="relative w-screen h-screen bg-[#020617] flex flex-col items-center justify-center select-none overflow-hidden stark-holo-grid">
      {/* Background radial glow */}
      <div className="absolute w-[600px] h-[600px] rounded-full bg-cyan-500/10 blur-[140px] pointer-events-none" />

      {/* Futuristic Scanline Overlay */}
      <div className="absolute inset-0 stark-scanlines pointer-events-none opacity-40" />

      {/* Main Center Card */}
      <div className="relative z-10 flex flex-col items-center max-w-xl text-center px-6">
        {/* Arc Reactor in 3D */}
        <div className={`transition-all duration-500 ${isFiring ? 'scale-125 filter drop-shadow-[0_0_60px_#00f0ff]' : 'hover:scale-105'}`}>
          <ArcReactor
            size={260}
            state={isFiring ? 'thinking' : 'idle'}
            onClick={handleLaunch}
            interactive={true}
          />
        </div>

        {/* Title */}
        <div className="mt-8 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-500/30 text-xs font-mono text-cyan-400">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span>MARK VII ARCHITECTURE // ONLINE</span>
          </div>

          <h1 className="font-orbitron font-extrabold text-3xl md:text-4xl tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-200 via-cyan-400 to-sky-300 drop-shadow-[0_0_20px_rgba(0,240,255,0.4)]">
            MR. STARK
          </h1>

          <p className="font-mono text-xs uppercase tracking-widest text-cyan-500/80">
            CINEMATIC AI COMMAND CENTRE & ENGINEERING SUITE
          </p>
        </div>

        {/* Sarcastic Stark Greeting Message Box */}
        <div className="mt-6 w-full min-h-[72px] p-4 rounded-xl bg-slate-900/80 border border-cyan-500/25 backdrop-blur-md text-left flex items-start space-x-3 shadow-lg">
          <Terminal className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
          <div className="text-sm font-sans text-cyan-100 italic leading-relaxed">
            "{displayedText}"
            <span className="inline-block w-1.5 h-4 ml-1 bg-cyan-400 animate-pulse" />
          </div>
        </div>

        {/* Big Futuristic Initialize Button */}
        <div className="mt-8">
          <button
            onClick={handleLaunch}
            disabled={isFiring}
            className={`px-8 py-3.5 rounded-xl font-orbitron font-bold text-sm tracking-wider uppercase transition-all duration-300 flex items-center space-x-3 border ${
              isFiring
                ? 'bg-cyan-400 text-slate-950 border-cyan-300 shadow-[0_0_40px_#00f0ff] scale-95'
                : 'bg-gradient-to-r from-cyan-500/30 via-cyan-400/20 to-cyan-500/30 text-cyan-200 border-cyan-400/60 hover:border-cyan-300 hover:text-white hover:bg-cyan-500/40 shadow-glow-cyan hover:scale-105 active:scale-95'
            }`}
          >
            <Sparkles className="w-4 h-4 text-cyan-300 animate-spin" />
            <span>{isFiring ? 'POWERING UNIBEAM...' : 'INITIALIZE SYSTEM'}</span>
          </button>
        </div>

        {/* Footer telemetry notice */}
        <div className="mt-10 font-mono text-[10px] text-slate-500">
          STARK INDUSTRIES // SYSTEM READY // CLICK OR HIT INITIALIZE TO ENGAGE
        </div>
      </div>
    </div>
  );
};
