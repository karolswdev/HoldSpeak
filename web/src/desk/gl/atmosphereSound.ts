import { useEffect } from "react";
import { micPhase } from "../../lib/micSession";
import { observeAtmosphereActivity } from "./atmosphereActivity";
import { useAtmosphereControls } from "./atmosphereControls";
import type { AtmosphereId } from "./atmosphereRegistry";

// Locally synthesized room tone, intentionally quiet. No downloaded samples,
// speech, timers posing as product events, or additional capture sessions.
const VOICES: Partial<
  Record<
    AtmosphereId,
    {
      noise: number;
      cutoff: number;
      hum: number;
      humGain: number;
      pulse?: number;
    }
  >
> = {
  "radio-station": { noise: 0.025, cutoff: 1600, hum: 60, humGain: 0.006 },
  "midnight-archive": { noise: 0.014, cutoff: 350, hum: 90, humGain: 0.002 },
  "night-train": {
    noise: 0.065,
    cutoff: 700,
    hum: 48,
    humGain: 0.009,
    pulse: 1.7,
  },
  "deep-sea": {
    noise: 0.075,
    cutoff: 230,
    hum: 42,
    humGain: 0.01,
    pulse: 0.08,
  },
  greenhouse: { noise: 0.03, cutoff: 2900, hum: 110, humGain: 0.0007 },
  laundromat: {
    noise: 0.035,
    cutoff: 620,
    hum: 60,
    humGain: 0.007,
    pulse: 0.65,
  },
  "rainy-city": { noise: 0.035, cutoff: 2200, hum: 60, humGain: 0.001 },
  "lantern-garden": { noise: 0.024, cutoff: 2500, hum: 100, humGain: 0.0005 },
};

export function useAtmosphereSound(id: AtmosphereId) {
  const { sound } = useAtmosphereControls();
  useEffect(() => {
    const voice = VOICES[id];
    if (!sound || !voice || typeof AudioContext === "undefined") return;
    const activity = observeAtmosphereActivity();
    const context = new AudioContext();
    const master = context.createGain();
    master.gain.value = 0;
    master.connect(context.destination);
    const buffer = context.createBuffer(
      1,
      context.sampleRate * 4,
      context.sampleRate,
    );
    const samples = buffer.getChannelData(0);
    for (let i = 0; i < samples.length; i++) samples[i] = Math.random() * 2 - 1;
    const noise = context.createBufferSource();
    noise.buffer = buffer;
    noise.loop = true;
    const filter = context.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = voice.cutoff;
    filter.Q.value = 0.4;
    const noiseGain = context.createGain();
    noiseGain.gain.value = voice.noise;
    noise.connect(filter).connect(noiseGain).connect(master);
    const hum = context.createOscillator();
    hum.frequency.value = voice.hum;
    const humGain = context.createGain();
    humGain.gain.value = voice.humGain;
    hum.connect(humGain).connect(master);
    const sources: Array<AudioScheduledSourceNode> = [noise, hum];
    const nodes: AudioNode[] = [noise, filter, noiseGain, hum, humGain, master];
    if (voice.pulse) {
      const pulse = context.createOscillator();
      pulse.frequency.value = voice.pulse;
      const depth = context.createGain();
      depth.gain.value = voice.noise * 0.25;
      pulse.connect(depth).connect(noiseGain.gain);
      sources.push(pulse);
      nodes.push(pulse, depth);
    }
    sources.forEach((source) => source.start());
    let destroyed = false;
    const sync = () => {
      if (destroyed) return;
      // Silence the room whenever a microphone is held, even between speech
      // segments. Ambience must never leak into the product's own capture.
      const muted =
        activity.read().recording || micPhase() !== "closed" || document.hidden;
      master.gain.cancelScheduledValues(context.currentTime);
      master.gain.setTargetAtTime(
        muted ? 0 : 0.8,
        context.currentTime,
        muted ? 0.015 : 0.5,
      );
      if (document.hidden) void context.suspend().catch(() => undefined);
    };
    const resume = () => {
      if (!destroyed && !document.hidden)
        void context
          .resume()
          .then(sync)
          .catch(() => undefined);
    };
    const visibility = () => {
      sync();
      if (!document.hidden) resume();
    };
    const unsubscribe = activity.subscribe(sync);
    document.addEventListener("visibilitychange", visibility);
    // Browsers may require a gesture after a saved opt-in has reloaded.
    window.addEventListener("pointerdown", resume);
    window.addEventListener("keydown", resume);
    sync();
    resume();
    return () => {
      destroyed = true;
      unsubscribe();
      activity.dispose();
      document.removeEventListener("visibilitychange", visibility);
      window.removeEventListener("pointerdown", resume);
      window.removeEventListener("keydown", resume);
      sources.forEach((source) => source.stop());
      nodes.forEach((node) => node.disconnect());
      void context.close().catch(() => undefined);
    };
  }, [id, sound]);
}
