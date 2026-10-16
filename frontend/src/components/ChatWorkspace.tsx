import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Paperclip,
  Mic,
  Sparkles,
  FileText,
  Trash2,
  Download,
  Terminal,
  Cpu,
  Zap,
} from 'lucide-react';
import { ChatMessage } from '../services/api';
import { sound } from '../services/sound';
import { ArcReactor } from './ArcReactor';

interface ChatWorkspaceProps {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  isLoading: boolean;
  reactorState: 'idle' | 'listening' | 'thinking' | 'speaking' | 'error';
  onClearChat: () => void;
  onVoiceTrigger: () => void;
}

export const ChatWorkspace: React.FC<ChatWorkspaceProps> = ({
  messages,
  onSendMessage,
  isLoading,
  reactorState,
  onClearChat,
  onVoiceTrigger,
}) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    sound.playClick();
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleChipClick = (action: string) => {
    sound.playClick();
    let prompt = '';
    if (action === 'Explain') prompt = 'Explain this concept deeper with first-principles derivation.';
    else if (action === 'Simulate') prompt = 'Simulate this circuit with component tolerances and transient response.';
    else if (action === 'Find Similar') prompt = 'Find similar engineering circuit topologies and alternative ICs.';
    else if (action === 'Give Questions') prompt = 'Generate 3 rigorous engineering interview questions based on this.';
    else if (action === 'Summary') prompt = 'Summarize key takeaways into an executive engineering spec.';
    
    if (prompt) {
      onSendMessage(prompt);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950/60 overflow-hidden relative">
      {/* Top Header Bar */}
      <header className="px-6 py-3.5 border-b border-cyan-500/20 bg-slate-900/40 backdrop-blur-md flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
          <div>
            <h1 className="font-orbitron font-bold text-sm tracking-wider text-cyan-200">
              MR. STARK // TACTICAL INTELLIGENCE COMMAND
            </h1>
            <div className="flex items-center space-x-3 text-[11px] font-mono text-cyan-500/70">
              <span>CORE: GEMINI-3.6-FLASH</span>
              <span>•</span>
              <span>PERSONALITY: ADAPTIVE (SARCASTIC & WITTY)</span>
              <span>•</span>
              <span className="text-emerald-400">STATUS: NOMINAL</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              sound.playClick();
              onClearChat();
            }}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-400 hover:text-rose-400 bg-slate-900/60 hover:bg-rose-950/30 border border-slate-800 hover:border-rose-500/30 transition-all"
            title="Clear Chat History"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>CLEAR</span>
          </button>
        </div>
      </header>

      {/* Messages Scroll View */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 stark-holo-grid">
        {messages.map((msg) => {
          const isStark = msg.sender === 'stark';
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isStark ? 'items-start' : 'items-end'}`}
            >
              {/* Message Meta Info */}
              <div
                className={`flex items-center space-x-2 text-[11px] font-mono mb-1.5 px-1 ${
                  isStark ? 'text-cyan-400' : 'text-slate-400'
                }`}
              >
                {isStark ? (
                  <>
                    <span className="font-semibold text-cyan-300">MR. STARK</span>
                    <span className="text-cyan-600">::</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950/80 border border-cyan-500/30 text-cyan-300">
                      {msg.detectedState || 'CHIEF ARCHITECT'}
                    </span>
                  </>
                ) : (
                  <>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800/80 border border-slate-700 text-slate-300">
                      LEAD ENGINEER
                    </span>
                    <span className="text-slate-500">::</span>
                    <span className="font-semibold text-slate-300">YOU</span>
                  </>
                )}
                <span className="text-slate-600 text-[10px]">{msg.timestamp}</span>
              </div>

              {/* Message Bubble Card */}
              <div
                className={`max-w-2xl rounded-xl p-4 transition-all ${
                  isStark
                    ? 'bg-slate-900/85 border border-cyan-500/30 text-slate-100 shadow-[0_4px_25px_rgba(0,240,255,0.06)]'
                    : 'bg-cyan-950/35 border border-cyan-500/40 text-cyan-100 shadow-[0_4px_20px_rgba(0,0,0,0.4)]'
                }`}
              >
                {/* User Attachment pill if present */}
                {msg.attachments && msg.attachments.length > 0 && (
                  <div className="mb-3 flex flex-wrap gap-2">
                    {msg.attachments.map((att, i) => (
                      <div
                        key={i}
                        className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-950/80 border border-cyan-500/30 text-xs font-mono text-cyan-300"
                      >
                        <FileText className="w-3.5 h-3.5 text-cyan-400" />
                        <span>{att}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Message Content with Markdown & Math formatting */}
                <div className="text-sm leading-relaxed whitespace-pre-wrap font-sans">
                  {msg.text}
                </div>

                {/* Stark Action Chips (Only under Stark's messages) */}
                {isStark && (
                  <div className="mt-4 pt-3 border-t border-cyan-500/15 flex flex-wrap gap-1.5">
                    {['Explain', 'Simulate', 'Find Similar', 'Give Questions', 'Summary'].map(
                      (action) => (
                        <button
                          key={action}
                          onClick={() => handleChipClick(action)}
                          className="px-2.5 py-1 rounded-md text-[11px] font-mono bg-cyan-950/50 hover:bg-cyan-900/60 border border-cyan-500/25 hover:border-cyan-400/60 text-cyan-300 hover:text-cyan-100 transition-all shadow-sm"
                        >
                          [{action}]
                        </button>
                      )
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex flex-col items-start space-y-1">
            <div className="flex items-center space-x-2 text-[11px] font-mono text-cyan-400 px-1">
              <span className="font-semibold text-cyan-300">MR. STARK</span>
              <span className="text-cyan-600">::</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950/80 border border-cyan-500/30 text-cyan-300">
                COMPUTING NEURAL TENSORS...
              </span>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-cyan-500/30 text-cyan-300 flex items-center space-x-3">
              <div className="w-3 h-3 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-xs font-mono text-cyan-200">
                Stark Intelligence is formulating a response...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Composer Dock */}
      <footer className="p-4 border-t border-cyan-500/20 bg-slate-900/80 backdrop-blur-md">
        <form onSubmit={handleSubmit} className="flex items-center space-x-3">
          {/* Attachment Button */}
          <button
            type="button"
            onClick={() => sound.playClick()}
            className="p-2.5 rounded-lg bg-slate-950/80 border border-cyan-500/25 text-slate-400 hover:text-cyan-300 hover:border-cyan-400/50 transition-all"
            title="Attach Schematic, PDF, or CAD file"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          {/* Text Input Box */}
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask Mr. Stark anything... or run an engineering simulation"
              disabled={isLoading}
              className="w-full bg-slate-950/90 border border-cyan-500/30 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all font-sans"
            />
          </div>

          {/* Voice Mic Button */}
          <button
            type="button"
            onClick={() => {
              sound.playClick();
              onVoiceTrigger();
            }}
            className={`p-3 rounded-xl border transition-all ${
              reactorState === 'listening'
                ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200 shadow-glow-cyan animate-pulse'
                : 'bg-slate-950/80 border-cyan-500/25 text-slate-400 hover:text-cyan-300 hover:border-cyan-400/50'
            }`}
            title="Trigger Voice Dictation"
          >
            <Mic className="w-4 h-4" />
          </button>

          {/* Send Button */}
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            className="p-3 rounded-xl bg-gradient-to-r from-cyan-500 to-cyan-400 text-slate-950 hover:from-cyan-400 hover:to-cyan-300 disabled:opacity-40 disabled:cursor-not-allowed font-bold shadow-glow-cyan transition-all"
            title="Transmit Message"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </footer>
    </div>
  );
};
