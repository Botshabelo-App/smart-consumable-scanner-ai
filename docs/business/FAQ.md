# Frequently Asked Questions — Smart Consumable Scanner AI

**Status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode.

## General

### What is Smart Consumable Scanner AI?

A cross-platform mobile inspection system that uses a smartphone camera and AI to detect expired, spoiled, damaged, counterfeit, or near-expiry consumable products.

### Is it production-ready?

Not yet. It is in Release Candidate 1 (RC1) and is ready for controlled pilot deployments. Version 1.0.0 will only be released after successful pilot validation and release checklist sign-off.

### Who can use it?

Government inspectors, municipal health inspectors, school food inspectors, retailers, warehouse managers, manufacturers, restaurants, hotels, and consumers.

## AI and accuracy

### Does the AI use real computer vision?

Yes. The pipeline uses YOLOv8 for detection, EfficientNet-B0 for product classification, MobileNetV3-Small for spoilage analysis, and OpenCV for packaging analysis. Results are not simulated or hardcoded.

### How accurate is it?

Accuracy depends on the product category, lighting, camera quality, and the size of the labelled training dataset. The current RC1 models are trained on small public datasets. Production claims require validation on a larger, representative, expert-labelled dataset collected during pilots.

### Can it see inside sealed packaging or cans?

No. The smartphone camera can only observe external, visible characteristics. The system clearly states this limitation and flags cases where internal condition cannot be determined.

### Can it detect odour or chemical contamination?

No. Smell and chemical contamination require specialised sensors. The architecture supports future NIR, hyperspectral, thermal, and gas sensor integration, but these are not yet implemented.

## Barcode and expiry

### Does it read expiry dates?

It reads barcodes and QR codes and can retrieve printed expiry data from public databases when available. It also detects visible spoilage independently. If the two disagree, it flags a discrepancy for human review.

### Can it detect fake or relabelled products?

It can flag visible anomalies such as mismatched labels, damaged packaging, or condition that does not match the printed expiry. A definitive counterfeit determination requires human investigation and possibly forensic testing.

## Mobile and offline

### Does it work offline?

Yes. Scans can be queued locally and synced when connectivity returns. AI inference currently runs on the backend, so an online connection is needed at the time of analysis.

### Which devices are supported?

Android 8+ and iOS 14+. Mid-range and flagship devices with autofocus cameras give the best experience.

### How is my data protected?

Tokens are stored in `expo-secure-store`. Data is transmitted over HTTPS. Backend access is controlled by JWT and role-based permissions. PII is minimised.

## Pilot and deployment

### How do I join the pilot?

Contact the project owner. The pilot proposal in `docs/business/PILOT_PROPOSAL.md` outlines the scope, responsibilities, and success criteria.

### Can I install it in my own data centre?

Yes. The backend and AI service are containerised and can be deployed with Docker Compose or Kubernetes. See `docs/business/IMPLEMENTATION_GUIDE.md`.

### How often are models updated?

Models are only updated after offline retraining and validation. The model registry blocks promotion unless the new model matches or exceeds the active model's validation score.

## Support

### Where can I find more documentation?

- `docs/README.md` or `README.md` for an overview.
- `docs/OPERATIONS_GUIDE.md` for operations.
- `docs/business/IMPLEMENTATION_GUIDE.md` for deployment.
- `docs/business/TRAINING_GUIDE.md` for user training.
- `docs/diagrams/` for architecture diagrams.
