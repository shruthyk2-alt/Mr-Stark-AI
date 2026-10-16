/**
 * Procedural Web Audio API Sound Synthesizer for Mr. Stark
 * Creates authentic sci-fi sound effects directly in the browser without external audio assets.
 */

class SoundSystem {
  private ctx: AudioContext | null = null;
  private isMuted: boolean = false;
  private volume: number = 0.65;

  private getContext(): AudioContext | null {
    if (typeof window === 'undefined') return null;
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  public setMuted(muted: boolean) {
    this.isMuted = muted;
  }

  public getMuted(): boolean {
    return this.isMuted;
  }

  public setVolume(vol: number) {
    this.volume = Math.max(0, Math.min(1, vol));
  }

  public getVolume(): number {
    return this.volume;
  }

  /**
   * The signature Stark "Chak-Kshing" activation sequence:
   * 1. High-speed metallic latch "chak" (high-passed noise burst + 880Hz click)
   * 2. Powerful unibeam energy ignition "kshing" (exponential sub-bass sweep + metallic resonant filter sweep)
   */
  public playBootSequence() {
    if (this.isMuted) return;
    const ctx = this.getContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const master = ctx.createGain();
    master.gain.setValueAtTime(this.volume, now);
    master.connect(ctx.destination);

    // --- PHASE 1: "CHAK" (Metallic mechanical latch at T=0.0s) ---
    // Mechanical click oscillator
    const clickOsc = ctx.createOscillator();
    const clickGain = ctx.createGain();
    clickOsc.type = 'triangle';
    clickOsc.frequency.setValueAtTime(1200, now);
    clickOsc.frequency.exponentialRampToValueAtTime(180, now + 0.04);
    clickGain.gain.setValueAtTime(0.7, now);
    clickGain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
    clickOsc.connect(clickGain);
    clickGain.connect(master);
    clickOsc.start(now);
    clickOsc.stop(now + 0.06);

    // Snappy noise click
    const bufferSize = ctx.sampleRate * 0.05;
    const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = noiseBuffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }
    const noise = ctx.createBufferSource();
    noise.buffer = noiseBuffer;
    const noiseFilter = ctx.createBiquadFilter();
    noiseFilter.type = 'bandpass';
    noiseFilter.frequency.setValueAtTime(3200, now);
    noiseFilter.Q.setValueAtTime(4, now);
    const noiseGain = ctx.createGain();
    noiseGain.gain.setValueAtTime(0.8, now);
    noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
    noise.connect(noiseFilter);
    noiseFilter.connect(noiseGain);
    noiseGain.connect(master);
    noise.start(now);
    noise.stop(now + 0.05);

    // --- PHASE 2: "KSHING" (Energy unibeam sweep at T=0.07s) ---
    const kshingStart = now + 0.07;

    // Resonant metallic sweep
    const kshingBufferSize = ctx.sampleRate * 0.8;
    const kshingBuffer = ctx.createBuffer(1, kshingBufferSize, ctx.sampleRate);
    const kData = kshingBuffer.getChannelData(0);
    for (let i = 0; i < kshingBufferSize; i++) {
      kData[i] = Math.random() * 2 - 1;
    }
    const kNoise = ctx.createBufferSource();
    kNoise.buffer = kshingBuffer;
    const kFilter = ctx.createBiquadFilter();
    kFilter.type = 'bandpass';
    kFilter.frequency.setValueAtTime(950, kshingStart);
    kFilter.frequency.exponentialRampToValueAtTime(4500, kshingStart + 0.25);
    kFilter.frequency.exponentialRampToValueAtTime(1200, kshingStart + 0.7);
    kFilter.Q.setValueAtTime(9, kshingStart);

    const kGain = ctx.createGain();
    kGain.gain.setValueAtTime(0.01, kshingStart);
    kGain.gain.linearRampToValueAtTime(0.85, kshingStart + 0.06);
    kGain.gain.exponentialRampToValueAtTime(0.001, kshingStart + 0.75);

    kNoise.connect(kFilter);
    kFilter.connect(kGain);
    kGain.connect(master);
    kNoise.start(kshingStart);
    kNoise.stop(kshingStart + 0.8);

    // Sub-bass arc reactor ignition rumble
    const subOsc = ctx.createOscillator();
    const subGain = ctx.createGain();
    subOsc.type = 'sine';
    subOsc.frequency.setValueAtTime(65, kshingStart);
    subOsc.frequency.exponentialRampToValueAtTime(140, kshingStart + 0.18);
    subOsc.frequency.exponentialRampToValueAtTime(42, kshingStart + 0.65);

    subGain.gain.setValueAtTime(0.01, kshingStart);
    subGain.gain.linearRampToValueAtTime(0.9, kshingStart + 0.08);
    subGain.gain.exponentialRampToValueAtTime(0.001, kshingStart + 0.7);

    subOsc.connect(subGain);
    subGain.connect(master);
    subOsc.start(kshingStart);
    subOsc.stop(kshingStart + 0.75);

    // Shimmering sci-fi harmonic chime
    const chimeOsc = ctx.createOscillator();
    const chimeGain = ctx.createGain();
    chimeOsc.type = 'sine';
    chimeOsc.frequency.setValueAtTime(2640, kshingStart + 0.05);
    chimeOsc.frequency.exponentialRampToValueAtTime(1760, kshingStart + 0.6);
    chimeGain.gain.setValueAtTime(0.25, kshingStart + 0.05);
    chimeGain.gain.exponentialRampToValueAtTime(0.001, kshingStart + 0.6);
    chimeOsc.connect(chimeGain);
    chimeGain.connect(master);
    chimeOsc.start(kshingStart + 0.05);
    chimeOsc.stop(kshingStart + 0.65);
  }

  /**
   * High-tech UI click for buttons and actions
   */
  public playClick() {
    if (this.isMuted) return;
    const ctx = this.getContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(1800, now);
    osc.frequency.exponentialRampToValueAtTime(450, now + 0.03);

    gain.gain.setValueAtTime(this.volume * 0.25, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.035);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.04);
  }

  /**
   * Sub-bass arc reactor hum & energy pulse
   */
  public playPulse() {
    if (this.isMuted) return;
    const ctx = this.getContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(110, now);
    osc.frequency.exponentialRampToValueAtTime(220, now + 0.12);
    osc.frequency.exponentialRampToValueAtTime(80, now + 0.35);

    gain.gain.setValueAtTime(0.01, now);
    gain.gain.linearRampToValueAtTime(this.volume * 0.4, now + 0.08);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.45);
  }

  /**
   * Incoming message notification ping
   */
  public playMessagePing() {
    if (this.isMuted) return;
    const ctx = this.getContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(987.77, now); // B5
    osc.frequency.setValueAtTime(1318.51, now + 0.08); // E6

    gain.gain.setValueAtTime(this.volume * 0.2, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.32);
  }
}

export const sound = new SoundSystem();
