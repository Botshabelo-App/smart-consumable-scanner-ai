# Technical White Paper — Smart Consumable Scanner AI

**Status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode.

## Abstract

Smart Consumable Scanner AI is a real-time, camera-first inspection platform for consumable products. It uses computer vision and deep learning to detect visible spoilage and packaging damage, integrates barcode and QR metadata for discrepancy flagging, and produces auditable reports for enterprise and regulatory use.

This white paper describes the system architecture, AI pipeline, data governance, security model, and roadmap.

## 1. System architecture

The platform consists of three deployable units:

1. **Mobile app:** React Native + Expo, with `expo-camera`, barcode/QR scanning, GPS capture, offline queue, and secure token storage.
2. **Backend:** FastAPI with SQLAlchemy, JWT/RBAC, rate limiting, audit logging, reporting, monitoring, and model registry.
3. **AI service:** Python service using YOLOv8 for object detection, EfficientNet-B0 for product classification, MobileNetV3-Small for condition/spoilage analysis, and OpenCV for packaging analysis.

See `docs/diagrams/` for system, backend, mobile, deployment, security, and database diagrams.

## 2. AI inference pipeline

The pipeline follows a product-first approach:

1. **Image quality validation:** blur, resolution, and corruption checks.
2. **Object detection:** YOLOv8 locates the product and primary packaging.
3. **Product classification:** EfficientNet-B0 maps the detected object to a supported category.
4. **Condition analysis:** MobileNetV3-Small and OpenCV analyse colour, texture, visible mould, bruising, swelling, leaks, and deformation.
5. **Calibration and explanation:** class scores are calibrated; Grad-CAM and top-k findings explain the prediction.
6. **Result assembly:** product name, category, condition, confidence, findings, and limitations are returned.

All inference is real. No hardcoded or simulated results are used.

## 3. Barcode and QR integration

The mobile camera can read barcodes and QR codes. The backend queries public databases (e.g., Open Food Facts) to retrieve product name, manufacturer, batch, production date, and printed expiry date. If the AI-detected condition conflicts with the printed expiry, the system flags the case for human review rather than declaring fraud automatically.

## 4. Human-in-the-loop and continuous improvement

Inspectors can accept or override any AI prediction with a reason and additional photos. Authorised reviewers inspect flagged cases, assign corrected labels, and approve them for the training dataset. New models are trained and validated offline before promotion. The model registry blocks promotion unless the new model's validation score meets or exceeds the active model.

## 5. Data governance and privacy

- Dataset versions are tracked.
- Labels require expert review before inclusion.
- PII is minimised and stored with access controls.
- GPS coordinates are captured at inspector discretion.
- Compliance with POPIA and GDPR is supported through consent, anonymisation, and audit logging.

## 6. Security model

- Passwords hashed with bcrypt and validated for complexity.
- JWT access tokens and refresh tokens stored in `expo-secure-store` on mobile.
- Role-based access control (RBAC) for inspectors, admins, company admins, and reviewers.
- Rate limiting on auth, scan, and report endpoints.
- TLS termination, CORS allow-lists, and container security scanning.
- Dependency vulnerabilities monitored with `npm audit` and `pip-audit`.

## 7. Deployment and scalability

- Docker Compose for development.
- Kubernetes manifests with horizontal pod autoscaling for production.
- Nginx reverse proxy for TLS and load balancing.
- PostgreSQL for relational data and S3-compatible storage for images/reports.
- EAS for mobile builds.

## 8. Current limitations

The smartphone camera can only observe external, visible characteristics. It cannot detect internal spoilage, odour, or chemical contamination in sealed or opaque products. The architecture supports future integration of NIR, hyperspectral, thermal, and gas sensors, but such claims require separate validation and model cards.

## 9. Roadmap to v1.0.0

1. Controlled RC1 pilot deployments.
2. Collection of expert-labelled, representative datasets.
3. Offline model retraining and validation.
4. Completion of `docs/RELEASE_CHECKLIST.md`.
5. Production release `v1.0.0`.

Post-1.0.0 research includes sensor fusion, federated learning, and ERP/inventory integrations.
