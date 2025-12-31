import { useState, useEffect } from 'react';

export default function VendorSelect({ value, onChange, vendors, onCreateNew }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const filteredVendors = vendors.filter(vendor =>
    vendor.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelect = (vendorName) => {
    onChange(vendorName);
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleCreateNew = () => {
    onCreateNew();
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          value={value || searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 200)}
          className="input"
          placeholder="Select or type vendor name"
        />
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
          {filteredVendors.length === 0 ? (
            <div className="p-3 text-sm text-gray-500">
              No vendors found
            </div>
          ) : (
            filteredVendors.map((vendor) => (
              <button
                key={vendor.id}
                type="button"
                onClick={() => handleSelect(vendor.name)}
                className="w-full px-3 py-2 text-left hover:bg-gray-100 transition-colors"
              >
                {vendor.name}
              </button>
            ))
          )}
          <button
            type="button"
            onClick={handleCreateNew}
            className="w-full px-3 py-2 text-left text-primary-600 hover:bg-primary-50 transition-colors border-t border-gray-200"
          >
            + Create New Vendor
          </button>
        </div>
      )}
    </div>
  );
}