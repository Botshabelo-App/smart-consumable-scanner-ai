# Smart Consumable Scanner AI — Production Architecture

This document describes the target production architecture for the Smart Consumable Scanner AI application. It is intended to support schools, supermarkets, warehouses, manufacturers, wholesalers, restaurants, and government food inspectors.

## Core principles

1. **Organisation-agnostic by default** — No single organisation (including the Department of Education) is hard-coded into the core system. Organisation identity, branding, and backend URL are loaded from configuration at runtime.
2. **Pilot baseline locked** — RC1 Pilot v10l remains the official pilot baseline. Production changes live on a separate branch and do not alter the pilot build.
3. **Real-world validation first** — Production features are driven by data gathered from the pilot. Code changes are limited to verified bugs, security, stability, and architecture until the pilot is complete.
4. **Cautious AI language** — The system never claims a product is safe or counterfeit when evidence is insufficient. Results use “possible”, “suspicious”, or “needs manual inspection” where appropriate.
5. **Barcode/QR is not proof of safety** — A valid barcode or QR code only identifies the product. The physical product, packaging, and printed information must still be inspected.

## Supported consumable categories

The production scanner must support any packaged consumable where a barcode or QR code is present, including but not limited to:

- Meat, chicken, fish/seafood
- Milk, cheese, yoghurt, butter
- Bread, pastries
- Fruit, vegetables
- Canned food, bottled water, soft drinks, juice
- Beer, wine, spirits
- Frozen products, dry goods, baby food, cooking oil
- Other packaged consumables

## High-level data flow

```
Mobile device
    |
    v
[Camera capture] --+---> [Barcode/QR detection] --+--> [Barcode lookup service]
                   |                                 |         |
                   +---> [OCR] ----------------------+         v
                   |          (brand, dates, batch)      [Local product DB]
                   |                                       [Open Food Facts / external]
                   |
                   +---> [Visual inspection]
                            (packaging damage, swelling, leaks, discolouration)
                            |
                            v
                   [Cross-check engine]
                            |
                            v
                   [Cautious AI result]
```

## Inspection inputs

- **Barcode/QR code** — EAN-13, EAN-8, UPC-A, Code-128, QR.
- **OCR** — Extract printed product name, brand, batch/lot number, manufacturing date, expiry date.
- **Visual analysis** — Detect packaging condition, swelling, leaks, tears, discolouration, mould, label tampering.
- **Optional manual input** — Inspector can override any auto-detected field.

## Cross-check rules

The cross-check engine flags a result as suspicious when any of the following occur:

- Barcode/QR product information conflicts with OCR-read text on the packaging.
- Manufacturing or expiry dates are missing, unreadable, or impossible (e.g., production date in the future).
- Expiry date is in the past or near the present date.
- Packaging shows damage, swelling, leaks, or tears.
- Label appears reprinted, peeled, or tampered with.
- Barcode is not recognised, but the product is clearly packaged — OCR and visual inspection continue.
- Image is too blurry or dark to make a reliable determination.

## AI result categories

The production result must clearly return one of the following, with confidence and reasons:

- Safe / Fresh
- Near expiry
- Expired
- Suspicious expiry / label
- Damaged packaging
- Missing / illegible label
- Possible barcode / product mismatch
- Possible counterfeit / tampering indicators
- Unknown / Needs manual inspection

## Organisation configuration

Organisation-specific values (logo, primary colour, app name hint, default backend URL) are stored in:

- `mobile/src/config/brand.ts` (fallback defaults)
- Runtime configuration fetched from the backend at `/config/organisation`
- Backend organisation record in the `organisations` table

No organisation name is hard-coded in the core source.

## Deployment strategy

- Pilot APK and backend URL remain on `devin/initial-scaffold`.
- Production work lives on `production/v1`.
- Once pilot validation is complete, `production/v1` is merged/released as the production build.
- See `PRODUCTION_DEPLOYMENT_CHECKLIST.md` for cloud hosting options and costs.
