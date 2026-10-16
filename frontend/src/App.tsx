import React, { useState, useEffect } from 'react';
import { Sidebar, NavItem } from './components/Sidebar';
import { ChatWorkspace } from './components/ChatWorkspace';
import { TelemetryPanel } from './components/TelemetryPanel';
import { StartupSequence } from './components/StartupSequence';
import { ChatMessage, TelemetryData, sendChatMessage, fetchTelemetry } from './services/api';
import { sound } from './services/sound';

export const App: React.FC = () => {
  const [isStarted, setIsStarted] = useState<boolean>(false);
  const [activeNav, setActiveNav] = useState<NavItem>('chat');
  const [voiceActive, setVoiceActive] = useState<boolean>(true);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [reactorState, setReactorState] = useState<'idle' | 'listening' | 'thinking' | 'speaking' | 'error'>('idle');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);

  // Initial reference messages matching the design specification & visual reference
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-1',
      sender: 'user',
      text: 'Analyze this inverting op-amp circuit. Derive the voltage gain formula and calculate output voltage for Vin = 0.5V, R1 = 10kΩ, and Rf = 100kΩ.',
      timestamp: '11:42 AM',
      attachments: ['circuit_schematic.pdf', 'opamp_specs.json'],
    },
    {
      id: 'msg-2',
      sender: 'stark',
      text: `Well, look who finally remembered what an operational amplifier looks like. Let's do the math before you accidentally solder your fingers together.

In an ideal inverting op-amp configuration with negative feedback:
1. Virtual Ground: The non-inverting terminal (+) is grounded, so V_⁻ ≈ 0V.
2. High Input Impedance: No current enters the inverting terminal (I_in = 0).

Applying Kirchhoff's Current Law at the inverting summing junction:
I_1 = (V_in - 0) / R_1
I_f = (0 - V_out) / R_f
Since I_1 + I_f = 0:

Gain Formula:
Av = - (Rf / R1) = - (100 kΩ / 10 kΩ) = -10

Output Voltage Calculation:
V_out = Av × V_in = -10 × 0.5V = -5.0 V

Notice the 180° phase inversion. Make sure your split power rail supplies at least ±7V to avoid rail clipping and saturation distortion. Now, are we building this or just admiring the numbers?`,
      timestamp: '11:42 AM',
      detectedState: 'SARCASTIC & ANALYTICAL',
    },
  ]);

  // Polling telemetry
  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    const updateStats = async () => {
      try {
        const data = await fetchTelemetry();
        setTelemetry(data);
      } catch (err) {
        // Fallback default
        setTelemetry({
          cpu_percent: 18.4,
          memory_percent: 46.2,
          disk_percent: 54.1,
          timestamp: new Date().toISOString(),
          armor_percent: 98,
          unibeam_percent: 87,
          core_temp: 32,
          battery_percent: 76,
        });
      }
    };

    updateStats();
    timer = setInterval(updateStats, 4500);
    return () => clearInterval(timer);
  }, []);

  const handleSendMessage = async (text: string) => {
    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setReactorState('thinking');

    try {
      const data = await sendChatMessage(text);
      const starkMsg: ChatMessage = {
        id: `stark-${Date.now()}`,
        sender: 'stark',
        text: data.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        detectedState: data.detected_state.toUpperCase(),
      };
      setMessages((prev) => [...prev, starkMsg]);
      sound.playMessagePing();
      setReactorState('speaking');
      setTimeout(() => setReactorState('idle'), 2400);
    } catch (err: unknown) {
      const errorText = err instanceof Error ? err.message : String(err);
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'stark',
        text: `Diagnostics alert: Backend connection stuttered. Details: ${errorText}\n\nMake sure the local Python FastAPI service is running on port 8000.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        detectedState: 'SYSTEM FAULT',
      };
      setMessages((prev) => [...prev, errorMsg]);
      setReactorState('error');
      setTimeout(() => setReactorState('idle'), 4000);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  const handleToggleVoice = () => {
    sound.playClick();
    setVoiceActive(!voiceActive);
  };

  const handleToggleMute = () => {
    const nextMute = !isMuted;
    setIsMuted(nextMute);
    sound.setMuted(nextMute);
  };

  const handleVoiceTrigger = () => {
    setReactorState('listening');
    sound.playPulse();
    setTimeout(() => {
      setReactorState('idle');
    }, 3000);
  };

  // Render Cinematic Startup Sequence first
  if (!isStarted) {
    return <StartupSequence onInitialize={() => setIsStarted(true)} />;
  }

  // Render Full Command Centre
  return (
    <div className="w-screen h-screen flex bg-stark-darkest text-slate-100 overflow-hidden font-sans">
      {/* 1. Left Navigation Sidebar */}
      <Sidebar
        activeItem={activeNav}
        onSelectItem={setActiveNav}
        voiceActive={voiceActive}
        onToggleVoice={handleToggleVoice}
        isMuted={isMuted}
        onToggleMute={handleToggleMute}
      />

      {/* 2. Center Chat & Engineering Workspace */}
      <ChatWorkspace
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        reactorState={reactorState}
        onClearChat={handleClearChat}
        onVoiceTrigger={handleVoiceTrigger}
      />

      {/* 3. Right Telemetry & 3D Exosuit Panel */}
      <TelemetryPanel telemetry={telemetry} />
    </div>
  );
};
