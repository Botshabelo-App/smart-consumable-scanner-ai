# Limitations and Future Sensor Roadmap

**Status:** Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode. The capabilities and limitations described here reflect the current smartphone-camera-only release. Future sensor support is on the roadmap and will require separate validation before claims are made.

## What the smartphone camera can and cannot do

The Smart Consumable Scanner AI is designed to inspect consumable products using the smartphone camera as the primary sensor. This is a powerful and accessible starting point, but it has important physical limits.

### Capabilities

- **Surface appearance** — color, texture, visible mold, bruising, wrinkling, drying.
- **Packaging condition** — dents, swelling, tears, leaks, deformation.
- **Object recognition** — product category and packaging type using deep-learning classifiers.
- **Freshness indicators for exposed produce** — trained spoilage models on fruits and vegetables give real P(spoiled) scores.
- **Barcode and QR scanning** — retrieve product name, manufacturer, and printed dates from public databases when encoded.

### Limitations

| Product state | Camera can see | Camera cannot reliably see |
|---------------|----------------|---------------------------|
| Sealed bottle/can | Label, packaging shape, leaks/swelling, discoloration through transparent packaging | Internal microbial growth, gas composition, true expiry |
| Opaque package | External damage, swelling | Internal spoilage, off-odors, temperature history |
| Meat/fish behind plastic film | Color, exudate, package shape | Bacterial load, internal decay, smell |
| Frozen products | Packaging condition, ice crystals, freezer burn surface | Internal thaw/refreeze history |
| Dairy/cheese inside carton | Carton shape, leaks | Milk protein breakdown, bacterial toxins |
| Barcode/QR only | Metadata from database | The physical condition of the product itself |

The application therefore:

1. Runs **real model inference** on the visible evidence.
2. Uses **barcode/QR data** to retrieve product metadata and printed dates, but treats those as separate signals.
3. **Flags discrepancies** when the AI-detected condition conflicts with printed expiry data, and routes the case for human review rather than automatically concluding fraud.
4. **Documents uncertainty and limitations** in the `findings` list.
5. Uses **packaging and surface cues** only for sealed or opaque products.
6. Allows **inspector override** and manual expiry date entry for compliance workflows.

## Future sensor integration points

The architecture is modular so extra sensors can be added without changing the core inference contract.

### 1. Near-Infrared (NIR) cameras

- Plug-in to `ai-service` as an extra image channel.
- NIR can detect water content and internal bruising in fruits.
- New model: `NIRClassifier` following the same `predict(image, product_hint)` interface.

### 2. Hyperspectral cameras

- Captures per-pixel spectral signatures.
- Useful for detecting early spoilage, contamination, and counterfeit packaging inks.
- Extend `image_processor.py` to stack hyperspectral bands and pass them to a 3-D CNN.

### 3. Thermal cameras

- Detects temperature anomalies, thawed/refrozen products, and packaging leaks.
- Add `ThermalAnalyzer` service that returns temperature maps and hotspot flags.

### 4. Bluetooth/USB probes

- pH, conductivity, volatile organic compound (VOC), and gas sensors.
- Connected via mobile Bluetooth/USB; readings appended to `ScanCreate` payload.
- Backend stores sensor readings in a new `sensor_readings` table.

### 5. Barcode, QR code, RFID, NFC

- Scanned identifiers are resolved against product databases or blockchain traceability records.
- Adds `barcode`, `qr_code`, `rfid_tag`, `nfc_id` fields to the `Scan` model.
- Cross-checks label expiry against AI-detected condition.

### 6. IoT warehouse monitoring

- Temperature/humidity loggers push telemetry to a new `/iot/ingest` endpoint.
- Dashboard correlates warehouse environmental history with inspection results.

### Mobile on-device inference

- The `ai-service/scripts/export_mobile_models.py` script exports PyTorch checkpoints to ONNX and TensorFlow Lite.
- Future mobile releases can run the spoilage classifier locally (TensorFlow Lite / ONNX Runtime) for offline, low-latency inference, then sync results when online.
- The first production release uses server inference to support rapid model updates and centralized model governance.

## Model retraining policy

The application **does not retrain production models automatically** from reviewer feedback. Approved review examples are exported to a controlled `datasets/feedback/` directory. Retraining and validation happen offline; the updated model is deployed only after review.
