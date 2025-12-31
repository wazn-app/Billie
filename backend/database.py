"""
Billie MVP - Invoice Processing System
Database Models and Session Management

SQLAlchemy ORM with SQLite backend for local storage
"""

from sqlalchemy import create_engine, Column, Integer, String, Date, Numeric, DateTime, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from decimal import Decimal

# =============================================================================
# Database Configuration
# =============================================================================

# SQLite database file
DATABASE_URL = "sqlite+aiosqlite:///./billie.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL query logging
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# =============================================================================
# Database Models
# =============================================================================

class Vendor(Base):
    """Vendor model for invoice issuers"""
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to invoices
    invoices = relationship("Invoice", back_populates="vendor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vendor(id={self.id}, name='{self.name}')>"


class Invoice(Base):
    """Invoice model for processed invoices"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    date = Column(Date, nullable=True)
    total = Column(Numeric(10, 2), nullable=False)
    invoice_number = Column(String(255), nullable=True, index=True)
    status = Column(String(50), default="draft", nullable=False, index=True)  # draft, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to vendor
    vendor = relationship("Vendor", back_populates="invoices")

    def __repr__(self):
        return f"<Invoice(id={self.id}, file_id='{self.file_id}', status='{self.status}')>"

# =============================================================================
# Dependency Injection
# =============================================================================

async def get_db():
    """
    Dependency for getting database sessions.
    
    Usage in FastAPI:
        @app.get("/invoices")
        async def list_invoices(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# =============================================================================
# Database Initialization
# =============================================================================

async def init_db():
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)