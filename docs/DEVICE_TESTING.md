# Real Device Testing Guide

**Status:** Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode.

This document describes how to validate the Smart Consumable Scanner AI mobile app on real Android and iOS devices.

## Goals

- Measure scan latency (time from shutter tap to AI result).
- Estimate camera preview FPS during live scanning.
- Monitor battery, RAM, CPU and device temperature.
- Capture device model, OS version, and network conditions.
- Collect structured logs for comparison across low-end, mid-range and flagship devices.

## Built-in performance profiler

The mobile app includes a zero-dependency performance profiler in `mobile/src/utils/performanceProfiler.ts`.

Usage in a screen:

```ts
import { defaultProfiler } from "@/utils/performanceProfiler";

async function handleScan() {
  const scanId = `scan_${Date.now()}`;
  defaultProfiler.startScan(scanId);
  // ... capture image and call API ...
  const sample = defaultProfiler.finishScan(scanId, "wifi");
  console.log(JSON.stringify(sample));
  // upload to backend /metrics or save locally for export
}
```

The profiler records:

- `durationMs` — total scan-to-result time.
- `fps` — approximate camera preview frame rate.
- `deviceInfo.platform` / `osVersion` / `model`.
- `memoryMB` — JavaScript heap size when running in a web context (for native memory, see below).

## Device matrix

Test on at least the following device classes:

| Class | Examples | Why |
|-------|----------|-----|
| Low-end | Android Go, older Samsung A-series | Ensures app works for price-sensitive inspectors and schools. |
| Mid-range | Samsung A54, Google Pixel 6a, iPhone SE | Expected largest user base. |
| Flagship | Samsung S24, iPhone 15 Pro | Baseline for best-case latency and camera quality. |

## Metrics to record per device

| Metric | How to measure | Target (RC1) |
|--------|----------------|--------------------|
| Scan latency | `performanceProfiler` | ≤ 2 s on Wi-Fi, ≤ 4 s on 4G |
| Camera preview FPS | `frameCount / durationMs * 1000` | ≥ 15 FPS on mid-range |
| Battery drain | Use `expo-battery` or `react-native-device-info` | ≤ 10% per 30 min active scanning |
| RAM usage | `expo-device` / `react-native-device-info` | ≤ 400 MB peak |
| CPU usage | Android Studio Profiler / Xcode Instruments | < 60% sustained |
| Device temperature | Manual observation or `react-native-thermal-printer` vendor API | No thermal throttling during 15 min session |

## Manual test protocol

1. Install the production build (`eas build --platform android` or iOS equivalent).
2. Disable power saving and close background apps.
3. For each device:
   - Scan 10 fresh and 10 expired/suspicious items per product category.
   - Vary lighting (bright indoor, dim, natural window, fluorescent).
   - Use multiple angles and distances.
   - Record success/failure, latency, and AI confidence.
4. Export logs and upload to the backend `/metrics` endpoint or share via e-mail/cloud.

## Optional native integrations

For richer telemetry, add:

- `expo-device` — device manufacturer, model, OS version.
- `expo-battery` — battery level and state.
- `react-native-device-info` — total/used memory, CPU architecture.

These are **not** required for baseline testing but improve reporting.

## Upload and analysis

Collect JSON logs from test devices and run:

```bash
python scripts/analyze_device_logs.py --logs-dir device_logs/ --output reports/device_testing_report.json
```

This aggregates latency, FPS and success rate by device class and OS version.
