"""
Test script for OCR extraction with existing uploaded invoices.
Tests the InvoiceExtractor class with the uploaded PDF files.
"""

import asyncio
import sys
from pathlib import Path
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from ocr import InvoiceExtractor


async def test_invoice(pdf_path: Path) -> dict:
    """
    Test OCR extraction on a single PDF invoice.

    Returns:
        Dictionary with test results
    """
    print(f"\n{'='*70}")
    print(f"Testing: {pdf_path.name}")
    print(f"{'='*70}")

    try:
        extractor = InvoiceExtractor()
        result = await extractor.extract(pdf_path)

        # Print results
        print(f"\nExtracted Data:")
        print(f"  Vendor: {result['vendor']}")
        print(f"  Vendor Confidence: {result['vendor_confidence']:.2f}")
        print(f"  Date: {result['date']}")
        print(f"  Date Confidence: {result['date_confidence']:.2f}")
        print(f"  Total: ${result['total']:.2f}")
        print(f"  Total Confidence: {result['total_confidence']:.2f}")
        print(f"  Invoice Number: {result['invoice_number']}")
        print(f"  Invoice Number Confidence: {result['invoice_number_confidence']:.2f}")

        # Validate results
        validation = {
            'vendor_valid': result['vendor'] is not None and result['vendor'] != "Unknown Vendor",
            'total_valid': result['total'] is not None and result['total'] > 0,
            'date_valid': result['date'] is not None,
            'invoice_number_valid': result['invoice_number'] is not None,
            'vendor_confidence_adequate': result['vendor_confidence'] >= 0.5,
            'total_confidence_adequate': result['total_confidence'] >= 0.5,
        }

        print(f"\nValidation Results:")
        print(f"  Vendor Valid: {validation['vendor_valid']} (not 'Unknown Vendor')")
        print(f"  Total Valid: {validation['total_valid']} (> 0)")
        print(f"  Date Valid: {validation['date_valid']} (not None)")
        print(f"  Invoice Number Valid: {validation['invoice_number_valid']} (not None)")
        print(f"  Vendor Confidence Adequate: {validation['vendor_confidence_adequate']} (>= 0.5)")
        print(f"  Total Confidence Adequate: {validation['total_confidence_adequate']} (>= 0.5)")

        return {
            'file': pdf_path.name,
            'success': True,
            'result': result,
            'validation': validation
        }

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'file': pdf_path.name,
            'success': False,
            'error': str(e)
        }


async def main():
    """Run tests on all uploaded invoices."""
    uploads_dir = Path(__file__).parent / 'uploads'

    # Find all PDF files in uploads directory
    pdf_files = list(uploads_dir.glob('*.pdf'))

    if not pdf_files:
        print("No PDF files found in uploads directory!")
        return

    print(f"Found {len(pdf_files)} PDF file(s) to test")

    # Test each invoice
    results = []
    for pdf_file in pdf_files:
        result = await test_invoice(pdf_file)
        results.append(result)

    # Print summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")

    successful = sum(1 for r in results if r['success'])
    print(f"\nTotal Tests: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

    # Detailed summary of each test
    print(f"\n{'='*70}")
    print("DETAILED RESULTS")
    print(f"{'='*70}")

    for result in results:
        if result['success']:
            print(f"\n✅ {result['file']}")
            r = result['result']
            print(f"   Vendor: {r['vendor']} (conf: {r['vendor_confidence']:.2f})")
            print(f"   Total: ${r['total']:.2f} (conf: {r['total_confidence']:.2f})")
            print(f"   Date: {r['date']} (conf: {r['date_confidence']:.2f})")
            print(f"   Invoice #: {r['invoice_number']} (conf: {r['invoice_number_confidence']:.2f})")
        else:
            print(f"\n❌ {result['file']}")
            print(f"   Error: {result['error']}")

    # Overall assessment
    print(f"\n{'='*70}")
    print("OVERALL ASSESSMENT")
    print(f"{'='*70}")

    if successful == len(results):
        print("\n✅ All tests passed! OCR extraction is working correctly.")
    else:
        print(f"\n⚠️  {len(results) - successful} test(s) failed. Review errors above.")

    # Check if 422 error would occur
    print(f"\n{'='*70}")
    print("422 ERROR CHECK")
    print(f"{'='*70}")
    print("\nChecking if extracted data would pass Pydantic validation...")

    validation_issues = []
    for result in results:
        if result['success']:
            r = result['result']
            issues = []
            if r['vendor'] is None or r['vendor'] == "":
                issues.append("vendor is None or empty")
            if r['total'] is None or r['total'] <= 0:
                issues.append("total is None or <= 0")
            if issues:
                validation_issues.append(f"{result['file']}: {', '.join(issues)}")

    if validation_issues:
        print("\n⚠️  Potential 422 validation errors:")
        for issue in validation_issues:
            print(f"   - {issue}")
    else:
        print("\n✅ No 422 validation errors expected. All data has valid defaults.")


if __name__ == "__main__":
    asyncio.run(main())