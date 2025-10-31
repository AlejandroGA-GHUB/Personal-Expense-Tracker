import { useState, useRef, useEffect } from 'react';
import './CSVUpload.css';

const CSVUpload = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState('');
  const [detectedBank, setDetectedBank] = useState(null);
  const [detectingBank, setDetectingBank] = useState(false);
  const [categories, setCategories] = useState([]);
  const fileInputRef = useRef(null);

  // Fetch categories on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/categories');
        if (response.ok) {
          const data = await response.json();
          setCategories(data);
        }
      } catch (err) {
        console.error('Error fetching categories:', err);
      }
    };
    fetchCategories();
  }, []);

  // Helper function to get category name by ID
  const getCategoryName = (categoryId) => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.name : 'Unknown';
  };

  // Helper function to get category color by ID
  const getCategoryColor = (categoryId) => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.color : '#6c757d';
  };

  // Detect bank format from file
  const detectBankFormat = async (file) => {
    setDetectingBank(true);
    setDetectedBank(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/transactions/preview-csv', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.success && data.validation) {
        setDetectedBank({
          name: data.validation.format_name || 'Unknown',
          format: data.validation.format,
          isValid: data.validation.is_valid
        });
      }
    } catch (err) {
      console.error('Bank detection error:', err);
    } finally {
      setDetectingBank(false);
    }
  };

  // Handle file selection
  const handleFileSelect = (file) => {
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Please select a CSV file');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setSelectedFile(file);
    setError('');
    setPreviewData(null);
    setUploadResult(null);
    
    // Automatically detect bank format
    detectBankFormat(file);
  };

  // Handle drag events
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  // Handle file drop
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  // Handle file input change
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  // Handle preview
  const handlePreview = async () => {
    if (!selectedFile) {
      setError('Please select a CSV file first');
      return;
    }

    setPreviewing(true);
    setError('');
    setPreviewData(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://localhost:8000/api/transactions/preview-csv', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setPreviewData(data);
      } else {
        setError(data.detail || 'Failed to preview CSV file');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Preview error:', err);
    } finally {
      setPreviewing(false);
    }
  };

  // Handle file upload
  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a CSV file first');
      return;
    }

    setUploading(true);
    setError('');
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://localhost:8000/api/transactions/upload-csv', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setUploadResult(data);
        setPreviewData(null); // Clear preview after successful upload
        // Clear the file selection after successful upload
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        // Notify parent component of successful upload
        if (onUploadSuccess) {
          setTimeout(() => onUploadSuccess(), 2000); // Give user time to see success message
        }
      } else {
        setError(data.detail || 'Failed to upload CSV file');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  // Reset form
  const handleReset = () => {
    setSelectedFile(null);
    setError('');
    setPreviewData(null);
    setUploadResult(null);
    setDragActive(false);
    setDetectedBank(null);
    setDetectingBank(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="csv-upload-container">
      <h2>Import Transactions from CSV</h2>
      <p>Upload your CSV file to import transactions automatically</p>
      
      {/* Drag and Drop Area */}
      <div
        className={`upload-area ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'file-selected' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="upload-content">
          {selectedFile ? (
            <>
              <div className="file-info">
                <span className="file-icon">📄</span>
                <span className="file-name">{selectedFile.name}</span>
                <span className="file-size">({(selectedFile.size / 1024).toFixed(2)} KB)</span>
              </div>
              
              {/* Bank Detection Indicator */}
              {detectingBank && (
                <div className="bank-detection detecting">
                  <span className="detection-icon">🔍</span>
                  <span>Detecting bank format...</span>
                </div>
              )}
              
              {!detectingBank && detectedBank && (
                <div className={`bank-detection ${detectedBank.isValid ? 'detected' : 'unknown'}`}>
                  {detectedBank.isValid ? (
                    <>
                      <span className="detection-icon">✅</span>
                      <span><strong>{detectedBank.name}</strong> format detected</span>
                    </>
                  ) : (
                    <>
                      <span className="detection-icon">⚠️</span>
                      <span>Unknown bank format</span>
                    </>
                  )}
                </div>
              )}
            </>
          ) : (
            <>
              <div className="upload-icon">📂</div>
              <p>Drag and drop your CSV file here</p>
              <p className="upload-or">or</p>
            </>
          )}
          
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="file-input"
            id="csv-file-input"
          />
          <label htmlFor="csv-file-input" className="file-input-label">
            {selectedFile ? 'Choose Different File' : 'Choose File'}
          </label>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* Action Buttons */}
      {selectedFile && (
        <div className="upload-actions">
          <button
            onClick={handlePreview}
            disabled={previewing || uploading}
            className="preview-btn"
          >
            {previewing ? (
              <>
                <span className="loading-spinner"></span>
                Previewing...
              </>
            ) : (
              <>
                <span className="btn-icon">👁️</span>
                Preview Transactions
              </>
            )}
          </button>
          
          <button
            onClick={handleUpload}
            disabled={previewing || uploading}
            className="upload-btn"
          >
            {uploading ? (
              <>
                <span className="loading-spinner"></span>
                Uploading...
              </>
            ) : (
              <>
                <span className="btn-icon">📤</span>
                Upload & Import
              </>
            )}
          </button>

          <button onClick={handleReset} className="reset-btn">
            Clear
          </button>
        </div>
      )}

      {/* Preview Results */}
      {previewData && (
        <div className="preview-results">
          <h3>Preview Results</h3>
          <div className="preview-summary">
            <div className="summary-item">
              <span className="label">File:</span>
              <span className="value">{previewData.filename}</span>
            </div>
            <div className="summary-item">
              <span className="label">Detected Bank:</span>
              <span className="value">{previewData.validation.format_name || previewData.validation.format}</span>
            </div>
            <div className="summary-item">
              <span className="label">Transactions Found:</span>
              <span className="value">{previewData.total_transactions_found}</span>
            </div>
          </div>
          
          {previewData.preview_transactions.length > 0 && (
            <div className="preview-transactions">
              <h4>All Transactions ({previewData.preview_transactions.length}) with Auto-Categorization:</h4>
              <div className="preview-table-container">
                <div className="preview-table">
                  <div className="preview-header">
                    <span>Date</span>
                    <span>Description</span>
                    <span>Amount</span>
                    <span>Category</span>
                  </div>
                  {previewData.preview_transactions.map((transaction, index) => (
                    <div key={index} className="preview-row">
                      <span className="preview-date">{transaction.date}</span>
                      <span className="preview-description">{transaction.description}</span>
                      <span className={`preview-amount ${transaction.amount < 0 ? 'expense' : 'income'}`}>
                        {transaction.amount < 0 ? '-' : '+'}${Math.abs(transaction.amount).toFixed(2)}
                      </span>
                      <span className="preview-category">
                        <span 
                          className="category-badge" 
                          style={{ backgroundColor: getCategoryColor(transaction.category_id) }}
                        >
                          {getCategoryName(transaction.category_id)}
                        </span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Upload Results */}
      {uploadResult && (
        <div className="upload-results success">
          <div className="result-header">
            <span className="success-icon">✅</span>
            <h3>Upload Successful!</h3>
          </div>
          <div className="result-summary">
            <div className="summary-item">
              <span className="label">File:</span>
              <span className="value">{uploadResult.filename}</span>
            </div>
            {uploadResult.bank_format && (
              <div className="summary-item">
                <span className="label">Bank Format:</span>
                <span className="value">{uploadResult.bank_format}</span>
              </div>
            )}
            <div className="summary-item">
              <span className="label">Transactions Created:</span>
              <span className="value">{uploadResult.transactions_created}</span>
            </div>
            <div className="summary-item">
              <span className="label">Total Rows Processed:</span>
              <span className="value">{uploadResult.total_rows_processed}</span>
            </div>
          </div>
          <p className="result-message">{uploadResult.message}</p>
        </div>
      )}

      {/* File Format Info */}
      <div className="format-info">
        <h4>Supported Formats:</h4>
        <p>Automatically detects and imports transactions from:</p>
        <ul>
          <li>Bank of America CSV exports</li>
        </ul>
        <p className="format-note">The system will automatically detect your bank's format</p>
      </div>
    </div>
  );
};

export default CSVUpload;