import React, { useEffect, useRef } from 'react';
import { ExosuitViewer } from './ExosuitViewer';
import { TelemetryData } from '../services/api';
import { Activity, ShieldCheck, Zap, Thermometer, BatteryCharging, HardDrive, Cpu } from 'lucide-react';

interface TelemetryPanelProps {
  telemetry: TelemetryData | null;
}

export const TelemetryPanel: React.FC<TelemetryPanelProps> = ({ telemetry }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Oscilloscope waveform animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let offset = 0;

    const render = () => {
      animId = requestAnimationFrame(render);
      offset += 0.04;

      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      // Draw faint grid
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.08)';
      ctx.lineWidth = 1;
      for (let x = 0; x < w; x += 20) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += 15) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Draw primary cyan waveform
      ctx.strokeStyle = '#00f0ff';
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      for (let x = 0; x < w; x++) {
        const rad = (x / w) * Math.PI * 4 + offset;
        const y = h / 2 + Math.sin(rad) * 12 + Math.sin(rad * 2.5 + offset * 1.5) * 5;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Draw secondary faint blue harmonic wave
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let x = 0; x < w; x++) {
        const rad = (x / w) * Math.PI * 6 - offset * 1.2;
        const y = h / 2 + Math.cos(rad) * 8 + Math.sin(rad * 0.8) * 4;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, []);

  const armor = telemetry?.armor_percent ?? 98;
  const unibeam = telemetry?.unibeam_percent ?? 87;
  const temp = telemetry?.core_temp ?? 32;
  const battery = telemetry?.battery_percent ?? 76;
  const cpu = telemetry?.cpu_percent ?? 14.2;
  const ram = telemetry?.memory_percent ?? 48.6;

  return (
    <aside className="w-[390px] h-screen bg-slate-950/90 border-l border-cyan-500/20 flex flex-col justify-between shrink-0 p-4 space-y-4 overflow-y-auto backdrop-blur-xl">
      {/* 1. 3D Exosuit Interactive Viewer */}
      <ExosuitViewer />

      {/* 2. Mark VII Suit Stats */}
      <div className="bg-slate-900/60 border border-cyan-500/20 rounded-xl p-3.5 space-y-3">
        <div className="flex items-center justify-between text-xs font-orbitron text-cyan-300 border-b border-cyan-500/20 pb-2">
          <div className="flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <span>MARK VII INTEGRITY</span>
          </div>
          <span className="font-mono text-[10px] text-cyan-400">STATUS: COMBAT READY</span>
        </div>

        <div className="space-y-2.5 text-xs font-mono">
          {/* Armor */}
          <div>
            <div className="flex justify-between text-slate-300 mb-1">
              <span className="text-[11px]">ARMOR PLATING</span>
              <span className="text-cyan-300 font-bold">{armor}%</span>
            </div>
            <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-cyan-500/20">
              <div
                className="bg-gradient-to-r from-cyan-600 to-cyan-400 h-1.5 rounded-full shadow-[0_0_8px_#00f0ff]"
                style={{ width: `${armor}%` }}
              />
            </div>
          </div>

          {/* Unibeam */}
          <div>
            <div className="flex justify-between text-slate-300 mb-1">
              <span className="text-[11px]">UNIBEAM OUTPUT</span>
              <span className="text-cyan-300 font-bold">{unibeam}%</span>
            </div>
            <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-cyan-500/20">
              <div
                className="bg-gradient-to-r from-cyan-600 to-cyan-400 h-1.5 rounded-full shadow-[0_0_8px_#00f0ff]"
                style={{ width: `${unibeam}%` }}
              />
            </div>
          </div>

          {/* Stats Grid: Temp & Battery */}
          <div className="grid grid-cols-2 gap-2 pt-1">
            <div className="bg-slate-950/80 p-2 rounded-lg border border-cyan-500/20 flex items-center space-x-2">
              <Thermometer className="w-4 h-4 text-amber-400" />
              <div>
                <div className="text-[9px] text-slate-400">CORE TEMP</div>
                <div className="text-xs font-bold text-amber-300">{temp}°C</div>
              </div>
            </div>
            <div className="bg-slate-950/80 p-2 rounded-lg border border-cyan-500/20 flex items-center space-x-2">
              <BatteryCharging className="w-4 h-4 text-emerald-400" />
              <div>
                <div className="text-[9px] text-slate-400">REPULSOR CELL</div>
                <div className="text-xs font-bold text-emerald-300">{battery}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. System Host Metrics */}
      <div className="bg-slate-900/60 border border-cyan-500/20 rounded-xl p-3.5 space-y-2">
        <div className="flex items-center justify-between text-xs font-orbitron text-cyan-300 border-b border-cyan-500/20 pb-2">
          <div className="flex items-center space-x-1.5">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>HOST SYSTEM TELEMETRY</span>
          </div>
          <span className="font-mono text-[10px] text-emerald-400">LIVE FEED</span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
          <div className="bg-slate-950/80 p-2 rounded-lg border border-cyan-500/20">
            <div className="text-[10px] text-slate-400">CPU LOAD</div>
            <div className="text-sm font-bold text-cyan-300">{cpu.toFixed(1)}%</div>
          </div>
          <div className="bg-slate-950/80 p-2 rounded-lg border border-cyan-500/20">
            <div className="text-[10px] text-slate-400">RAM USAGE</div>
            <div className="text-sm font-bold text-cyan-300">{ram.toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* 4. Live Data Stream Oscilloscope */}
      <div className="bg-slate-900/60 border border-cyan-500/20 rounded-xl p-3 space-y-2">
        <div className="flex items-center justify-between text-[11px] font-orbitron text-cyan-300">
          <div className="flex items-center space-x-1.5">
            <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span>LIVE DATA STREAM</span>
          </div>
          <span className="font-mono text-[9px] text-cyan-500">142.85 MHz // FLUX</span>
        </div>

        <div className="w-full h-16 bg-slate-950 rounded-lg border border-cyan-500/20 overflow-hidden flex items-center justify-center">
          <canvas ref={canvasRef} width={340} height={64} className="w-full h-full" />
        </div>
      </div>
    </aside>
  );
};
