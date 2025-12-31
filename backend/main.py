"""
Billie MVP - Invoice Processing System
FastAPI Application Entry Point

Greenfield project - async/await pattern with dependency injection
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os
from pathlib import Path
from datetime import datetime
import uuid
from typing import Optional, List
import shutil

from database import get_db, engine, Base
from models import (
    InvoiceCreate,
    InvoiceResponse,
    ExtractionResult,
    VendorCreate,
    VendorResponse
)
try:
    from ocr import InvoiceExtractor
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    InvoiceExtractor = None

# =============================================================================
# Configuration
# =============================================================================

# Project paths
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEST_INVOICES_DIR = BASE_DIR / "test_invoices"

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
TEST_INVOICES_DIR.mkdir(exist_ok=True)

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Billie MVP - Invoice Processing System",
    description="Automated invoice data extraction using PaddleOCR",
    version="0.1.0"
)

# CORS middleware for Vite dev server (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded PDFs
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# =============================================================================
# Startup Events
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# =============================================================================
# Health Check
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connectivity
        from database import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "billie-invoice-processor",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "billie-invoice-processor",
            "database": "disconnected",
            "error": str(e)
        }, 503

# =============================================================================
# OCR Instance
# =============================================================================

if OCR_AVAILABLE:
    ocr_extractor = InvoiceExtractor()
else:
    ocr_extractor = None

# =============================================================================
# File Upload & Processing Endpoint (Task 5)
# =============================================================================

@app.post("/upload", response_model=ExtractionResult)
async def upload_invoice(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload PDF invoice and extract data using OCR.

    Validates file type and size, saves with UUID filename, triggers OCR extraction.
    Returns ExtractionResult with confidence scores.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Validate file size (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit"
        )
    # Reset file pointer for reading
    await file.seek(0)

    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.pdf"
    file_path = UPLOAD_DIR / filename

    # Save uploaded file
    try:
        with file_path.open("wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    # Perform OCR extraction
    if not OCR_AVAILABLE:
        # OCR not available - return empty extraction
        return {
            "vendor": None,
            "vendor_confidence": 0.0,
            "date": None,
            "date_confidence": 0.0,
            "total": None,
            "total_confidence": 0.0,
            "invoice_number": None,
            "invoice_number_confidence": 0.0,
            "file_id": file_id,
            "filename": file.filename
        }
    
    try:
        extraction_result = await ocr_extractor.extract(file_path)
        extraction_result["file_id"] = file_id
        extraction_result["filename"] = file.filename
        return extraction_result
    except Exception as e:
        # Clean up file on OCR failure
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=400,
            detail="Unable to process PDF file"
        )

# =============================================================================
# Invoice CRUD Endpoints (Task 6)
# =============================================================================

@app.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(
    invoice: InvoiceCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Save extracted invoice data to database.

    Auto-creates vendor if doesn't exist.
    """
    from sqlalchemy import select
    from database import Invoice, Vendor

    # Find or create vendor
    result = await db.execute(
        select(Vendor).where(Vendor.name == invoice.vendor)
    )
    vendor = result.scalar_one_or_none()

    if not vendor:
        vendor = Vendor(name=invoice.vendor)
        db.add(vendor)
        await db.flush()  # Get the vendor ID

    # Create invoice
    db_invoice = Invoice(
        filename=invoice.filename or "unknown.pdf",
        file_id=invoice.file_id,
        vendor_id=vendor.id,
        date=invoice.date,
        total=invoice.total,
        invoice_number=invoice.invoice_number,
        status=invoice.status or "draft"
    )
    db.add(db_invoice)
    await db.commit()
    await db.refresh(db_invoice)

    return InvoiceResponse(
        id=db_invoice.id,
        filename=db_invoice.filename,
        file_id=db_invoice.file_id,
        vendor=vendor.name,
        vendor_id=vendor.id,
        date=db_invoice.date.isoformat() if db_invoice.date else None,
        total=float(db_invoice.total),
        invoice_number=db_invoice.invoice_number,
        status=db_invoice.status,
        created_at=db_invoice.created_at.isoformat()
    )


