import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { ToastProvider } from './contexts/ToastContext';
import Upload from './pages/Upload';
import Review from './pages/Review';
import InvoiceList from './pages/InvoiceList';

// Navigation component
function Navigation() {
  const location = useLocation();
  
  const isActive = (path) => {
    return location.pathname === path ? 'text-primary-500' : 'text-gray-600 hover:text-primary-500';
  };

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <span className="text-xl font-semibold text-gray-900">Billie</span>
            </Link>
          </div>
          
          <div className="flex items-center space-x-4">
            <Link
              to="/"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/')}`}
            >
              Upload
            </Link>
            <Link
              to="/invoices"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/invoices')}`}
            >
              Invoices
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

// Main App component
function App() {
  return (
    <ToastProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Routes>
              <Route path="/" element={<Upload />} />
              <Route path="/review/:fileId" element={<Review />} />
              <Route path="/invoices" element={<InvoiceList />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ToastProvider>
  );
}

export default App;