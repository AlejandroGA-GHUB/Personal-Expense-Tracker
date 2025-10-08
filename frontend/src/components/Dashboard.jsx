import { useState, useEffect } from 'react';
import './Dashboard.css';

const Dashboard = () => {
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [currentPage, setCurrentPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  
  const TRANSACTIONS_PER_PAGE = 100;

  // Load categories on component mount
  useEffect(() => {
    loadCategories();
  }, []);

  // Load transactions when category or page changes
  useEffect(() => {
    loadTransactions();
  }, [selectedCategory, currentPage]);

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
      
      if (selectedCategory === 'all') {
        url = `http://localhost:8000/api/transactions/?skip=${skip}&limit=${TRANSACTIONS_PER_PAGE}`;
      } else {
        // For category filtering, we'll load all transactions for that category for now
        // In a production app, you'd want to add pagination to the category endpoint too
        url = `http://localhost:8000/api/transactions/category/${selectedCategory}`;
      }
      
      const response = await fetch(url);
      
      if (response.ok) {
        const data = await response.json();
        
        if (currentPage === 0) {
          setTransactions(data);
        } else {
          setTransactions(prev => [...prev, ...data]);
        }
        
        // Check if there are more transactions
        setHasMore(data.length === TRANSACTIONS_PER_PAGE);
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

  const handleCategoryChange = (categoryId) => {
    setSelectedCategory(categoryId);
    setCurrentPage(0);
    setTransactions([]);
  };

  const loadMoreTransactions = () => {
    if (selectedCategory === 'all' && hasMore) {
      setCurrentPage(prev => prev + 1);
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

      {/* Category Filter */}
      <div className="category-filter">
        <label htmlFor="category-select">Filter by Category:</label>
        <select
          id="category-select"
          value={selectedCategory}
          onChange={(e) => handleCategoryChange(e.target.value)}
          className="category-select"
        >
          <option value="all">All Categories</option>
          {categories.map(category => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </div>

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
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Load More Button */}
      {selectedCategory === 'all' && hasMore && !loading && (
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