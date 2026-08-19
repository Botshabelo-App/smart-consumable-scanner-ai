// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import { Platform } from "react-native";

export interface PerfSample {
  timestamp: number;
  scanId: string;
  durationMs: number;
  fps?: number;
  deviceInfo: {
    platform: string;
    osVersion?: string | number;
    model?: string;
  };
  memoryMB?: number;
  note?: string;
}

export interface ScanSession {
  scanId: string;
  startTime: number;
  frameCount: number;
  lastFrameTime: number;
  samples: PerfSample[];
}

const getTime = () =>
  typeof performance !== "undefined" && performance.now
    ? performance.now()
    : Date.now();

const requestFrame = (cb: () => void): number =>
  typeof requestAnimationFrame !== "undefined"
    ? (requestAnimationFrame(cb) as unknown as number)
    : (setTimeout(cb, 16) as unknown as number);

const cancelFrame = (id: number) => {
  if (typeof cancelAnimationFrame !== "undefined") {
    cancelAnimationFrame(id);
  } else {
    clearTimeout(id as unknown as ReturnType<typeof setTimeout>);
  }
};

/**
 * Lightweight profiler for measuring scan latency and camera FPS during
 * device testing. No native modules are required, so it works in Expo Go.
 *
 * For battery, CPU and temperature on real devices, integrate a native module
 * such as react-native-device-info or expo-device/expo-battery and pass the
 * values through `recordSample`.
 */
export class PerformanceProfiler {
  sessions: Map<string, ScanSession> = new Map();
  private frameId: number | null = null;

  startScan(scanId: string): ScanSession {
    const session: ScanSession = {
      scanId,
      startTime: getTime(),
      frameCount: 0,
      lastFrameTime: getTime(),
      samples: [],
    };
    this.sessions.set(scanId, session);
    this.startFrameCounter(session);
    return session;
  }

  private startFrameCounter(session: ScanSession) {
    const tick = () => {
      session.frameCount += 1;
      session.lastFrameTime = getTime();
      this.frameId = requestFrame(tick);
    };
    this.frameId = requestFrame(tick);
  }

  finishScan(scanId: string, note?: string): PerfSample {
    const session = this.sessions.get(scanId);
    if (!session) {
      throw new Error(`Scan ${scanId} not started`);
    }
    if (this.frameId !== null) {
      cancelFrame(this.frameId);
      this.frameId = null;
    }
    const now = getTime();
    const durationMs = now - session.startTime;
    const fps =
      durationMs > 0 ? Math.round((session.frameCount / durationMs) * 1000) : undefined;

    const sample: PerfSample = {
      timestamp: Date.now(),
      scanId,
      durationMs: Math.round(durationMs * 100) / 100,
      fps,
      deviceInfo: this.getDeviceInfo(),
      memoryMB: this.getMemoryMB(),
      note,
    };
    session.samples.push(sample);
    return sample;
  }

  getDeviceInfo() {
    return {
      platform: Platform.OS,
      osVersion: Platform.Version,
      // @ts-expect-error React Native does not always expose model on Android
      model: Platform.OS === "ios" ? "iPhone" : (Platform.constants?.Model as string | undefined),
    };
  }

  getMemoryMB(): number | undefined {
    // React Native has no standard memory API; use a placeholder for native
    // integration (e.g., react-native-device-info getTotalMemory / getUsedMemory).
    const perf = globalThis as unknown as { performance?: { memory?: { usedJSHeapSize?: number } } };
    if (perf.performance?.memory?.usedJSHeapSize) {
      return Math.round(perf.performance.memory.usedJSHeapSize / (1024 * 1024));
    }
    return undefined;
  }

  exportSession(scanId: string): PerfSample[] {
    return this.sessions.get(scanId)?.samples ?? [];
  }

  clear() {
    this.sessions.clear();
  }
}

export const defaultProfiler = new PerformanceProfiler();
