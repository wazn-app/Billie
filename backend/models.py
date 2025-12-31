"""
Billie MVP - Invoice Processing System
Pydantic Schemas for Request/Response Validation

Data validation and serialization for API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import date
from decimal import Decimal

# =============================================================================
# Invoice Schemas
# =============================================================================

class InvoiceCreate(BaseModel):
    """Schema for creating/updating invoices"""
    filename: Optional[str] = None
    file_id: str = Field(..., description="UUID of the uploaded file")
    vendor: str = Field(..., min_length=1, max_length=255, description="Vendor name")
    date: Optional[date] = None
    total: Decimal = Field(..., gt=0, description="Invoice total amount")
    invoice_number: Optional[str] = Field(None, max_length=255, description="Invoice number")
    status: Optional[str] = Field("draft", pattern="^(draft|approved|rejected)$")

    class Config:
        json_encoders = {
            Decimal: float,
            date: lambda v: v.isoformat() if v else None
        }


class InvoiceResponse(BaseModel):
    """Schema for invoice response"""
    id: int
    filename: str
    file_id: str
    vendor: str
    vendor_id: int
    date: Optional[str] = None
    total: float
    invoice_number: Optional[str] = None
    status: str
    created_at: str

    class Config:
        from_attributes = True


# =============================================================================
# Extraction Result Schemas
# =============================================================================

class ExtractionResult(BaseModel):
    """Schema for OCR extraction result with confidence scores"""
    vendor: Optional[str] = None
    vendor_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score for vendor extraction")
    date: Optional[str] = None
    date_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score for date extraction")
    total: Optional[float] = None
    total_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score for total extraction")
    invoice_number: Optional[str] = None
    invoice_number_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score for invoice number extraction")
    file_id: Optional[str] = Field(None, description="UUID of the uploaded file")
    filename: Optional[str] = Field(None, description="Original filename")

    class Config:
        json_schema_extra = {
            "example": {
                "vendor": "Acme Corp",
                "vendor_confidence": 0.92,
                "date": "2024-01-15",
                "date_confidence": 0.95,
                "total": 1250.50,
                "total_confidence": 0.98,
                "invoice_number": "INV-2024-001",
                "invoice_number_confidence": 0.88,
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "acme_invoice.pdf"
            }
        }


# =============================================================================
# Vendor Schemas
# =============================================================================

class VendorCreate(BaseModel):
    """Schema for creating vendors"""
    name: str = Field(..., min_length=1, max_length=255, description="Vendor name")

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Vendor name cannot be empty')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corporation"
            }
        }


class VendorResponse(BaseModel):
    """Schema for vendor response"""
    id: int
    name: str
    created_at: str

    class Config:
        from_attributes = True


# =============================================================================
# Error Response Schemas
# =============================================================================

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Unable to process PDF file"
            }
        }


# =============================================================================
# Health Check Schema
# =============================================================================

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: str
    service: str