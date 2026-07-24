# Smart Consumable Scanner AI

A production-ready, cross-platform mobile application for detecting expired, spoiled, damaged, counterfeit, or near-expiry consumable products using AI and a smartphone camera.

## Goals

- Camera-first inspection for food, beverages, packaged goods, produce, meat, dairy, and more.
- AI analysis based on product condition, not only printed expiry dates.
- Offline-capable SQLite mode and online PostgreSQL mode.
- Professional report generation with PDF/CSV/Excel export and digital signatures.
- Role-based access for inspectors, managers, administrators, and consumers.
- Scalable architecture for future sensors (Bluetooth, NIR, thermal, barcode, RFID, NFC, IoT).

## What's implemented

- **Real computer-vision pipeline** in `ai-service/`: YOLOv8 object detection, EfficientNet-B0 product classification, MobileNetV3-Small fresh/spoiled spoilage classifier, and OpenCV-based packaging/bruise analysis.
- **Explainable AI**: every scan returns `findings` with concrete reasons (model scores, color/texture stats, packaging contour analysis).
- **Dataset and training scaffold** in `ai-service/datasets/` to prepare public datasets and fine-tune EfficientNet/MobileNet classifiers.
- **Mobile scanner**: live camera preview, continuous capture, multiple scan angles, image quality validation, and detailed result display.
- **Inspector dashboard**: inspection counts, breakdown bar chart, confidence trend line chart, GPS map of inspections.
- **Security**: JWT auth, role-based endpoints, encrypted token storage with `expo-secure-store`, audit logs, and offline scan queue.
- **Production deployment**: Kubernetes manifests, Nginx reverse-proxy config, and EAS production build config.

## Repository Structure

```text
.
├── backend           FastAPI API server, auth, database, reports, audit logs
├── ai-service        Python AI inference service (PyTorch / torchvision / YOLO)
├── mobile            React Native (Expo) mobile application
├── docs              Architecture, API, deployment, limitations/roadmap
├── k8s               Kubernetes manifests
├── nginx             Nginx reverse-proxy configuration
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

## Training your own models

```bash
cd ai-service/datasets
python prepare_hf.py --dataset Project-AgML/fresh_rotten_fruit_classification --output ../data
python train.py --data-dir ../data/raw --output-dir ../checkpoints
```

## Production build

### Mobile

```bash
cd mobile
npx eas build --platform android --profile production
npx eas build --platform ios --profile production
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

Update `k8s/backend.yaml` and `k8s/postgres.yaml` with strong secrets before deploying.

## Limitations and sensor roadmap

See [docs/LIMITATIONS_AND_ROADMAP.md](docs/LIMITATIONS_AND_ROADMAP.md) for what the smartphone camera can realistically detect and how NIR, hyperspectral, thermal, Bluetooth, RFID, NFC, and IoT sensors can be integrated in future releases.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## API

See [docs/API.md](docs/API.md).

## License

Proprietary — all rights reserved.
