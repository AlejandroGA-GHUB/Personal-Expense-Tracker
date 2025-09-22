import { useState } from 'react';
import './CSVUpload.css';

const CSVUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  // Handle file selection
  const handleFileSelect = (file) => {
    if (file && file.type === 'text/csv') {
      setSelectedFile(file);
      setUploadStatus(`Selected: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`);
    } else {
      setUploadStatus('Please select a valid CSV file');
      setSelectedFile(null);
    }
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

  // Handle file upload
  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus('Please select a file first');
      return;
    }

    setUploadStatus('Uploading...');
    
    // TODO: Add actual upload logic here
    // For now, just simulate upload
    setTimeout(() => {
      setUploadStatus(`✅ Successfully uploaded ${selectedFile.name}`);
    }, 1500);
  };

  // Reset form
  const handleReset = () => {
    setSelectedFile(null);
    setUploadStatus('');
    setDragActive(false);
  };

  return (
    <div className="csv-upload-container">
      <h2>Upload Bank Statement</h2>
      <p>Upload your CSV bank statement to start tracking your finances</p>
      
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
            </>
          ) : (
            <>
              <div className="upload-icon">📂</div>
              <p>Drag and drop your CSV file here</p>
              <p className="upload-or">or</p>
            </>
          )}
          
          <input
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

      {/* Status Message */}
      {uploadStatus && (
        <div className={`status-message ${uploadStatus.includes('✅') ? 'success' : ''}`}>
          {uploadStatus}
        </div>
      )}

      {/* Action Buttons */}
      <div className="upload-actions">
        <button 
          onClick={handleUpload} 
          disabled={!selectedFile || uploadStatus.includes('Uploading')}
          className="upload-btn"
        >
          {uploadStatus.includes('Uploading') ? 'Uploading...' : 'Upload File'}
        </button>
        
        {selectedFile && (
          <button onClick={handleReset} className="reset-btn">
            Clear
          </button>
        )}
      </div>

      {/* File Format Info */}
      <div className="format-info">
        <h4>Supported Format:</h4>
        <p>CSV files with columns like: Date, Description, Amount, Category</p>
        <p>Example: "2024-01-15", "Coffee Shop", "-4.50", "Food"</p>
      </div>
    </div>
  );
};

export default CSVUpload;