# Smart Consumable Scanner AI

A production-ready, cross-platform mobile application for detecting expired, spoiled, damaged, counterfeit, or near-expiry consumable products using AI and a smartphone camera.

## Goals

- Camera-first inspection for food, beverages, packaged goods, produce, meat, dairy, and more.
- AI analysis based on product condition, not only printed expiry dates.
- Offline-capable SQLite mode and online PostgreSQL mode.
- Professional report generation with PDF/CSV/Excel export and digital signatures.
- Role-based access for inspectors, managers, administrators, and consumers.
- Scalable architecture for future sensors (Bluetooth, NIR, thermal, barcode, RFID, NFC, IoT).

## Repository Structure

```text
.
├── backend           FastAPI API server, auth, database, reports
├── ai-service        Python AI inference service (TensorFlow/PyTorch)
├── mobile            React Native (Expo) mobile application
├── shared            Shared schemas/types used by backend and mobile
├── docs              Architecture, API, and deployment guides
└── docker-compose.yml
```

## Quick Start

### 1. Start backend + AI service + database

```bash
docker-compose up --build
```

- API: http://localhost:8000
- AI service: http://localhost:8001
- API docs: http://localhost:8000/docs

### 2. Run the mobile app

```bash
cd mobile
npm install
npx expo start
```

Use the Expo Go app on Android/iOS, or run `i` / `a` in the terminal.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## API

See [docs/API.md](docs/API.md).

## License

Proprietary — all rights reserved.
