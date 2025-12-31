# Billie MVP - Invoice Processing System

A web application that automates invoice data extraction using open-source OCR (PaddleOCR). Users upload PDF invoices, the system extracts key fields, displays a split-screen review interface for verification, and exports clean data to CSV.

## Features

- **PDF Upload** - Drag-and-drop interface for uploading invoice PDFs
- **OCR Extraction** - Automatic extraction of vendor, date, total, and invoice number using PaddleOCR
- **Confidence Scoring** - Each extracted field includes a confidence score; low-confidence fields are highlighted for manual review
- **Split-Screen Review** - PDF viewer on the left, editable form on the right
- **Vendor Management** - Create vendors from invoices or select from existing
- **Invoice Status Tracking** - Track invoices as draft, approved, or rejected
- **CSV Export** - Export approved invoices formatted for Excel/QuickBooks/Xero
- **Responsive Design** - Works on desktop and mobile devices

## Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite** - Local database storage
- **PaddleOCR** - Open-source OCR library
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **react-pdf** - PDF viewing
- **Axios** - HTTP client

## Project Structure

```
Billie/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # SQLAlchemy models and session management
│   ├── models.py            # Pydantic schemas for validation
│   ├── ocr.py               # PaddleOCR extraction wrapper
│   ├── requirements.txt     # Python dependencies
│   ├── uploads/             # Uploaded PDF files
│   └── test_invoices/       # Sample invoices for testing
├── frontend/
│   ├── src/
│   │   ├── api.js           # API client with axios
│   │   ├── App.jsx          # Main app with routing
│   │   ├── main.jsx         # React entry point
│   │   ├── index.css        # Global styles with Tailwind
│   │   ├── pages/
│   │   │   ├── Upload.jsx   # Invoice upload page
│   │   │   ├── Review.jsx   # Split-screen review workspace
│   │   │   └── InvoiceList.jsx # Invoice list with export
│   │   └── components/
│   │       └── VendorSelect.jsx # Vendor dropdown component
│   ├── package.json         # Node dependencies
│   ├── vite.config.js       # Vite configuration
│   ├── tailwind.config.js   # Tailwind configuration
│   └── index.html           # HTML entry point
└── README.md                # This file
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload PDF and extract data |
| GET | `/invoices` | List invoices (with optional status filter) |
| POST | `/invoices` | Save invoice data |
| GET | `/invoices/{id}` | Get single invoice |
| PUT | `/invoices/{id}` | Update invoice |
| DELETE | `/invoices/{id}` | Delete invoice |
| GET | `/vendors` | List all vendors |
| POST | `/vendors` | Create new vendor |
| GET | `/export/csv` | Export approved invoices to CSV |

## Usage

1. **Upload Invoice**: Navigate to the home page and drag-drop a PDF invoice
2. **Review Extracted Data**: The system will extract data and show it in a split-screen view
3. **Edit and Approve**: Review the extracted data, make corrections if needed, and click "Save & Approve"
4. **Export**: Go to the Invoices page and click "Export CSV" to download approved invoices

## Development

### Running Tests

Backend tests (pytest):
```bash
cd backend
pytest
```

Frontend tests (React Testing Library):
```bash
cd frontend
npm test
```

### Building for Production

Frontend:
```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`

## License

This project is open source and available under the MIT License.