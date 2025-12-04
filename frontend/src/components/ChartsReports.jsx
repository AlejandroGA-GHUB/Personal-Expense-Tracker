import { useState, useEffect } from 'react';
import './ChartsReports.css';

const ChartsReports = () => {
  const [activeTab, setActiveTab] = useState('reports');
  const [dailySpending, setDailySpending] = useState(0);
  const [totalExpenses, setTotalExpenses] = useState(0);
  const [loading, setLoading] = useState(true);
  
  // Monthly & Yearly Reports
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1); // 1-12
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [monthlyData, setMonthlyData] = useState({ spending: 0, category: null });
  const [yearlyData, setYearlyData] = useState({ spendingPerMonth: [], category: null });
  const [monthlyLoading, setMonthlyLoading] = useState(false);
  const [yearlyLoading, setYearlyLoading] = useState(false);
  const [categoryBreakdown, setCategoryBreakdown] = useState([]);
  const [categoryLoading, setCategoryLoading] = useState(true);

  useEffect(() => {
    const fetchDailySpending = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/reports/daily_and_total_expenses');
        if (response.ok) {
          const data = await response.json();
          // data is a tuple: [averageDailySpending, totalExpenses]
          setDailySpending(data[0]);
          setTotalExpenses(data[1]);
        }
      } catch (err) {
        console.error('Error fetching daily spending:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDailySpending();
  }, []);

  // Fetch monthly spending
  useEffect(() => {
    const fetchMonthlySpending = async () => {
      setMonthlyLoading(true);
      try {
        const response = await fetch(
          `http://localhost:8000/api/reports/monthly?month=${selectedMonth}&year=${selectedYear}`
        );
        if (response.ok) {
          const data = await response.json();
          // data is tuple: [spending, [categoryName, categorySpending]]
          setMonthlyData({
            spending: data[0],
            category: (data[1] && data[1].length > 0) ? { name: data[1][0], amount: data[1][1] } : null
          });
        }
      } catch (err) {
        console.error('Error fetching monthly spending:', err);
      } finally {
        setMonthlyLoading(false);
      }
    };

    fetchMonthlySpending();
  }, [selectedMonth, selectedYear]);

  // Fetch yearly spending
  useEffect(() => {
    const fetchYearlySpending = async () => {
      setYearlyLoading(true);
      try {
        const response = await fetch(
          `http://localhost:8000/api/reports/yearly?year=${selectedYear}`
        );
        if (response.ok) {
          const data = await response.json();
          // data is tuple: [spendingPerMonth[], [categoryName, categorySpending]]
          setYearlyData({
            spendingPerMonth: data[0],
            category: (data[1] && data[1].length > 0) ? { name: data[1][0], amount: data[1][1] } : null
          });
        }
      } catch (err) {
        console.error('Error fetching yearly spending:', err);
      } finally {
        setYearlyLoading(false);
      }
    };

    fetchYearlySpending();
  }, [selectedYear]);

  // Fetch category breakdown
  useEffect(() => {
    const fetchCategoryBreakdown = async () => {
      setCategoryLoading(true);
      try {
        const response = await fetch('http://localhost:8000/api/reports/category_spending');
        if (response.ok) {
          const data = await response.json();
          // data is list of tuples: [["Food & Dining", 1234.56], ["Transportation", 567.89], ...]
          setCategoryBreakdown(data);
        }
      } catch (err) {
        console.error('Error fetching category breakdown:', err);
      } finally {
        setCategoryLoading(false);
      }
    };

    fetchCategoryBreakdown();
  }, []);

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  return (
    <div className="charts-reports-container">
      <div className="charts-reports-header">
        <h2>Analytics & Reports</h2>
        <div className="tab-navigation">
          <button 
            onClick={() => setActiveTab('reports')}
            className={activeTab === 'reports' ? 'tab-button active' : 'tab-button'}
          >
            📈 Reports
          </button>
          <button 
            onClick={() => setActiveTab('charts')}
            className={activeTab === 'charts' ? 'tab-button active' : 'tab-button'}
          >
            📊 Charts
          </button>
        </div>
      </div>

      <div className="charts-reports-content">
        {activeTab === 'charts' && (
          <div className="charts-section">
            <h3>Visualize Your Spending</h3>
            
            {/* Category Breakdown Section */}
            <div className="chart-card">
              <h4>Spending by Category</h4>
              <div className="chart-placeholder">
                <p>📊 Bar/Pie chart showing aggregate spending by category</p>
                <small>Coming soon: Interactive category breakdown</small>
              </div>
            </div>

            {/* Time-based Charts Section */}
            <div className="chart-card">
              <h4>Spending Over Time</h4>
              <div className="time-filter">
                <button className="filter-btn active">Monthly</button>
                <button className="filter-btn">Yearly</button>
                <button className="filter-btn">Custom Range</button>
              </div>
              <div className="chart-placeholder">
                <p>📈 Line/Bar chart showing spending trends</p>
                <small>Coming soon: Monthly and yearly trend analysis</small>
              </div>
            </div>

            {/* Income vs Expenses */}
            <div className="chart-card">
              <h4>Income vs Expenses</h4>
              <div className="chart-placeholder">
                <p>💰 Comparison chart of income and expenses</p>
                <small>Coming soon: Cash flow visualization</small>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="reports-section">
            <h3>Detailed Financial Reports</h3>

            {/* Summary Statistics */}
            <div className="report-card">
              <h4>Summary Statistics</h4>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-label">Total Expenses</span>
                  <span className="stat-value">
                    {loading ? '...' : `$${totalExpenses.toFixed(2)}`}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Average Daily Spending</span>
                  <span className="stat-value">
                    {loading ? '...' : `$${dailySpending.toFixed(2)}`}
                  </span>
                </div>
              </div>
            </div>

            {/* Category Breakdown Report */}
            <div className="report-card">
              <h4>Category Breakdown</h4>
              {categoryLoading ? (
                <p>Loading...</p>
              ) : categoryBreakdown.length > 0 ? (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
                        <th style={{ padding: '12px' }}>Category</th>
                        <th style={{ padding: '12px', textAlign: 'right' }}>Total Spending</th>
                        <th style={{ padding: '12px', textAlign: 'right' }}>Percentage</th>
                      </tr>
                    </thead>
                    <tbody>
                      {categoryBreakdown.map(([category, amount], idx) => {
                        const total = categoryBreakdown.reduce((sum, [_, amt]) => sum + amt, 0);
                        const percentage = ((amount / total) * 100).toFixed(1);
                        return (
                          <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                            <td style={{ padding: '12px', fontWeight: '500' }}>{category}</td>
                            <td style={{ padding: '12px', textAlign: 'right' }}>${amount.toFixed(2)}</td>
                            <td style={{ padding: '12px', textAlign: 'right' }}>{percentage}%</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p>No category data available</p>
              )}
            </div>

            {/* Monthly & Yearly Reports */}
            <div className="report-card">
              <h4>Monthly & Yearly Reports</h4>
              
              {/* Year/Month Selector */}
              <div className="date-selector" style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
                <select 
                  value={selectedYear} 
                  onChange={(e) => setSelectedYear(Number(e.target.value))}
                  style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                >
                  {[2023, 2024, 2025, 2026].map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
                <select 
                  value={selectedMonth} 
                  onChange={(e) => setSelectedMonth(Number(e.target.value))}
                  style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                >
                  {monthNames.map((month, idx) => (
                    <option key={idx} value={idx + 1}>{month}</option>
                  ))}
                </select>
              </div>

              {/* Monthly Report */}
              <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                <h5 style={{ marginTop: 0 }}>📅 {monthNames[selectedMonth - 1]} {selectedYear}</h5>
                {monthlyLoading ? (
                  <p>Loading...</p>
                ) : (
                  <>
                    <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '10px 0' }}>
                      ${monthlyData.spending.toFixed(2)}
                    </p>
                    {monthlyData.category && (
                      <p style={{ color: '#666' }}>
                        Highest Spending: <strong>{monthlyData.category.name}</strong> (${monthlyData.category.amount.toFixed(2)})
                      </p>
                    )}
                  </>
                )}
              </div>

              {/* Yearly Report */}
              <div style={{ padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                <h5 style={{ marginTop: 0 }}>📊 Year {selectedYear} Overview</h5>
                {yearlyLoading ? (
                  <p>Loading...</p>
                ) : (
                  <>
                    {yearlyData.spendingPerMonth.length > 0 ? (
                      <>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '15px' }}>
                          {yearlyData.spendingPerMonth.map((amount, idx) => (
                            <div key={idx} style={{ padding: '10px', backgroundColor: 'white', borderRadius: '4px', textAlign: 'center' }}>
                              <div style={{ fontSize: '12px', color: '#666' }}>{monthNames[idx]}</div>
                              <div style={{ fontWeight: 'bold' }}>${amount.toFixed(2)}</div>
                            </div>
                          ))}
                        </div>
                        {yearlyData.category && (
                          <p style={{ color: '#666', marginBottom: 0 }}>
                            Year's Highest Spending: <strong>{yearlyData.category.name}</strong> (${yearlyData.category.amount.toFixed(2)})
                          </p>
                        )}
                      </>
                    ) : (
                      <p>No transactions for {selectedYear}</p>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Export Options */}
            <div className="report-card">
              <h4>Export Reports</h4>
              <div className="export-options">
                <button className="export-btn" disabled>
                  📄 Export as PDF
                </button>
                <button className="export-btn" disabled>
                  📊 Export as CSV
                </button>
                <button className="export-btn" disabled>
                  📧 Email Report
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChartsReports;
