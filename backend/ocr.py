"""
Billie MVP - Invoice Processing System
Tesseract OCR Extraction Wrapper

InvoiceExtractor class with confidence scoring for field extraction
Uses pytesseract and pdf2image for PDF processing
"""

import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import re
from datetime import datetime
import logging
import numpy as np
import cv2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvoiceExtractor:
    """
    Invoice extraction using Tesseract OCR with confidence scoring.

    Extracts key fields from PDF invoices:
    - Vendor name
    - Invoice date
    - Total amount
    - Invoice number

    Each field includes a confidence score (0.0 - 1.0).
    Fields with confidence < 0.8 should be flagged for manual review.
    """

    def __init__(self, lang: str = 'eng'):
        """
        Initialize Tesseract OCR engine.

        Args:
            lang: Language for OCR (default: 'eng' for English)
        """
        logger.info(f"Initializing Tesseract OCR (lang={lang})")
        self.lang = lang
        # Verify tesseract is available
        try:
            pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            logger.error(f"Tesseract not found: {e}")
            raise RuntimeError("Tesseract OCR is not installed or not in PATH")

    def _preprocess_image(self, image) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy.

        Args:
            image: PIL Image object

        Returns:
            Preprocessed numpy array image
        """
        logger.debug("Applying image preprocessing")
        
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Apply adaptive thresholding for better text contrast
        # This handles varying lighting conditions better than simple thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Remove noise using median filtering
        denoised = cv2.medianBlur(thresh, 3)
        
        # Optional: Deskew image
        # Get coordinates of all non-zero pixels
        coords = np.column_stack(np.where(denoised > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            # Adjust angle
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Only rotate if angle is significant (> 0.5 degrees)
            if abs(angle) > 0.5:
                (h, w) = denoised.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                denoised = cv2.warpAffine(denoised, M, (w, h), 
                                         flags=cv2.INTER_CUBIC, 
                                         borderMode=cv2.BORDER_REPLICATE)
                logger.debug(f"Deskewed image by {angle:.2f} degrees")
        
        logger.debug("Image preprocessing complete")
        return denoised

    async def extract(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract invoice data from PDF file.

        Args:
            pdf_path: Path to the PDF invoice file

        Returns:
            Dictionary with extracted fields and confidence scores:
            {
                'vendor': str or None,
                'vendor_confidence': float,
                'date': str or None,
                'date_confidence': float,
                'total': float or None,
                'total_confidence': float,
                'invoice_number': str or None,
                'invoice_number_confidence': float
            }

        Raises:
            Exception: If PDF cannot be processed
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Extracting data from: {pdf_path}")

        # Convert PDF to images
        try:
            images = convert_from_path(pdf_path, dpi=300)
            logger.info(f"Converted PDF to {len(images)} image(s)")
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            raise Exception("Unable to process PDF file")

        if not images:
            logger.warning("No images extracted from PDF")
            return self._empty_result()

        # Extract text from all pages
        all_text_lines = []
        for page_num, image in enumerate(images):
            try:
                # Preprocess image for better OCR
                preprocessed = self._preprocess_image(image)
                
                # Get text with line-level data
                data = pytesseract.image_to_data(
                    preprocessed,
                    lang=self.lang,
                    output_type=pytesseract.Output.DICT
                )
                
                # Extract lines with their positions
                for i in range(len(data['text'])):
                    text = data['text'][i].strip()
                    if text:  # Skip empty lines
                        # Calculate a basic confidence based on text quality
                        # Tesseract provides confidence at character level
                        conf = data['conf'][i] / 100.0 if 'conf' in data else 0.8
                        conf = max(0.0, min(1.0, conf))
                        
                        all_text_lines.append({
                            'text': text,
                            'confidence': conf,
                            'page': page_num,
                            'top': data['top'][i] if 'top' in data else 0
                        })
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num}: {e}")
                continue

        if not all_text_lines:
            logger.warning("No text detected in PDF")
            return self._empty_result()

        # Join all text for pattern matching
        full_text = ' '.join([line['text'] for line in all_text_lines])

        # Extract fields with confidence scoring
        vendor, vendor_conf = self._extract_vendor(all_text_lines, full_text)
        date_str, date_conf = self._extract_date(all_text_lines, full_text)
        total, total_conf = self._extract_total(all_text_lines, full_text)
        invoice_num, invoice_num_conf = self._extract_invoice_number(all_text_lines, full_text)

        logger.info(f"Extraction complete - Vendor: {vendor}, Total: {total}, Confidence scores: V={vendor_conf:.2f}, D={date_conf:.2f}, T={total_conf:.2f}, I={invoice_num_conf:.2f}")

        return {
            'vendor': vendor,
            'vendor_confidence': vendor_conf,
            'date': date_str,
            'date_confidence': date_conf,
            'total': total,
            'total_confidence': total_conf,
            'invoice_number': invoice_num,
            'invoice_number_confidence': invoice_num_conf
        }

    def _empty_result(self) -> Dict[str, Any]:
        """
        Return empty result with sensible defaults instead of None.
        Required fields get default values to prevent 422 validation errors.
        """
        logger.info("Returning empty result with defaults")
        return {
            'vendor': "Unknown Vendor",  # Default vendor instead of None
            'vendor_confidence': 0.0,
            'date': None,  # Date can be None (truly optional)
            'date_confidence': 0.0,
            'total': 0.01,  # Minimum valid amount instead of None
            'total_confidence': 0.0,
            'invoice_number': None,  # Invoice number can be None
            'invoice_number_confidence': 0.0
        }

    def _extract_vendor(self, text_lines: list, full_text: str) -> tuple:
        """
        Extract vendor name from invoice.

        Strategy: Look for company names at the top of the document,
        typically in the first few lines, often with "From:", "Vendor:",
        or just the first prominent text.
        """
        logger.debug("Extracting vendor name")
        
        # Expanded vendor patterns - with and without company suffixes
        vendor_patterns = [
            # Patterns with company suffixes
            (r'(?:from|vendor|supplier|bill\s+from|invoice\s+from|payable\s+to|remit\s+to|sold\s+by)[:\s]+([A-Z][A-Za-z\s&]+(?:Inc|LLC|Corp|Co|Ltd|GmbH|S\.A\.|Pty|Ltd\.|Corp\.|Inc\.))', 0.3),
            (r'^([A-Z][A-Za-z\s&]+(?:Inc|LLC|Corp|Co|Ltd|GmbH|S\.A\.|Pty|Ltd\.|Corp\.|Inc\.))\s*$', 0.2),
            # Patterns without company suffixes (capitalized company names)
            (r'(?:from|vendor|supplier|bill\s+from|invoice\s+from|payable\s+to|remit\s+to|sold\s+by)[:\s]+([A-Z][a-zA-Z\s&]{2,}(?:\s+[A-Z][a-z]+)*)', 0.25),
            (r'^([A-Z][A-Za-z\s&]{5,50})\s*$', 0.15),  # Capitalized line, 5-50 chars
        ]

        candidates = []

        # Check first 20 lines for vendor (increased from 10)
        for i, line in enumerate(text_lines[:20]):
            text = line['text'].strip()
            confidence = line['confidence']

            # Skip very short lines or common non-vendor text
            if len(text) < 3 or text.lower() in ['invoice', 'bill', 'date', 'total', 'amount', 'page']:
                continue

            # Check against patterns
            for pattern, base_conf in vendor_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    vendor_name = match.group(1).strip()
                    # Clean up common suffixes and extra spaces
                    vendor_name = re.sub(r'\s+', ' ', vendor_name)
                    vendor_name = vendor_name.strip()
                    
                    # Calculate confidence based on pattern specificity and position
                    position_factor = max(0, (20 - i) / 20)  # Higher for earlier lines
                    calculated_conf = min(confidence + base_conf + (position_factor * 0.1), 1.0)
                    
                    candidates.append({
                        'value': vendor_name,
                        'confidence': calculated_conf,
                        'pattern': pattern,
                        'line_index': i
                    })
                    logger.debug(f"Vendor candidate found: '{vendor_name}' (conf={calculated_conf:.2f}, pattern={pattern})")

        # Fallback: look for capitalized company names anywhere in first 15 lines
        if not candidates:
            logger.debug("No vendor patterns matched, trying fallback")
            for i, line in enumerate(text_lines[:15]):
                text = line['text'].strip()
                # Look for lines that start with capital letter and contain mostly letters/spaces
                if len(text) >= 5 and len(text) <= 60:
                    if re.match(r'^[A-Z][A-Za-z\s&]+$', text):
                        # Avoid common words
                        if not any(word in text.lower() for word in ['invoice', 'bill', 'date', 'total', 'amount', 'page', 'address', 'phone', 'email']):
                            position_factor = max(0, (15 - i) / 15)
                            calculated_conf = line['confidence'] * 0.5 + (position_factor * 0.2)
                            candidates.append({
                                'value': text,
                                'confidence': calculated_conf,
                                'pattern': 'fallback_capitalized',
                                'line_index': i
                            })
                            logger.debug(f"Fallback vendor candidate: '{text}' (conf={calculated_conf:.2f})")

        # Return best candidate
        if candidates:
            best = max(candidates, key=lambda x: x['confidence'])
            logger.info(f"Vendor extracted: '{best['value']}' (confidence={best['confidence']:.2f})")
            return best['value'], best['confidence']

        logger.warning("No vendor found, using default")
        return "Unknown Vendor", 0.0

    def _extract_date(self, text_lines: list, full_text: str) -> tuple:
        """
        Extract invoice date.

        Strategy: Look for date patterns, especially near "Date:", "Invoice Date:",
        or common date formats in the document.
        """
        logger.debug("Extracting invoice date")
        
        # Expanded date patterns including month names
        date_patterns = [
            # Patterns with labels
            (r'(?:invoice\s+date|date|due\s+date)[:\s]*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})', 0.3),
            (r'(?:invoice\s+date|date|due\s+date)[:\s]*(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})', 0.3),
            # Month name patterns
            (r'(?:invoice\s+date|date|due\s+date)[:\s]*([A-Za-z]{3,9}\s+\d{1,2}[,\s]+\d{4})', 0.35),
            (r'(?:invoice\s+date|date|due\s+date)[:\s]*(\d{1,2}\s+[A-Za-z]{3,9}[,\s]+\d{4})', 0.35),
            # Standalone date patterns
            (r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})', 0.1),
            (r'(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})', 0.1),
            (r'([A-Za-z]{3,9}\s+\d{1,2}[,\s]+\d{4})', 0.15),
            (r'(\d{1,2}\s+[A-Za-z]{3,9}[,\s]+\d{4})', 0.15),
        ]

        candidates = []

        for i, line in enumerate(text_lines):
            text = line['text']
            confidence = line['confidence']

            for pattern, base_conf in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    # Normalize date format
                    try:
                        # Try various date formats
                        date_formats = [
                            '%m-%d-%Y', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d',
                            '%m.%d.%Y', '%d.%m.%Y', '%Y.%m.%d',
                            '%B %d, %Y', '%b %d, %Y', '%B %d %Y', '%b %d %Y',
                            '%d %B %Y', '%d %b %Y', '%d %B, %Y', '%d %b, %Y',
                            '%m-%d-%y', '%d-%m-%y', '%m/%d/%y', '%d/%m/%y'
                        ]
                        
                        for fmt in date_formats:
                            try:
                                parsed = datetime.strptime(date_str, fmt)
                                normalized = parsed.strftime('%Y-%m-%d')
                                
                                # Higher confidence for explicit date labels
                                label_boost = 0.2 if 'date' in text.lower() else 0.0
                                # Higher confidence for patterns with labels
                                pattern_boost = base_conf
                                
                                calculated_conf = min(confidence + label_boost + pattern_boost, 1.0)
                                
                                candidates.append({
                                    'value': normalized,
                                    'confidence': calculated_conf,
                                    'pattern': pattern,
                                    'line_index': i,
                                    'has_label': 'date' in text.lower()
                                })
                                logger.debug(f"Date candidate found: '{normalized}' (conf={calculated_conf:.2f})")
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logger.debug(f"Failed to parse date '{date_str}': {e}")
                        pass

        # Return best candidate, prioritizing those with date labels
        if candidates:
            # Sort by confidence, then by has_label
            candidates.sort(key=lambda x: (x['confidence'], x['has_label']), reverse=True)
            best = candidates[0]
            logger.info(f"Date extracted: '{best['value']}' (confidence={best['confidence']:.2f})")
            return best['value'], best['confidence']

        logger.info("No date found")
        return None, 0.0

    def _extract_total(self, text_lines: list, full_text: str) -> tuple:
        """
        Extract total amount.

        Strategy: Look for "Total:", "Amount Due:", "Grand Total:" patterns,
        typically at the bottom of the invoice.
        """
        logger.debug("Extracting total amount")
        
        # Expanded total patterns with currency symbols
        total_patterns = [
            # Patterns with explicit labels
            (r'(?:total\s+amount|total|grand\s+total|amount\s+due|balance\s+due|amount\s+payable|net\s+amount)[:\s]*[$€£¥]?\s*([\d,]+\.?\d*)', 0.35),
            (r'total\s*[$€£¥]\s*([\d,]+\.?\d*)', 0.3),
            (r'(?:balance\s+due|amount\s+payable)[:\s]*[$€£¥]?\s*([\d,]+\.?\d*)', 0.3),
            # Currency symbol patterns
            (r'[$€£¥]\s*([\d,]+\.?\d*)\s*(?:total|due|payable)?', 0.2),
            # Simple total patterns
            (r'total[:\s]*([\d,]+\.?\d*)', 0.25),
        ]

        candidates = []

        # Check last 30 lines instead of 20 (totals usually at bottom)
        for i, line in enumerate(reversed(text_lines[-30:])):
            text = line['text']
            confidence = line['confidence']
            actual_index = len(text_lines) - 30 + i

            for pattern, base_conf in total_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '')
                        amount = float(amount_str)
                        
                        # Skip zero or negative amounts
                        if amount <= 0:
                            continue
                        
                        # Higher confidence for explicit "total" labels
                        label_boost = 0.15 if 'total' in text.lower() else 0.0
                        # Position boost: higher for lines closer to the end
                        position_boost = i / 30.0 * 0.1
                        
                        calculated_conf = min(confidence + label_boost + base_conf + position_boost, 1.0)
                        
                        candidates.append({
                            'value': amount,
                            'confidence': calculated_conf,
                            'pattern': pattern,
                            'line_index': actual_index,
                            'text': text
                        })
                        logger.debug(f"Total candidate found: ${amount:.2f} (conf={calculated_conf:.2f})")
                    except ValueError:
                        pass

        # Return the candidate with the highest value (likely the grand total)
        # among those with reasonable confidence
        if candidates:
            # Filter by minimum confidence
            good_candidates = [c for c in candidates if c['confidence'] > 0.3]
            if good_candidates:
                # Return the highest value among good candidates (grand total)
                best = max(good_candidates, key=lambda x: x['value'])
                logger.info(f"Total extracted: ${best['value']:.2f} (confidence={best['confidence']:.2f})")
                return best['value'], best['confidence']
            else:
                # Fallback to highest confidence
                best = max(candidates, key=lambda x: x['confidence'])
                logger.info(f"Total extracted (fallback): ${best['value']:.2f} (confidence={best['confidence']:.2f})")
                return best['value'], best['confidence']

        logger.warning("No total found, using default")
        return 0.01, 0.0

    def _extract_invoice_number(self, text_lines: list, full_text: str) -> tuple:
        """
        Extract invoice number.

        Strategy: Look for "Invoice #:", "Invoice No:", "INV-:" patterns.
        """
        logger.debug("Extracting invoice number")
        
        # Expanded invoice number patterns
        invoice_patterns = [
            # Patterns with labels
            (r'(?:invoice\s*#?|invoice\s*no\.?|inv\s*#?|invoice\s+number)[:\s]*([A-Z0-9-]+)', 0.35),
            (r'(?:bill\s*#?|bill\s*no\.?|bill\s+number)[:\s]*([A-Z0-9-]+)', 0.3),
            (r'(?:ref\s*#?|reference|reference\s+number)[:\s]*([A-Z0-9-]+)', 0.25),
            # Patterns with prefixes
            (r'(?:INV|INV-|INVOICE)\s*[:#]?\s*([A-Z0-9-]+)', 0.3),
            (r'(?:BILL|BILL-)\s*[:#]?\s*([A-Z0-9-]+)', 0.25),
            # Alphanumeric patterns (fallback)
            (r'\b([A-Z]{2,4}[-_]?\d{4,})\b', 0.15),  # e.g., INV-1234, ABC12345
        ]

        candidates = []

        # Check first 40 lines instead of 30
        for i, line in enumerate(text_lines[:40]):
            text = line['text']
            confidence = line['confidence']

            for pattern, base_conf in invoice_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    invoice_num = match.group(1).strip()
                    
                    # Skip if it's just a number (likely not an invoice number)
                    if invoice_num.isdigit() and len(invoice_num) < 4:
                        continue
                    
                    # Calculate confidence
                    label_boost = 0.1 if any(label in text.lower() for label in ['invoice', 'bill', 'ref']) else 0.0
                    position_factor = max(0, (40 - i) / 40)  # Higher for earlier lines
                    
                    calculated_conf = min(confidence + base_conf + label_boost + (position_factor * 0.05), 1.0)
                    
                    candidates.append({
                        'value': invoice_num,
                        'confidence': calculated_conf,
                        'pattern': pattern,
                        'line_index': i
                    })
                    logger.debug(f"Invoice number candidate found: '{invoice_num}' (conf={calculated_conf:.2f})")

        # Return best candidate
        if candidates:
            best = max(candidates, key=lambda x: x['confidence'])
            logger.info(f"Invoice number extracted: '{best['value']}' (confidence={best['confidence']:.2f})")
            return best['value'], best['confidence']

        logger.info("No invoice number found")
        return None, 0.0


# =============================================================================
# Singleton instance for use in FastAPI
# =============================================================================

# Create a single instance to reuse across requests
_extractor_instance = None


def get_extractor() -> InvoiceExtractor:
    """Get or create the singleton extractor instance"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = InvoiceExtractor()
    return _extractor_instance