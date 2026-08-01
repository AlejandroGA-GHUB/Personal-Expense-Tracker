import React, { useState, useEffect } from 'react';
import './ManualTransactionForm.css';

const ManualTransactionForm = () => {
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    date: new Date().toISOString().slice(0, 16), // Current datetime in HTML format
    category_id: ''
  });
  
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  // Fetch categories on component mount
  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/categories/');
      if (response.ok) {
        const categoriesData = await response.json();
        setCategories(categoriesData);
        // Set default category to first one
        if (categoriesData.length > 0) {
          setFormData(prev => ({ ...prev, category_id: categoriesData[0].id }));
        }
      }
    } catch (error) {
      console.error('Error fetching categories:', error);
      setMessage({ text: 'Failed to load categories', type: 'error' });
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ text: '', type: '' });

    try {
      // Convert amount to number and make expenses negative (system only handles expenses)
      const amount = parseFloat(formData.amount);
      const finalAmount = -Math.abs(amount);

      const transactionData = {
        description: formData.description,
        amount: finalAmount,
        date: formData.date,
        category_id: parseInt(formData.category_id)
      };

      const response = await fetch('http://localhost:8000/api/transactions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transactionData)
      });

      if (response.ok) {
        const createdTransaction = await response.json();
        setMessage({ 
          text: `✅ Transaction created successfully! ID: ${createdTransaction.id}`, 
          type: 'success' 
        });
        
        // Reset form
        setFormData({
          description: '',
          amount: '',
          date: new Date().toISOString().slice(0, 16),
          category_id: categories.length > 0 ? categories[0].id : ''
        });
        
        
      } else {
        const errorData = await response.json();
        setMessage({ 
          text: `❌ Error: ${errorData.detail || 'Failed to create transaction'}`, 
          type: 'error' 
        });
      }
    } catch (error) {
      console.error('Error creating transaction:', error);
      setMessage({ 
        text: '❌ Network error. Please check if the backend is running.', 
        type: 'error' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="manual-transaction-form">
      <h2>💰 Add Manual Transaction</h2>
      
      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="description">Description:</label>
          <input
            type="text"
            id="description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            placeholder="e.g., Coffee at Starbucks"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="amount">Amount:</label>
          <input
            type="number"
            id="amount"
            name="amount"
            value={formData.amount}
            onChange={handleInputChange}
            placeholder="25.50"
            step="0.01"
            min="0"
            required
          />
        </div>

        {/* Transaction type removed — system records expenses only */}

        <div className="form-group">
          <label htmlFor="date">Date & Time:</label>
          <input
            type="datetime-local"
            id="date"
            name="date"
            value={formData.date}
            onChange={handleInputChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="category_id">Category:</label>
          <select
            id="category_id"
            name="category_id"
            value={formData.category_id}
            onChange={handleInputChange}
            required
          >
            {categories.map(category => (
              <option key={category.id} value={category.id}>
                {category.icon} {category.name}
              </option>
            ))}
          </select>
        </div>

        <button type="submit" disabled={loading} className="submit-btn">
          {loading ? '⏳ Creating...' : '✅ Add Transaction'}
        </button>
      </form>
    </div>
  );
};

export default ManualTransactionForm;