@app.get("/invoices")
async def list_invoices(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List invoices with optional status filter.

    Filters: draft, approved, rejected
    Returns paginated results with total count.
    """
    from sqlalchemy import select, func
    from database import Invoice, Vendor

    # Build base query
    query = select(Invoice, Vendor).join(Vendor)
    count_query = select(func.count()).select_from(Invoice)

    if status:
        query = query.where(Invoice.status == status)
        count_query = count_query.where(Invoice.status == status)

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Get paginated results
    query = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    invoices = result.all()

    return {
        "data": [
            InvoiceResponse(
                id=invoice.id,
                filename=invoice.filename,
                file_id=invoice.file_id,
                vendor=vendor.name,
                vendor_id=vendor.id,
                date=invoice.date.isoformat() if invoice.date else None,
                total=float(invoice.total),
                invoice_number=invoice.invoice_number,
                status=invoice.status,
                created_at=invoice.created_at.isoformat()
            )
            for invoice, vendor in invoices
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@app.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get single invoice by ID"""
    from sqlalchemy import select
    from database import Invoice, Vendor

    result = await db.execute(
        select(Invoice, Vendor).join(Vendor).where(Invoice.id == invoice_id)
    )
    invoice = result.first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    db_invoice, vendor = invoice

    return InvoiceResponse(
        id=db_invoice.id,
        filename=db_invoice.filename,
        file_id=db_invoice.file_id,
        vendor=vendor.name,
        vendor_id=vendor.id,
        date=db_invoice.date.isoformat() if db_invoice.date else None,
        total=float(db_invoice.total),
        invoice_number=db_invoice.invoice_number,
        status=db_invoice.status,
        created_at=db_invoice.created_at.isoformat()
    )


@app.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    invoice: InvoiceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update invoice (e.g., after user review/edit)"""
    from sqlalchemy import select
    from database import Invoice, Vendor

    # Get existing invoice
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    db_invoice = result.scalar_one_or_none()

    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Find or create vendor
    vendor_result = await db.execute(
        select(Vendor).where(Vendor.name == invoice.vendor)
    )
    vendor = vendor_result.scalar_one_or_none()

    if not vendor:
        vendor = Vendor(name=invoice.vendor)
        db.add(vendor)
        await db.flush()

    # Update fields
    db_invoice.vendor_id = vendor.id
    db_invoice.date = invoice.date
    db_invoice.total = invoice.total
    db_invoice.invoice_number = invoice.invoice_number
    db_invoice.status = invoice.status or db_invoice.status

    await db.commit()
    await db.refresh(db_invoice)

    return InvoiceResponse(
        id=db_invoice.id,
        filename=db_invoice.filename,
        file_id=db_invoice.file_id,
        vendor=vendor.name,
        vendor_id=vendor.id,
        date=db_invoice.date.isoformat() if db_invoice.date else None,
        total=float(db_invoice.total),
        invoice_number=db_invoice.invoice_number,
        status=db_invoice.status,
        created_at=db_invoice.created_at.isoformat()
    )


@app.delete("/invoices/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete invoice by ID"""
    from sqlalchemy import select
    from database import Invoice

    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Delete associated file
    file_path = UPLOAD_DIR / f"{invoice.file_id}.pdf"
    if file_path.exists():
        file_path.unlink()

    await db.delete(invoice)
    await db.commit()

    return {"message": "Invoice deleted successfully"}

# =============================================================================
# Vendor Management Endpoints (Task 7)
# =============================================================================

@app.get("/vendors", response_model=List[VendorResponse])
async def list_vendors(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all vendors"""
    from sqlalchemy import select
    from database import Vendor

    result = await db.execute(
        select(Vendor)
        .order_by(Vendor.name)
        .offset(skip)
        .limit(limit)
    )
    vendors = result.scalars().all()

    return [
        VendorResponse(
            id=vendor.id,
            name=vendor.name,
            created_at=vendor.created_at.isoformat()
        )
        for vendor in vendors
    ]


@app.post("/vendors", response_model=VendorResponse)
async def create_vendor(
    vendor: VendorCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new vendor"""
    from database import Vendor

    # Check if vendor already exists
    from sqlalchemy import select
    result = await db.execute(
        select(Vendor).where(Vendor.name == vendor.name)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Vendor with this name already exists"
        )

    db_vendor = Vendor(name=vendor.name)
    db.add(db_vendor)
    await db.commit()
    await db.refresh(db_vendor)

    return VendorResponse(
        id=db_vendor.id,
        name=db_vendor.name,
        created_at=db_vendor.created_at.isoformat()
    )


@app.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get vendor details"""
    from sqlalchemy import select
    from database import Vendor

    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id)
    )
    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return VendorResponse(
        id=vendor.id,
        name=vendor.name,
        created_at=vendor.created_at.isoformat()
    )

# =============================================================================
# CSV Export Endpoint (Task 8)
# =============================================================================

@app.get("/export/csv")
async def export_csv(
    db: AsyncSession = Depends(get_db)
):
    """
    Export approved invoices to CSV.

    Format: Vendor, Date, Invoice#, Total, Status
    Downloaded as: billie-export-YYYY-MM-DD.csv
    """
    from fastapi.responses import StreamingResponse
    from sqlalchemy import select
    from database import Invoice, Vendor
    import io
    import pandas as pd
    from datetime import datetime

    # Get approved invoices
    result = await db.execute(
        select(Invoice, Vendor)
        .join(Vendor)
        .where(Invoice.status == "approved")
        .order_by(Invoice.date.desc())
    )
    invoices = result.all()

    # Build data for CSV
    data = [
        {
            "Vendor": vendor.name,
            "Date": invoice.date.isoformat() if invoice.date else "",
            "Invoice#": invoice.invoice_number or "",
            "Total": f"{float(invoice.total):.2f}",
            "Status": invoice.status
        }
        for invoice, vendor in invoices
    ]

    # Generate CSV with pandas
    df = pd.DataFrame(data)

    # Create output stream
    output = io.StringIO()
    df.to_csv(output, index=False)

    # Generate filename with timestamp
    filename = f"billie-export-{datetime.now().strftime('%Y-%m-%d')}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """API information"""
    return {
        "name": "Billie MVP - Invoice Processing API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "upload": "POST /upload",
            "invoices": "GET /invoices, POST /invoices",
            "invoice": "GET /invoices/{id}, PUT /invoices/{id}, DELETE /invoices/{id}",
            "vendors": "GET /vendors, POST /vendors",
            "export": "GET /export/csv"
        }
    }
