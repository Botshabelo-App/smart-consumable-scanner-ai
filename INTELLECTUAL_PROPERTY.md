# Intellectual Property

## Copyright

Copyright © 2026 Moeketsi Daniel and the Smart Consumable Scanner AI contributors. All rights reserved.

## Ownership

The Smart Consumable Scanner AI software, documentation, model cards, datasets (where owned by the project), trademarks, and associated materials are owned by Moeketsi Daniel unless otherwise stated.

## Trademark

The name "Smart Consumable Scanner AI" and any associated logos are trademarks of the project owner. Use of the name or logos without written permission is prohibited.

## Patents

No patents have been filed or granted for the current RC1 codebase. Any patentable inventions developed during or after the pilot program remain the property of the project owner unless assigned in writing.

## Third-party licenses and open-source attributions

The project uses the following open-source components under the licences listed below. The complete dependency trees are described in `backend/requirements.txt`, `backend/requirements-dev.txt`, `ai-service/requirements.txt`, `ai-service/requirements-dev.txt`, and `mobile/package-lock.json`.

### Backend and AI service

- **FastAPI** — MIT Licence
- **Uvicorn** — BSD 3-Clause Licence
- **SQLAlchemy** — MIT Licence
- **Pydantic** — MIT Licence
- **PyTorch / torchvision** — BSD 3-Clause Licence
- **Ultralytics (YOLOv8)** — AGPL-3.0 Licence
- **OpenCV (opencv-python-headless)** — Apache 2.0 Licence
- **NumPy** — BSD 3-Clause Licence
- **scikit-learn** — BSD 3-Clause Licence
- **Pillow** — HPND / PIL Software Licence
- **PyJWT** — MIT Licence
- **bcrypt** — Apache 2.0 Licence
- **ReportLab** — BSD 3-Clause Licence
- **OpenPyXL** — MIT Licence
- **pandas** — BSD 3-Clause Licence
- **qrcode** — BSD 3-Clause Licence
- **pytest** — MIT Licence

### Mobile application

- **React Native** — MIT Licence
- **Expo SDK** — MIT Licence
- **React Navigation** — MIT Licence
- **i18n-js** — MIT Licence
- **axios** — MIT Licence
- **react-native-maps** — MIT Licence
- **react-native-chart-kit** — MIT Licence
- **react-native-svg** — MIT Licence

### Datasets and pretrained weights

Public datasets and pretrained model weights used during RC1 development are subject to their own licences. Review the source documentation for:

- Project-AgML datasets on Hugging Face.
- Marcus Klasson GroceryStoreDataset.
- ImageNet-pretrained EfficientNet, MobileNetV3, ConvNeXt, and ViT weights downloaded via torchvision.
- COCO-pretrained YOLOv8 weights downloaded via Ultralytics.

Commercial use of pretrained weights or derivative models must comply with the upstream licences.

## Licence

This project is proprietary unless a separate written licence is granted. No part of the source code, documentation, or diagrams may be reproduced, distributed, or used to create derivative works without explicit permission, except as permitted by the third-party licences referenced above.

## Source file headers

Source files in this repository include a short header indicating copyright and proprietary status. See the top of each `.py`, `.ts`, `.tsx`, and `.md` file for the applicable notice.

## Questions

For licensing, partnership, or commercial-use enquiries, contact the project owner.
