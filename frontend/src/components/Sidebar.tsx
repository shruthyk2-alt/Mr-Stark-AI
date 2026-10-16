import React from 'react';
import {
  MessageSquare,
  Wrench,
  Cpu,
  FolderLock,
  FileText,
  Code2,
  Eye,
  Shield,
  Search,
  Database,
  Activity,
  Settings,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { ArcReactor } from './ArcReactor';
import { sound } from '../services/sound';

export type NavItem =
  | 'chat'
  | 'engineering'
  | 'electronics'
  | 'vault'
  | 'notes'
  | 'code'
  | 'visual'
  | 'exosuit'
  | 'research'
  | 'memory'
  | 'monitor'
  | 'settings';

interface SidebarProps {
  activeItem: NavItem;
  onSelectItem: (item: NavItem) => void;
  voiceActive: boolean;
  onToggleVoice: () => void;
  isMuted: boolean;
  onToggleMute: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeItem,
  onSelectItem,
  voiceActive,
  onToggleVoice,
  isMuted,
  onToggleMute,
}) => {
  const navList: { id: NavItem; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: 'chat', label: 'Chat Workspace', icon: <MessageSquare className="w-4 h-4" /> },
    { id: 'engineering', label: 'Engineering Tools', icon: <Wrench className="w-4 h-4" /> },
    { id: 'electronics', label: 'Electronics Solver', icon: <Cpu className="w-4 h-4" />, badge: 'AI' },
    { id: 'vault', label: 'Project Vault', icon: <FolderLock className="w-4 h-4" /> },
    { id: 'notes', label: 'Notes & PDFs', icon: <FileText className="w-4 h-4" /> },
    { id: 'code', label: 'Code Assistant', icon: <Code2 className="w-4 h-4" /> },
    { id: 'visual', label: 'Visual Lab', icon: <Eye className="w-4 h-4" /> },
    { id: 'exosuit', label: 'Exo-Suit Lab', icon: <Shield className="w-4 h-4" />, badge: '3D' },
    { id: 'research', label: 'Research Mode', icon: <Search className="w-4 h-4" /> },
    { id: 'memory', label: 'Memory & Context', icon: <Database className="w-4 h-4" /> },
    { id: 'monitor', label: 'System Monitor', icon: <Activity className="w-4 h-4" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="w-4 h-4" /> },
  ];

  const handleNavClick = (id: NavItem) => {
    sound.playClick();
    onSelectItem(id);
  };

  return (
    <aside className="w-64 h-screen bg-slate-950/90 border-r border-cyan-500/20 flex flex-col justify-between shrink-0 select-none backdrop-blur-xl">
      {/* Top Header with Miniature Arc Reactor */}
      <div className="p-4 border-b border-cyan-500/20 bg-slate-900/40">
        <div className="flex items-center space-x-3">
          <div className="w-11 h-11 rounded-full p-0.5 border border-cyan-500/40 bg-slate-950 flex items-center justify-center shadow-glow-cyan">
            <ArcReactor size={40} interactive={false} />
          </div>
          <div className="flex flex-col">
            <span className="font-orbitron font-bold text-sm tracking-wider text-cyan-300">
              MR. STARK
            </span>
            <span className="text-[10px] uppercase font-mono tracking-widest text-cyan-500/70">
              TACTICAL OS v2.0
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Links Scroll Container */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
        {navList.map((item) => {
          const isActive = activeItem === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all group ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/25 to-transparent text-cyan-200 border-l-2 border-cyan-400 font-semibold shadow-[inset_0_0_12px_rgba(0,240,255,0.15)]'
                  : 'text-slate-400 hover:text-cyan-300 hover:bg-slate-900/60'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <span
                  className={`transition-colors ${
                    isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-cyan-400'
                  }`}
                >
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/30 text-cyan-400">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Voice Mode Control & Audio Settings */}
      <div className="p-3 border-t border-cyan-500/20 bg-slate-900/60 space-y-2">
        {/* Voice Toggle Button */}
        <button
          onClick={onToggleVoice}
          className={`w-full py-2 px-3 rounded-lg flex items-center justify-between text-xs font-mono transition-all border ${
            voiceActive
              ? 'bg-cyan-500/20 border-cyan-400 text-cyan-200 shadow-glow-cyan'
              : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:border-cyan-500/40 hover:text-cyan-300'
          }`}
        >
          <div className="flex items-center space-x-2">
            {voiceActive ? (
              <Mic className="w-4 h-4 text-cyan-400 animate-pulse" />
            ) : (
              <MicOff className="w-4 h-4 text-slate-500" />
            )}
            <span className="font-semibold">{voiceActive ? 'VOICE: ACTIVE' : 'VOICE: MUTED'}</span>
          </div>
          <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#00f0ff]" />
        </button>

        {/* Audio Mute & Diagnostics Bar */}
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 px-1 pt-1">
          <button
            onClick={onToggleMute}
            className="flex items-center space-x-1 hover:text-cyan-300 transition-colors"
            title="Toggle SFX Mute"
          >
            {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
            <span>{isMuted ? 'SFX MUTED' : 'SFX ON'}</span>
          </button>
          <span className="text-[9px] text-cyan-600">STARK_IND::v2.0</span>
        </div>
      </div>
    </aside>
  );
};
