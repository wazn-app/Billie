# Test Invoices

This directory contains sample PDF invoices for testing the Billie Invoice Processing System.

## Adding Test Invoices

Place your test PDF invoices in this directory. The system will use them for:

- OCR extraction testing
- Manual testing of the upload workflow
- Validation of confidence scoring
- Edge case handling (missing fields, complex layouts)

## Recommended Test Cases

1. **Simple Invoice** - Standard layout with clear fields
2. **Complex Invoice** - Multiple items, taxes, discounts
3. **Low Quality** - Scanned or low-resolution PDF
4. **Missing Fields** - Invoice without vendor name or invoice number
5. **Edge Cases** - Handwritten notes, unusual formats

## Usage

Test invoices can be uploaded via the web interface at `/upload` or used in automated tests.