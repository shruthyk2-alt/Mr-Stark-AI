/**
 * API client to communicate with the local Mr. Stark FastAPI backend
 */

export interface ChatMessage {
  id: string;
  sender: 'user' | 'stark';
  text: string;
  timestamp: string;
  detectedState?: string;
  attachments?: string[];
}

export interface TelemetryData {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  timestamp: string;
  armor_percent?: number;
  unibeam_percent?: number;
  core_temp?: number;
  battery_percent?: number;
}

export async function fetchHealth(): Promise<{ status: string; system: string }> {
  const res = await fetch('/api/health');
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchGreeting(): Promise<string> {
  try {
    const res = await fetch('/api/greeting');
    if (!res.ok) throw new Error('Failed to fetch greeting');
    const data = await res.json();
    return data.greeting;
  } catch (err) {
    return "Don't just stand there with your jaw unhinged. What are we building today?";
  }
}

export async function sendChatMessage(
  message: string,
  userTone?: string
): Promise<{ response: string; detected_state: string; token_count?: number }> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_tone: userTone }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Chat error (${res.status}): ${errText}`);
  }
  const data = await res.json();
  return {
    response: data.response || data.reply || 'No response received',
    detected_state: data.detected_state || data.persona || 'Adaptive Sarcastic Core',
    token_count: data.token_count || 0,
  };
}

export async function fetchTelemetry(): Promise<TelemetryData> {
  const res = await fetch('/api/telemetry');
  if (!res.ok) throw new Error('Telemetry fetch failed');
  const data = await res.json();
  return {
    cpu_percent: data.cpu_percent ?? 0,
    memory_percent: data.ram_percent ?? data.memory_percent ?? 0,
    disk_percent: data.disk_percent ?? 0,
    timestamp: data.timestamp || new Date().toISOString(),
    armor_percent: data.suit_stats?.armor_integrity ?? 98,
    unibeam_percent: data.suit_stats?.power_level ?? 87,
    core_temp: data.suit_stats?.temperature_c ?? 32,
    battery_percent: data.suit_stats?.battery_pct ?? 76,
  };
}
