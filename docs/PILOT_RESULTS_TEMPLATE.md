# Smart Consumable Scanner AI — Pilot Results Template

Use this template to record every real-device and real-product test. The data will be compiled into a PASS/FAIL evaluation, bug list, OCR/barcode/QR accuracy, AI accuracy, performance report, and production readiness recommendation.

## Inspector information

- Pilot start date:
- Pilot end date:
- Inspector name(s):
- Test account used:
- Backend URL tested:
- APK version tested:
- APK SHA-256 tested:

## Device matrix

For each device, run the full protocol once.

| # | Device model | Android version | Budget/Mid/Flagship | Camera quality | Login | Dashboard | Scan | History | Reports | Offline/reconnect | Notes |
|---|--------------|-----------------|---------------------|----------------|-------|-----------|------|---------|---------|-------------------|-------|
| 1 |              |                 |                     |                |       |           |      |         |         |                   |       |
| 2 |              |                 |                     |                |       |           |      |         |         |                   |       |
| 3 |              |                 |                     |                |       |           |      |         |         |                   |       |
| 4 |              |                 |                     |                |       |           |      |         |         |                   |       |
| 5 |              |                 |                     |                |       |           |      |         |         |                   |       |

## Product category coverage

Test at least one item from each category. Mark `Y` when done.

| Category | Examples tested | Count | Barcode/QR read | OCR read | AI condition | Notes |
|----------|-----------------|-------|-----------------|----------|--------------|-------|
| Meat | beef, mince, sausages | | | | | |
| Poultry | chicken pieces, whole chicken | | | | | |
| Fish/seafood | fresh fish, frozen fillets, canned tuna | | | | | |
| Dairy | milk, cheese, yoghurt, butter, cream | | | | | |
| Bakery | bread, rolls, muffins, croissants | | | | | |
| Fruit | apples, bananas, oranges, grapes | | | | | |
| Vegetables | tomatoes, lettuce, potatoes, onions, spinach | | | | | |
| Canned food | beans, tuna, tomatoes, soup | | | | | |
| Bottled water | still, sparkling | | | | | |
| Soft drinks | cola, juice, energy drinks | | | | | |
| Alcoholic drinks | beer, wine, whisky, brandy, spirits | | | | | |
| Packaged snacks | crisps, biscuits, nuts, chocolate | | | | | |
| Frozen | frozen vegetables, ice cream, frozen meals | | | | | |
| Baby/health | formula, supplements, medicines | | | | | |

## Per-scan data sheet

For each product scanned, copy this block. Attach the product photo and app screenshot to each entry if possible.

```
Scan #:
Date/Time:
Device model:
Android version:
Product name (ground truth):
Brand (ground truth):
Category:
Lighting: bright / dim / torch / other
Packaging: flat label / curved / reflective / transparent / damaged

Auto-detected fields (after capture, before editing):
- Product name (AI/OCR): ___
- Brand (AI/OCR): ___
- Barcode/QR code: ___
- Batch/Lot number: ___
- Manufacturing date: ___
- Expiry date: ___

AI result:
- Condition: ___
- Confidence: ___
- Packaging condition: ___
- Findings/reasons:

Spoken result played: Yes / No / unclear

Inspector ground truth:
- Is the product actually fresh/near expiry/expired/suspicious/damaged?
- Did the AI condition match the real condition? Yes / No / Partially
- If mismatched, explain:

Barcode/QR result:
- Code read automatically: Yes / No
- If yes, did the code identify the correct product? Yes / No / Unknown product
- If barcode was unknown, did the scan continue with OCR/visual? Yes / No

OCR result:
- Product name correct: Yes / No
- Brand correct: Yes / No
- Batch/Lot correct: Yes / No
- Manufacturing date correct: Yes / No
- Expiry date correct: Yes / No

Cross-check / mismatch:
- Did barcode info conflict with printed label? Yes / No
- Did expiry date conflict with visual appearance? Yes / No
- Was a suspicious/missing/damaged label detected? Yes / No

Performance:
- Time from capture to result: ___ seconds
- Did the camera freeze or crash? Yes / No
- Did the app show "Server unavailable"? Yes / No
- Was the scan accepted without editing? Yes / No

Errors or UI issues:
- Crash log / error message:
- Screenshot filename:
- Photo filename:
- Additional notes:
```

## Summary ratings

Rate each area after the full device/product matrix is complete.

| Area | Score 1–5 (5 = excellent) | Problems observed |
|------|---------------------------|-------------------|
| Login / backend connection | | |
| Camera capture speed | | |
| Barcode/QR scanning | | |
| OCR product name accuracy | | |
| OCR brand accuracy | | |
| OCR batch/lot accuracy | | |
| OCR manufacturing date accuracy | | |
| OCR expiry date accuracy | | |
| AI condition accuracy (fresh) | | |
| AI condition accuracy (expired) | | |
| AI condition accuracy (damaged packaging) | | |
| AI confidence usefulness | | |
| Spoken result clarity | | |
| Dashboard accuracy | | |
| History list | | |
| PDF/CSV/Excel reports | | |
| Offline scanning and sync | | |
| App stability / crashes | | |
| Battery / performance | | |
| Security / no data leaks | | |

## Known issues list

List every bug, failure, or unexpected behaviour here.

| # | Severity | Description | Device / product | Reproducible | Evidence |
|---|----------|-------------|------------------|--------------|----------|
| 1 | Critical/High/Medium/Low | | | | |
| 2 | | | | | |

## Required fixes before production

1.
2.
3.

## Additional feedback

- Features that worked well:
- Features that need improvement:
- Products or labels that were especially hard to scan:
- Any security or privacy concerns:
- Recommended RC2 requirements:
