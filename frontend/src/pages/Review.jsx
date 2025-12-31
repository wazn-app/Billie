import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Document, Page, pdfjs } from 'react-pdf';
import { createInvoice, getVendors, createVendor } from '../api';
import { useToast } from '../contexts/ToastContext';
import VendorSelect from '../components/VendorSelect';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

export default function Review() {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const extractionResult = location.state?.extractionResult;
  const { success, error: showError } = useToast();

  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [pdfError, setPdfError] = useState(null);
  const [vendors, setVendors] = useState([]);
  const [showNewVendorModal, setShowNewVendorModal] = useState(false);
  const [newVendorName, setNewVendorName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isCreatingVendor, setIsCreatingVendor] = useState(false);
  const [error, setError] = useState(null);
  const [showExtractionSuccess, setShowExtractionSuccess] = useState(true);

  // Form state
  const [formData, setFormData] = useState({
    file_id: fileId,
    filename: extractionResult?.filename || '',
    vendor: extractionResult?.vendor || '',
    date: extractionResult?.date || '',
    total: extractionResult?.total || '',
    invoice_number: extractionResult?.invoice_number || '',
    status: 'draft',
  });

  // Confidence scores
  const confidence = {
    vendor: extractionResult?.vendor_confidence || 0,
    date: extractionResult?.date_confidence || 0,
    total: extractionResult?.total_confidence || 0,
    invoice_number: extractionResult?.invoice_number_confidence || 0,
  };

  useEffect(() => {
    loadVendors();
    // Auto-hide extraction success banner after 5 seconds
    const timer = setTimeout(() => {
      setShowExtractionSuccess(false);
    }, 5000);
    return () => clearTimeout(timer);
  }, []);

  const loadVendors = async () => {
    try {
      const data = await getVendors();
      setVendors(data);
    } catch (err) {
      console.error('Failed to load vendors:', err);
    }
  };

  const handlePdfLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const handlePdfLoadError = (error) => {
    setPdfError('Failed to load PDF');
    console.error('PDF load error:', error);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleVendorChange = (value) => {
    if (value === '__new__') {
      setShowNewVendorModal(true);
    } else {
      setFormData(prev => ({ ...prev, vendor: value }));
    }
  };

  const handleCreateVendor = async () => {
    if (!newVendorName.trim()) return;
    
    setIsCreatingVendor(true);
    setError(null);

    try {
      const newVendor = await createVendor({ name: newVendorName });
      setVendors(prev => [...prev, newVendor]);
      setFormData(prev => ({ ...prev, vendor: newVendor.name }));
      setShowNewVendorModal(false);
      setNewVendorName('');
      success(`Vendor "${newVendor.name}" created successfully!`);
    } catch (err) {
      setError(err.detail || 'Failed to create vendor');
      showError(err.detail || 'Failed to create vendor');
    } finally {
      setIsCreatingVendor(false);
    }
  };

  const handleSave = async (status) => {
    setIsSaving(true);
    setError(null);

    // Validate required fields before API call
    const validationErrors = [];
    
    // Validate vendor (handle both string and numeric types)
    if (!formData.vendor) {
      validationErrors.push('Vendor is required');
    } else if (typeof formData.vendor === 'string') {
      if (formData.vendor.trim() === '') {
        validationErrors.push('Vendor is required');
      }
    }
    
    // Validate total (handle both string and numeric types)
    if (!formData.total) {
      validationErrors.push('Total amount is required');
    } else if (typeof formData.total === 'string') {
      if (formData.total.trim() === '') {
        validationErrors.push('Total amount is required');
      } else {
        const totalValue = parseFloat(formData.total);
        if (isNaN(totalValue) || totalValue <= 0) {
          validationErrors.push('Total amount must be a valid number greater than 0');
        }
      }
    } else if (typeof formData.total === 'number') {
      if (isNaN(formData.total) || formData.total <= 0) {
        validationErrors.push('Total amount must be a valid number greater than 0');
      }
    }

    if (validationErrors.length > 0) {
      const errorMessage = validationErrors.join('. ');
      setError(errorMessage);
      showError(errorMessage);
      setIsSaving(false);
      return;
    }

    try {
      const invoiceData = {
        file_id: formData.file_id,
        filename: formData.filename || null,
        vendor: formData.vendor,
        date: formData.date || null,
        total: parseFloat(formData.total),
        invoice_number: formData.invoice_number || null,
        status,
      };

      await createInvoice(invoiceData);
      
      if (status === 'approved') {
        success('Invoice saved and approved successfully!');
      } else {
        success('Invoice rejected.');
      }
      
      // Small delay to show the toast before navigation
      setTimeout(() => {
        navigate('/invoices');
      }, 500);
    } catch (err) {
      setError(err.detail || 'Failed to save invoice');
      showError(err.detail || 'Failed to save invoice');
      setIsSaving(false);
    }
  };

  const handleReject = () => {
    handleSave('rejected');
  };

  const ConfidenceBadge = ({ score }) => {
    if (score >= 0.8) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
          High confidence
        </span>
      );
    } else if (score > 0) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
          Low confidence - please review
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
        Not detected
      </span>
    );
  };

  const LowConfidenceHighlight = ({ children, score }) => {
    if (score < 0.8 && score > 0) {
      return <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-1">{children}</div>;
    }
    return <>{children}</>;
  };

  return (
    <div className="space-y-6">
      {/* OCR Extraction Success Banner */}
      {showExtractionSuccess && extractionResult && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 animate-slide-in">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-green-800">
                Data extracted successfully!
              </p>
              <p className="text-sm text-green-700">
                Review the extracted data below and make any corrections before saving.
              </p>
            </div>
            <button
              onClick={() => setShowExtractionSuccess(false)}
              className="ml-auto flex-shrink-0 text-green-500 hover:text-green-700"
            >
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Review Invoice</h1>
          <p className="text-gray-600 mt-1">Verify and edit extracted data</p>
        </div>
        <button
          onClick={() => navigate('/invoices')}
          className="btn btn-secondary"
        >
          Cancel
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PDF Viewer - Left Side */}
        <div className="card overflow-hidden">
          <div className="bg-gray-50 border-b border-gray-200 px-4 py-3">
            <h2 className="font-medium text-gray-900">Original Invoice</h2>
          </div>
          <div className="p-4 bg-gray-100 min-h-[600px] flex items-center justify-center">
            {pdfError ? (
              <div className="text-center text-gray-500">
                <svg className="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>{pdfError}</p>
              </div>
            ) : (
              <Document
                file={`http://localhost:8000/uploads/${fileId}.pdf`}
                onLoadSuccess={handlePdfLoadSuccess}
                onLoadError={handlePdfLoadError}
                className="max-w-full"
              >
                <Page
                  pageNumber={pageNumber}
                  scale={1.2}
                  className="shadow-lg"
                />
              </Document>
            )}
          </div>
          {numPages && numPages > 1 && (
            <div className="bg-gray-50 border-t border-gray-200 px-4 py-3 flex items-center justify-between">
              <button
                onClick={() => setPageNumber(p => Math.max(1, p - 1))}
                disabled={pageNumber === 1}
                className="btn btn-secondary text-sm"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {pageNumber} of {numPages}
              </span>
              <button
                onClick={() => setPageNumber(p => Math.min(numPages, p + 1))}
                disabled={pageNumber === numPages}
                className="btn btn-secondary text-sm"
              >
                Next
              </button>
            </div>
          )}
        </div>

        {/* Edit Form - Right Side */}
        <div className="card">
          <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
            <h2 className="font-medium text-gray-900">Extracted Data</h2>
          </div>
          <div className="p-6 space-y-6">
            {/* Vendor */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vendor
              </label>
              <LowConfidenceHighlight score={confidence.vendor}>
                <VendorSelect
                  value={formData.vendor}
                  onChange={handleVendorChange}
                  vendors={vendors}
                  onCreateNew={() => setShowNewVendorModal(true)}
                />
              </LowConfidenceHighlight>
              <div className="mt-2">
                <ConfidenceBadge score={confidence.vendor} />
              </div>
            </div>

            {/* Invoice Number */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Invoice Number
              </label>
              <LowConfidenceHighlight score={confidence.invoice_number}>
                <input
                  type="text"
                  name="invoice_number"
                  value={formData.invoice_number}
                  onChange={handleInputChange}
                  className="input"
                  placeholder="INV-2024-001"
                />
              </LowConfidenceHighlight>
              <div className="mt-2">
                <ConfidenceBadge score={confidence.invoice_number} />
              </div>
            </div>

            {/* Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Invoice Date
              </label>
              <LowConfidenceHighlight score={confidence.date}>
                <input
                  type="date"
                  name="date"
                  value={formData.date}
                  onChange={handleInputChange}
                  className="input"
                />
              </LowConfidenceHighlight>
              <div className="mt-2">
                <ConfidenceBadge score={confidence.date} />
              </div>
            </div>

            {/* Total */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Total Amount
              </label>
              <LowConfidenceHighlight score={confidence.total}>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <input
                    type="number"
                    name="total"
                    value={formData.total}
                    onChange={handleInputChange}
                    step="0.01"
                    min="0"
                    className="input pl-7"
                    placeholder="0.00"
                  />
                </div>
              </LowConfidenceHighlight>
              <div className="mt-2">
                <ConfidenceBadge score={confidence.total} />
              </div>
            </div>

            {/* Actions */}
            <div className="pt-6 border-t border-gray-200 space-y-3">
              <button
                onClick={() => handleSave('approved')}
                disabled={isSaving}
                className="w-full btn btn-success flex items-center justify-center"
              >
                {isSaving ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Saving...
                  </>
                ) : (
                  'Save & Approve'
                )}
              </button>
              <button
                onClick={handleReject}
                disabled={isSaving}
                className="w-full btn btn-secondary"
              >
                Reject
              </button>
            </div>

            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg animate-pulse">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-red-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-red-700">{error}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* New Vendor Modal */}
      {showNewVendorModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Vendor</h3>
            <input
              type="text"
              value={newVendorName}
              onChange={(e) => setNewVendorName(e.target.value)}
              className="input mb-4"
              placeholder="Vendor name"
              autoFocus
            />
            <div className="flex space-x-3">
              <button
                onClick={handleCreateVendor}
                disabled={!newVendorName.trim() || isCreatingVendor}
                className="btn btn-primary flex-1"
              >
                {isCreatingVendor ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 inline" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating...
                  </>
                ) : (
                  'Create'
                )}
              </button>
              <button
                onClick={() => {
                  setShowNewVendorModal(false);
                  setNewVendorName('');
                }}
                className="btn btn-secondary flex-1"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}