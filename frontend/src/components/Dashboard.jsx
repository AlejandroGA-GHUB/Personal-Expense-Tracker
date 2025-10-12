import { useState, useEffect } from 'react';
import './Dashboard.css';
import CSVUpload from './CSVUpload';

const Dashboard = () => {
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [showAddCategory, setShowAddCategory] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDescription, setNewCategoryDescription] = useState('');
  const [addingCategory, setAddingCategory] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    category: 'all',
    transactionType: 'all'
  });
  const [tempFilters, setTempFilters] = useState({
    category: 'all',
    transactionType: 'all'
  });
  const [showCSVUpload, setShowCSVUpload] = useState(false);
  const [showFileInfo, setShowFileInfo] = useState(false);
  const [selectedFileInfo, setSelectedFileInfo] = useState(null);
  
  const TRANSACTIONS_PER_PAGE = 100;

  // Load categories on component mount
  useEffect(() => {
    loadCategories();
  }, []);

  // Load transactions when filters or page changes
  useEffect(() => {
    loadTransactions();
  }, [filters, currentPage]);

  const loadCategories = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/categories/');
      if (response.ok) {
        const data = await response.json();
        setCategories(data);
      } else {
        setError('Failed to load categories');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Error loading categories:', err);
    }
  };

  const loadTransactions = async () => {
    setLoading(true);
    setError('');
    
    try {
      let url;
      const skip = currentPage * TRANSACTIONS_PER_PAGE;
      
      // Determine URL based on filters
      if (filters.category !== 'all' && filters.transactionType !== 'all') {
        // Both filters applied - we'll need to get category transactions and filter client-side for now
        // In production, you'd want a combined endpoint
        url = `http://localhost:8000/api/transactions/category/${filters.category}`;
      } else if (filters.category !== 'all') {
        // Only category filter
        url = `http://localhost:8000/api/transactions/category/${filters.category}`;
      } else if (filters.transactionType !== 'all') {
        // Only transaction type filter
        const typeParam = filters.transactionType === 'expense' ? 'Expense' : 'Income';
        url = `http://localhost:8000/api/transactions/expense_or_income/${typeParam}`;
      } else {
        // No filters - get all transactions with pagination
        url = `http://localhost:8000/api/transactions/?skip=${skip}&limit=${TRANSACTIONS_PER_PAGE}`;
      }
      
      const response = await fetch(url);
      
      if (response.ok) {
        let data = await response.json();
        
        // Client-side filtering if both filters are applied
        if (filters.category !== 'all' && filters.transactionType !== 'all') {
          data = data.filter(transaction => {
            const isExpense = transaction.amount < 0;
            const matchesType = filters.transactionType === 'expense' ? isExpense : !isExpense;
            return matchesType;
          });
        }
        
        if (currentPage === 0) {
          setTransactions(data);
        } else {
          setTransactions(prev => [...prev, ...data]);
        }
        
        // Check if there are more transactions (only for unfiltered results)
        setHasMore(filters.category === 'all' && filters.transactionType === 'all' && data.length === TRANSACTIONS_PER_PAGE);
      } else {
        setError('Failed to load transactions');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Error loading transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(0);
    setTransactions([]);
  };

  const loadMoreTransactions = () => {
    if (filters.category === 'all' && filters.transactionType === 'all' && hasMore) {
      setCurrentPage(prev => prev + 1);
    }
  };

  const resetFilters = () => {
    setFilters({ category: 'all', transactionType: 'all' });
    setCurrentPage(0);
    setTransactions([]);
  };

  const getActiveFiltersCount = () => {
    let count = 0;
    if (filters.category !== 'all') count++;
    if (filters.transactionType !== 'all') count++;
    return count;
  };

  const getFilterSummary = () => {
    const parts = [];
    if (filters.category !== 'all') {
      const categoryName = getCategoryName(parseInt(filters.category));
      parts.push(`Category: ${categoryName}`);
    }
    if (filters.transactionType !== 'all') {
      parts.push(`Type: ${filters.transactionType === 'expense' ? 'Expenses' : 'Income'}`);
    }
    return parts.length > 0 ? parts.join(', ') : 'All Transactions';
  };

  const handleAddCategory = async () => {
    if (!newCategoryName.trim()) {
      setError('Category name is required');
      return;
    }

    setAddingCategory(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/categories/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newCategoryName.trim(),
          description: newCategoryDescription.trim() || null
        })
      });

      if (response.ok) {
        const newCategory = await response.json();
        setCategories(prev => [...prev, newCategory]);
        setNewCategoryName('');
        setNewCategoryDescription('');
        setShowAddCategory(false);
        setError('');
      } else {
        setError('Failed to create category');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Error creating category:', err);
    } finally {
      setAddingCategory(false);
    }
  };

  const handleCancelAddCategory = () => {
    setShowAddCategory(false);
    setNewCategoryName('');
    setNewCategoryDescription('');
    setError('');
  };

  const formatAmount = (amount) => {
    const isExpense = amount < 0;
    return {
      value: Math.abs(amount).toFixed(2),
      isExpense
    };
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getCategoryName = (categoryId) => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.name : 'Unknown';
  };

  const formatSourceInfo = (transaction) => {
    if (transaction.source_file && transaction.original_row) {
      return {
        type: 'csv',
        fileName: transaction.source_file,
        row: transaction.original_row,
        display: 'CSV Import'
      };
    }
    return {
      type: 'manual',
      display: 'Manual Entry'
    };
  };

  if (loading && transactions.length === 0) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading transactions...</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>Transaction Dashboard</h2>
        <div className="dashboard-summary">
          <span className="transaction-count">
            {transactions.length} transaction{transactions.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="filter-controls">
        <div className="filter-summary">
          <span className="filter-label">Showing: </span>
          <span className="filter-text">{getFilterSummary()}</span>
          {getActiveFiltersCount() > 0 && (
            <button onClick={resetFilters} className="clear-filters-btn">
              Clear Filters
            </button>
          )}
        </div>
        
        <div className="filter-actions">
          <button 
            onClick={() => {
              setTempFilters(filters); // Initialize temp filters with current filters
              setShowFilters(true);
            }}
            className="filter-btn"
          >
            <span>🔍 Filter</span>
            {getActiveFiltersCount() > 0 && (
              <span className="filter-badge">{getActiveFiltersCount()}</span>
            )}
          </button>
          
          <button 
            onClick={() => setShowAddCategory(true)}
            className="add-category-btn"
            disabled={showAddCategory}
          >
            + Add Category
          </button>

          <button 
            onClick={() => setShowCSVUpload(true)}
            className="csv-upload-btn"
          >
            📤 Import CSV
          </button>
        </div>
      </div>

      {/* Add Category Form */}
      {showAddCategory && (
        <div className="add-category-form">
          <div className="form-header">
            <h3>Create New Category</h3>
          </div>
          <div className="form-fields">
            <div className="field-group">
              <label htmlFor="category-name">Category Name *</label>
              <input
                id="category-name"
                type="text"
                value={newCategoryName}
                onChange={(e) => setNewCategoryName(e.target.value)}
                placeholder="e.g., Entertainment, Utilities"
                maxLength={100}
                disabled={addingCategory}
              />
            </div>
            <div className="field-group">
              <label htmlFor="category-description">Description (Optional)</label>
              <input
                id="category-description"
                type="text"
                value={newCategoryDescription}
                onChange={(e) => setNewCategoryDescription(e.target.value)}
                placeholder="Brief description of this category"
                maxLength={255}
                disabled={addingCategory}
              />
            </div>
          </div>
          <div className="form-actions">
            <button 
              onClick={handleCancelAddCategory}
              className="cancel-btn"
              disabled={addingCategory}
            >
              Cancel
            </button>
            <button 
              onClick={handleAddCategory}
              className="create-btn"
              disabled={addingCategory || !newCategoryName.trim()}
            >
              {addingCategory ? 'Creating...' : 'Create Category'}
            </button>
          </div>
        </div>
      )}

      {/* Filter Modal */}
      {showFilters && (
        <div className="filter-modal-overlay">
          <div className="filter-modal">
            <div className="filter-modal-header">
              <h3>Filter Transactions</h3>
              <button 
                onClick={() => setShowFilters(false)}
                className="close-modal-btn"
              >
                ×
              </button>
            </div>
            
            <div className="filter-modal-content">
              <div className="filter-section">
                <label>Filter by Category:</label>
                <select
                  value={tempFilters.category}
                  onChange={(e) => setTempFilters(prev => ({ ...prev, category: e.target.value }))}
                  className="filter-select"
                >
                  <option value="all">All Categories</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="filter-section">
                <label>Filter by Type:</label>
                <select
                  value={tempFilters.transactionType}
                  onChange={(e) => setTempFilters(prev => ({ ...prev, transactionType: e.target.value }))}
                  className="filter-select"
                >
                  <option value="all">All Types</option>
                  <option value="expense">Expenses Only</option>
                  <option value="income">Income Only</option>
                </select>
              </div>
            </div>
            
            <div className="filter-modal-actions">
              <button 
                onClick={() => {
                  setTempFilters({ category: 'all', transactionType: 'all' });
                }}
                className="reset-filters-btn"
              >
                Reset All
              </button>
              <button 
                onClick={() => {
                  setFilters(tempFilters); // Apply temp filters to main filters
                  setCurrentPage(0);
                  setTransactions([]);
                  setShowFilters(false);
                  // The useEffect will trigger loadTransactions when filters change
                }}
                className="apply-filters-btn"
              >
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSV Upload Modal */}
      {showCSVUpload && (
        <div className="csv-modal-overlay">
          <div className="csv-modal">
            <div className="csv-modal-header">
              <h3>Import Transactions</h3>
              <button 
                onClick={() => setShowCSVUpload(false)}
                className="close-modal-btn"
              >
                ×
              </button>
            </div>
            <div className="csv-modal-content">
              <CSVUpload onUploadSuccess={() => {
                setShowCSVUpload(false);
                loadTransactions(); // Refresh transactions after upload
              }} />
            </div>
          </div>
        </div>
      )}

      {/* File Info Modal */}
      {showFileInfo && selectedFileInfo && (
        <div className="file-info-modal-overlay">
          <div className="file-info-modal">
            <div className="file-info-modal-header">
              <h3>CSV Import Details</h3>
              <button 
                onClick={() => setShowFileInfo(false)}
                className="close-modal-btn"
              >
                ×
              </button>
            </div>
            <div className="file-info-modal-content">
              <div className="file-info-section">
                <div className="info-item">
                  <span className="info-label">Source File:</span>
                  <span className="info-value">📄 {selectedFileInfo.fileName}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Original Row:</span>
                  <span className="info-value">#{selectedFileInfo.row}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Import Date:</span>
                  <span className="info-value">{formatDate(selectedFileInfo.transaction.date)}</span>
                </div>
              </div>
              
              <div className="transaction-preview">
                <h4>Transaction Details</h4>
                <div className="transaction-card">
                  <div className="transaction-detail">
                    <span className="detail-label">Description:</span>
                    <span className="detail-value">{selectedFileInfo.transaction.description}</span>
                  </div>
                  <div className="transaction-detail">
                    <span className="detail-label">Amount:</span>
                    <span className={`detail-value ${selectedFileInfo.transaction.amount < 0 ? 'expense' : 'income'}`}>
                      {selectedFileInfo.transaction.amount < 0 ? '-' : '+'}$
                      {Math.abs(selectedFileInfo.transaction.amount).toFixed(2)}
                    </span>
                  </div>
                  <div className="transaction-detail">
                    <span className="detail-label">Category:</span>
                    <span className="detail-value category">
                      {getCategoryName(selectedFileInfo.transaction.category_id)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div className="file-info-modal-actions">
              <button 
                onClick={() => setShowFileInfo(false)}
                className="close-info-btn"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* Transactions Table */}
      <div className="transactions-table-container">
        <table className="transactions-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th>Category</th>
              <th>Amount</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map(transaction => {
              const amount = formatAmount(transaction.amount);
              return (
                <tr key={transaction.id}>
                  <td className="date-cell">
                    {formatDate(transaction.date)}
                  </td>
                  <td className="description-cell">
                    {transaction.description}
                  </td>
                  <td className="category-cell">
                    <span className="category-badge">
                      {getCategoryName(transaction.category_id)}
                    </span>
                  </td>
                  <td className={`amount-cell ${amount.isExpense ? 'expense' : 'income'}`}>
                    {amount.isExpense ? '-' : '+'}${amount.value}
                  </td>
                  <td className="source-cell">
                    {(() => {
                      const sourceInfo = formatSourceInfo(transaction);
                      return (
                        <div 
                          className={`source-badge ${sourceInfo.type} ${sourceInfo.type === 'csv' ? 'clickable' : ''}`}
                          onClick={() => {
                            if (sourceInfo.type === 'csv') {
                              setSelectedFileInfo({
                                fileName: sourceInfo.fileName,
                                row: sourceInfo.row,
                                transaction: transaction
                              });
                              setShowFileInfo(true);
                            }
                          }}
                          title={
                            sourceInfo.type === 'csv' 
                              ? 'Click to view file details' 
                              : 'Manually entered transaction'
                          }
                        >
                          <span className="source-icon">
                            {sourceInfo.type === 'csv' ? '📄' : '✏️'}
                          </span>
                          <span className="source-text">{sourceInfo.display}</span>
                          {sourceInfo.type === 'csv' && (
                            <span className="click-indicator">📋</span>
                          )}
                        </div>
                      );
                    })()}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Load More Button */}
      {filters.category === 'all' && filters.transactionType === 'all' && hasMore && !loading && (
        <div className="load-more-container">
          <button 
            onClick={loadMoreTransactions}
            className="load-more-btn"
          >
            <span>Load More Transactions</span>
            <span className="arrow">→</span>
          </button>
        </div>
      )}

      {loading && transactions.length > 0 && (
        <div className="loading-more">Loading more transactions...</div>
      )}

      {transactions.length === 0 && !loading && (
        <div className="no-transactions">
          <p>No transactions found.</p>
          <p>Add some transactions to get started!</p>
        </div>
      )}
    </div>
  );
};

export default Dashboard;