# Limitations and Future Sensor Roadmap

## What the smartphone camera can and cannot do

The Smart Consumable Scanner AI is designed to inspect consumable products using the smartphone camera as the primary sensor. This is a powerful and accessible starting point, but it has important physical limits.

### Capabilities

- **Surface appearance** — color, texture, visible mold, bruising, wrinkling, drying.
- **Packaging condition** — dents, swelling, tears, leaks, deformation.
- **Object recognition** — product category and packaging type using deep-learning classifiers.
- **Freshness indicators for exposed produce** — trained spoilage models on fruits and vegetables give real P(spoiled) scores.

### Limitations

| Product state | Camera can see | Camera cannot reliably see |
|---------------|----------------|---------------------------|
| Sealed bottle/can | Label, packaging shape, leaks/swelling, discoloration through transparent packaging | Internal microbial growth, gas composition, true expiry |
| Opaque package | External damage, swelling | Internal spoilage, off-odors, temperature history |
| Meat/fish behind plastic film | Color, exudate, package shape | Bacterial load, internal decay, smell |
| Frozen products | Packaging condition, ice crystals, freezer burn surface | Internal thaw/refreeze history |
| Dairy/cheese inside carton | Carton shape, leaks | Milk protein breakdown, bacterial toxins |

The application therefore:

1. Runs **real model inference** on the visible evidence.
2. **Documents uncertainty and limitations** in the `findings` list.
3. Uses **packaging and surface cues** only for sealed or opaque products.
4. Allows **inspector override** and manual expiry date entry for compliance workflows.

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
