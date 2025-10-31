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
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);
  const [filters, setFilters] = useState({
    categories: [], // Array for multiple selection
    transactionType: 'all'
  });
  const [tempFilters, setTempFilters] = useState({
    categories: [], // Array for multiple selection
    transactionType: 'all'
  });
  const [showCSVUpload, setShowCSVUpload] = useState(false);
  const [showFileInfo, setShowFileInfo] = useState(false);
  const [selectedFileInfo, setSelectedFileInfo] = useState(null);
  const [editingTransactionId, setEditingTransactionId] = useState(null);
  const [editFormData, setEditFormData] = useState({
    description: '',
    amount: '',
    date: '',
    category_id: ''
  });
  const [updatingTransaction, setUpdatingTransaction] = useState(false);
  const [sortBy, setSortBy] = useState('date-desc'); // 'date-desc', 'date-asc', 'added-desc', 'added-asc'
  
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
      
      // Check what filters are active
      const hasCategories = filters.categories.length > 0;
      const hasType = filters.transactionType !== 'all';
      
      if (hasCategories || hasType) {
        // Use filter endpoint for any combination of filters
        url = `http://localhost:8000/api/transactions/filter?`;
        
        // Add category_ids (multiple)
        if (hasCategories) {
          filters.categories.forEach(catId => {
            url += `category_ids=${catId}&`;
          });
        }
        
        // Add transaction_type
        if (hasType) {
          const typeParam = filters.transactionType === 'expense' ? 'Expense' : 'Income';
          url += `transaction_type=${typeParam}&`;
        }
        
        // Remove trailing & or ?
        url = url.replace(/[&?]$/, '');
      } else {
        // No filters: use main endpoint with pagination
        url = `http://localhost:8000/api/transactions/?skip=${skip}&limit=${TRANSACTIONS_PER_PAGE}`;
      }
      
      const response = await fetch(url);
      
      if (response.ok) {
        const data = await response.json();
        
        if (currentPage === 0) {
          setTransactions(data);
        } else {
          setTransactions(prev => [...prev, ...data]);
        }
        
        // Only show "Load More" for unfiltered results (which use pagination)
        setHasMore(!hasCategories && !hasType && data.length === TRANSACTIONS_PER_PAGE);
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
    // Only allow "Load More" when no filters are applied (only unfiltered results use pagination)
    if (filters.category === 'all' && filters.transactionType === 'all' && hasMore) {
      setCurrentPage(prev => prev + 1);
    }
  };

  const resetFilters = () => {
    setFilters({ categories: [], transactionType: 'all' });
    setCurrentPage(0);
    setTransactions([]);
  };

  const getActiveFiltersCount = () => {
    let count = 0;
    if (filters.categories.length > 0) count += filters.categories.length;
    if (filters.transactionType !== 'all') count++;
    return count;
  };

  const getFilterSummary = () => {
    const parts = [];
    if (filters.categories.length > 0) {
      const categoryNames = filters.categories.map(catId => getCategoryName(catId)).join(', ');
      parts.push(`Categories: ${categoryNames}`);
    }
    if (filters.transactionType !== 'all') {
      parts.push(`Type: ${filters.transactionType === 'expense' ? 'Expenses' : 'Income'}`);
    }
    return parts.length > 0 ? parts.join(' | ') : 'All Transactions';
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

  const getSortedTransactions = () => {
    const sorted = [...transactions];
    
    switch (sortBy) {
      case 'date-desc':
        // Newest transaction date first
        return sorted.sort((a, b) => new Date(b.date) - new Date(a.date));
      case 'date-asc':
        // Oldest transaction date first
        return sorted.sort((a, b) => new Date(a.date) - new Date(b.date));
      case 'added-desc':
        // Most recently added first (newest created_at or highest ID)
        return sorted.sort((a, b) => {
          if (a.created_at && b.created_at) {
            return new Date(b.created_at) - new Date(a.created_at);
          }
          // Fallback to ID if created_at not available
          return b.id - a.id;
        });
      case 'added-asc':
        // Oldest added first (oldest created_at or lowest ID)
        return sorted.sort((a, b) => {
          if (a.created_at && b.created_at) {
            return new Date(a.created_at) - new Date(b.created_at);
          }
          // Fallback to ID if created_at not available
          return a.id - b.id;
        });
      default:
        return sorted;
    }
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

  const handleEditTransaction = (transaction) => {
    setEditingTransactionId(transaction.id);
    setEditFormData({
      description: transaction.description,
      amount: Math.abs(transaction.amount).toString(),
      date: new Date(transaction.date).toISOString().slice(0, 16),
      category_id: transaction.category_id,
      isExpense: transaction.amount < 0
    });
  };

  const handleCancelEdit = () => {
    setEditingTransactionId(null);
    setEditFormData({
      description: '',
      amount: '',
      date: '',
      category_id: ''
    });
  };

  const handleUpdateTransaction = async (transactionId) => {
    setUpdatingTransaction(true);
    setError('');

    try {
      const finalAmount = editFormData.isExpense 
        ? -Math.abs(parseFloat(editFormData.amount))
        : Math.abs(parseFloat(editFormData.amount));

      const response = await fetch(`http://localhost:8000/api/transactions/${transactionId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: editFormData.description,
          amount: finalAmount,
          date: editFormData.date,
          category_id: parseInt(editFormData.category_id)
        })
      });

      if (response.ok) {
        const updatedTransaction = await response.json();
        // Update the transaction in the local state
        setTransactions(prev => 
          prev.map(t => t.id === transactionId ? updatedTransaction : t)
        );
        handleCancelEdit();
      } else {
        setError('Failed to update transaction');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Error updating transaction:', err);
    } finally {
      setUpdatingTransaction(false);
    }
  };

  if (loading && transactions.length === 0) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading transactions...</div>
      </div>
    );
  }

  return (
    <>
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
          {/* Sort Dropdown */}
          <div className="sort-control">
            <label htmlFor="sort-select" className="sort-label">Sort by:</label>
            <select 
              id="sort-select"
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              className="sort-select"
            >
              <option value="date-desc">📅 Transaction Date — Newest First</option>
              <option value="date-asc">📅 Transaction Date — Oldest First</option>
              <option value="added-desc">⬆️ Recently Added</option>
              <option value="added-asc">⬇️ First Added</option>
            </select>
          </div>

          <button 
            onClick={() => {
              setTempFilters(filters); // Initialize temp filters with current filters
              setShowFilters(true);
              setShowAddCategory(false); // Close category form
              setShowCSVUpload(false); // Close CSV upload
            }}
            className="filter-btn"
          >
            <span>🔍 Filter</span>
            {getActiveFiltersCount() > 0 && (
              <span className="filter-badge">{getActiveFiltersCount()}</span>
            )}
          </button>
          
          <button 
            onClick={() => {
              setShowAddCategory(true);
              setShowFilters(false); // Close filter form
              setShowCSVUpload(false); // Close CSV upload
            }}
            className="add-category-btn"
            disabled={showAddCategory}
          >
            + Add Category
          </button>

          <button 
            onClick={() => {
              setShowCSVUpload(true);
              setShowFilters(false); // Close filter form
              setShowAddCategory(false); // Close category form
            }}
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

      {/* Filter Form - Dropdown Style */}
      {showFilters && (
        <div className="filter-form">
          <div className="form-header">
            <h3>Filter Transactions</h3>
          </div>
          
          <div className="form-fields">
            <div className="field-group">
              <label>Filter by Category:</label>
              <div className="category-filter-wrapper">
                <select
                  className="category-select-display"
                  value=""
                  onClick={(e) => {
                    e.preventDefault();
                    setShowCategoryDropdown(!showCategoryDropdown);
                  }}
                  onMouseDown={(e) => e.preventDefault()}
                  readOnly
                >
                  <option value="">
                    {tempFilters.categories.length === 0 
                      ? 'All Categories' 
                      : `${tempFilters.categories.length} selected`}
                  </option>
                </select>
                
                {showCategoryDropdown && (
                  <div className="checkbox-dropdown">
                    {categories.map(category => (
                      <label key={category.id} className="checkbox-option">
                        <input
                          type="checkbox"
                          checked={tempFilters.categories.includes(category.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setTempFilters(prev => ({
                                ...prev,
                                categories: [...prev.categories, category.id]
                              }));
                            } else {
                              setTempFilters(prev => ({
                                ...prev,
                                categories: prev.categories.filter(id => id !== category.id)
                              }));
                            }
                          }}
                        />
                        {category.name}
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            <div className="field-group">
              <label htmlFor="filter-type">Filter by Type:</label>
              <select
                id="filter-type"
                value={tempFilters.transactionType}
                onChange={(e) => setTempFilters(prev => ({ ...prev, transactionType: e.target.value }))}
              >
                <option value="all">All Types</option>
                <option value="expense">Expenses Only</option>
                <option value="income">Income Only</option>
              </select>
            </div>
          </div>
          
          <div className="form-actions">
            <button 
              onClick={() => {
                setTempFilters({ categories: [], transactionType: 'all' });
                setShowCategoryDropdown(false);
                setShowFilters(false);
              }}
              className="reset-btn"
            >
              Cancel
            </button>
            <button 
              onClick={() => {
                setFilters(tempFilters);
                setCurrentPage(0);
                setTransactions([]);
                setShowCategoryDropdown(false);
                setShowFilters(false);
              }}
              className="apply-btn"
            >
              Apply Filters
            </button>
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
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {getSortedTransactions().map(transaction => {
              const amount = formatAmount(transaction.amount);
              const isEditing = editingTransactionId === transaction.id;
              
              return (
                <tr key={transaction.id} className={isEditing ? 'editing-row' : ''}>
                  <td className="date-cell">
                    {isEditing ? (
                      <div className="datetime-edit-group">
                        <input
                          type="date"
                          value={editFormData.date.split('T')[0]}
                          onChange={(e) => {
                            const time = editFormData.date.includes('T') ? editFormData.date.split('T')[1] : '00:00';
                            setEditFormData(prev => ({ ...prev, date: `${e.target.value}T${time}` }));
                          }}
                          className="edit-input date-only-input"
                        />
                        <input
                          type="time"
                          value={editFormData.date.includes('T') ? editFormData.date.split('T')[1] : '00:00'}
                          onChange={(e) => {
                            const date = editFormData.date.split('T')[0];
                            setEditFormData(prev => ({ ...prev, date: `${date}T${e.target.value}` }));
                          }}
                          className="edit-input time-input"
                        />
                      </div>
                    ) : (
                      formatDate(transaction.date)
                    )}
                  </td>
                  <td className="description-cell">
                    {isEditing ? (
                      <input
                        type="text"
                        value={editFormData.description}
                        onChange={(e) => setEditFormData(prev => ({ ...prev, description: e.target.value }))}
                        className="edit-input"
                        placeholder="Description"
                      />
                    ) : (
                      transaction.description
                    )}
                  </td>
                  <td className="category-cell">
                    {isEditing ? (
                      <select
                        value={editFormData.category_id}
                        onChange={(e) => setEditFormData(prev => ({ ...prev, category_id: e.target.value }))}
                        className="edit-select"
                      >
                        {categories.map(category => (
                          <option key={category.id} value={category.id}>
                            {category.name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className="category-badge">
                        {getCategoryName(transaction.category_id)}
                      </span>
                    )}
                  </td>
                  <td className={`amount-cell ${amount.isExpense ? 'expense' : 'income'}`}>
                    {isEditing ? (
                      <div className="amount-edit-group">
                        <select
                          value={editFormData.isExpense ? 'expense' : 'income'}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, isExpense: e.target.value === 'expense' }))}
                          className="edit-select type-select"
                        >
                          <option value="expense">Expense</option>
                          <option value="income">Income</option>
                        </select>
                        <input
                          type="number"
                          step="0.01"
                          value={editFormData.amount}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, amount: e.target.value }))}
                          className="edit-input amount-input"
                          placeholder="0.00"
                        />
                      </div>
                    ) : (
                      `${amount.isExpense ? '-' : '+'}$${amount.value}`
                    )}
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
                  <td className="actions-cell">
                    {isEditing ? (
                      <div className="action-buttons">
                        <button
                          onClick={() => handleUpdateTransaction(transaction.id)}
                          disabled={updatingTransaction}
                          className="save-btn"
                          title="Save changes"
                        >
                          ✓
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          disabled={updatingTransaction}
                          className="cancel-btn"
                          title="Cancel"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleEditTransaction(transaction)}
                        className="edit-btn"
                        title="Edit transaction"
                      >
                        ✏️
                      </button>
                    )}
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

      {/* CSV Upload Modal - Outside dashboard container */}
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

      {/* File Info Modal - Outside dashboard container */}
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
    </>
  );
};

export default Dashboard;