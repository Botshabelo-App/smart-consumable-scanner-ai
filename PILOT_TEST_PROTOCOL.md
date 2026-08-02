# Smart Consumable Scanner AI — Real-Device Pilot Test Protocol

## Purpose

This protocol describes how to validate the RC1 Pilot Build on real Android devices and real consumable products before declaring the build ready for wider pilot use.

## Scope

Test the following on at least **three different Android phones**:

- Camera capture and focus
- Barcode/QR code scanning
- OCR extraction of printed text
- AI condition assessment
- Spoken and visual inspection results
- Multi-language voice guidance (English, isiZulu, isiXhosa, Afrikaans, Sesotho)
- Dashboard, history, and report generation
- Offline behaviour and automatic background sync
- Enterprise branding and splash/logo appearance

## Test Environment

- **APK:** `SmartConsumableScannerAI-RC1-Pilot-v10.apk`
- **Backend URL:** the public pilot URL supplied with the build
- **Test account:** Moeketsi Daniel / `moeketsitsomodan@gmail.com` / `477SectionA`
- **Lighting:** good, even indoor light; also test low-light with the phone torch

## Device Requirements

Test on a mix of:

- Budget Android (Android 10+)
- Mid-range Android (Android 12+)
- Flagship Android (Android 14+)
- At least one device with a macro/close-focus camera

## Product Categories

Test at least three items from each category:

| Category | Examples |
|----------|----------|
| Meat | fresh beef, chicken pieces, sausages, mince |
| Poultry | whole chicken, chicken fillets, marinated wings |
| Fish | fresh whole fish, frozen fillets, smoked fish |
| Dairy | milk, cheese, yoghurt, butter, cream |
| Bakery | sliced bread, rolls, muffins, croissants |
| Fresh produce | apples, bananas, tomatoes, lettuce, potatoes, onions |
| Canned food | canned beans, tuna, tomatoes, soup, vegetables |
| Bottled drinks | bottled water, soft drinks, beer, wine, whisky, juice |
| Packaged snacks | crisps, biscuits, nuts, chocolate |
| Frozen | frozen vegetables, ice cream, frozen meals |
| Baby/health | formula, supplements, medicines |

## Test Procedure

### 1. Installation and Login

1. Install the APK.
2. Enter the pilot backend URL.
3. Log in with the test account.
4. Verify the dashboard loads.

### 2. Single Product Scan

For each product:

1. Tap **Scan**.
2. Hold the phone 15–25 cm from the label.
3. Ensure the label is in focus and well-lit.
4. Tap **Capture**.
5. Wait for the AI result.
6. Verify the app auto-fills:
   - Product name
   - Brand
   - Barcode (if visible)
   - Batch/Lot number
   - Manufacturing date (if visible)
   - Expiry date (if visible)
7. Check the spoken result and the visual result card.
8. Tap **Accept AI** if correct or **Override AI** and note why.

### 3. Specific Checks

| Check | Pass Criteria |
|-------|---------------|
| Product name extraction | Correct name filled automatically for ≥70% of products |
| Brand extraction | Brand filled automatically for ≥60% of products |
| Barcode scanning | 1D/2D codes read automatically for ≥80% of products |
| Batch/Lot extraction | Batch or lot number read for ≥50% of labelled products |
| Expiry date extraction | Correct expiry date read for ≥80% of labelled products |
| Manufacturing date extraction | Correct date read when present for ≥60% of products |
| AI condition | Spoken and visual result match the product condition |
| Tampering flags | Suspicious results shown for future expiry dates on expired-looking products |
| Damaged packaging | Condition marked suspicious when visible damage is present |
| Curved/reflective labels | OCR still extracts key fields for ≥50% of curved/glossy labels |
| Low-light scanning | With torch, key fields extracted for ≥50% of low-light captures |
| Focus stability | No crashes or frozen camera across all test devices |

### 4. Dashboard, History, and Reports

1. After 5–10 scans, open the **Dashboard**.
2. Confirm totals and category breakdowns are correct.
3. Open **History** and verify all scans are listed.
4. Open **Reports**, select a scan, and generate **PDF**, **CSV**, and **Excel** reports.
5. Verify the reports contain product name, condition, confidence, and findings.

### 5. Edge Cases

Test and record results for:

- Damaged or torn labels
- Labels printed over curved surfaces (bottles, cans)
- Labels with reflective or transparent packaging
- Very small fonts
- Hand-written or stamped dates
- Missing expiry date
- Barcode that does not match the product name (potential counterfeit)
- Product with future expiry date but visibly spoiled
- Product with past expiry date but visually normal

## Data to Collect

For each scan, record:

- Device model and Android version
- Product category and name
- Lighting conditions
- Whether each field was auto-detected correctly
- AI condition and confidence
- Inspector’s actual assessment (ground truth)
- Any errors, crashes, or UI issues

## Success Criteria

The build is considered **pilot-ready** when:

- Login and navigation work on all test devices.
- Camera capture succeeds in ≥95% of attempts.
- Auto-filled fields are correct in ≥70% of clear, well-lit captures.
- AI condition matches expert inspection in ≥80% of cases.
- No crashes during a full 30-minute test session per device.
- Reports generate successfully for all supported formats.

## Failure Escalation

If a test fails:

1. Note the device, product, and lighting.
2. Capture the product photo separately.
3. Share the photo and the app screenshot.
4. File an issue with the observed vs expected result.

## Important Safety Note

The AI evaluates **observable external characteristics** captured by a standard smartphone camera. It cannot determine the internal condition of sealed, opaque, or frozen products. Use the result as a screening aid, not a definitive food-safety verdict.
