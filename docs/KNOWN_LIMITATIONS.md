# Known Limitations — Smart Consumable Scanner AI

**Status:** Engineering Complete — RC1 Maintenance Mode.

This document lists the known functional, technical, and AI limitations of the RC1 baseline. It must be shared with pilot partners, customers, and reviewers before any deployment.

## 1. Camera-only sensing

The RC1 application uses a standard smartphone RGB camera. It can observe:

- Surface colour, texture, visible mould, bruising, wrinkling, drying.
- Packaging condition: dents, swelling, tears, leaks, deformation.
- Product shape and label information.
- Barcodes and QR codes.

It **cannot** see inside sealed, opaque, or tinted packaging, cans, bottles, or cartons.

## 2. What the AI cannot determine

The RC1 AI models do **not** determine:

- Internal microbial growth or bacterial load.
- Chemical contamination, toxins, or allergens.
- Odour, smell, or taste.
- True expiry date when labels are missing or not encoded.
- Temperature history or cold-chain breaks.
- Whether a product has been thawed and refrozen.
- Whether packaging gas composition is abnormal.

Any claim that the smartphone camera can detect these internal conditions without validated specialised hardware is false and must not be made.

## 3. Product and condition coverage

- The training pipeline supports all listed food, drink, and other consumable categories, but RC1 model weights are trained on small public datasets.
- Performance on South African products, local manufacturers, and specific packaging types has not been validated.
- The "near_expiry" and "suspicious" classes may have lower accuracy until more labelled examples are collected.

## 4. AI accuracy and validation

- Current reported accuracy is based on limited images and should not be generalised.
- Confidence scores are calibrated but require validation on a representative held-out test set.
- The system will occasionally misclassify products; inspector override and reviewer adjudication are required.

## 5. Mobile and hardware

- AI inference runs on the server; the mobile app requires connectivity at the time of analysis.
- Offline mode queues scans but cannot produce AI results until synced.
- Expo SDK 57 / React Native 0.86 prefer Node.js `>=20.19.4`; the current CI environment may need upgrading before production builds.
- On-device inference is not implemented in RC1.
- Battery, temperature, and device-specific performance metrics require physical pilot testing.

## 6. Barcode and QR integration

- Open Food Facts coverage is limited in some regions and product categories.
- Production date and expiry date may not be encoded in the barcode.
- A discrepancy flag does **not** prove fraud; it means the printed data and AI condition disagree and a human should review.

## 7. Reports and compliance

- Reports are generated from AI outputs and inspector input. They are inspection aids, not legal certificates.
- Digital signatures are stored as data; legal enforceability depends on local electronic-signature laws.
- GPS accuracy depends on the device and environment.

## 8. Security and operations

- Default `SECRET_KEY` and `CORS_ORIGINS` must be replaced before production.
- `npm audit` reports only moderate transitive issues, but new vulnerabilities may be discovered.
- A full penetration test and third-party code review are recommended before `v1.0.0`.

## 9. Future capabilities

The following are not implemented in RC1 and are on the research backlog:

- Near-Infrared (NIR) camera support.
- Hyperspectral imaging.
- Thermal imaging.
- Bluetooth/USB pH, VOC, gas, and temperature sensors.
- RFID and NFC integration.
- ERP / WMS / POS integration.
- Federated learning and edge AI optimisation.

Each of these will require separate hardware validation, dataset collection, model retraining, and regulatory review before any claim is made.

## 10. How limitations are communicated

- Every AI result includes confidence, findings, and a statement of camera-only limitations where applicable.
- `docs/LIMITATIONS_AND_ROADMAP.md` describes the camera capabilities and future sensor integration points.
- Business documents (`docs/business/`) repeat these limitations for customers and pilot partners.
- The mobile UI and reports use text labels alongside colour coding for accessibility.

## 11. Mitigation

- Inspectors are trained to use the AI as an assistant, not a final decision-maker.
- Override and review workflows capture expert judgement.
- Discrepancy cases are escalated to human reviewers.
- Model registry gates ensure only validated models are promoted.
- Dataset strategy mandates representative, expert-labelled data before production claims.
