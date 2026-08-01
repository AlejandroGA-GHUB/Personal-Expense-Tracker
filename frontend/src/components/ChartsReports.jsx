import { useState, useEffect, useRef, useMemo } from 'react';
import './ChartsReports.css';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend } from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend);

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
  
  // Chart state
  const [chartType, setChartType] = useState('pie'); // 'pie' or 'bar'
  const [chartTimeRange, setChartTimeRange] = useState('yearly'); // Start with 'yearly' to show current year
  const [chartMonth, setChartMonth] = useState(new Date().getMonth() + 1);
  const [chartYear, setChartYear] = useState(new Date().getFullYear());
  const [chartData, setChartData] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);
  
  // Trend chart state
  const [trendYear, setTrendYear] = useState(new Date().getFullYear());
  const [yearlyTrendData, setYearlyTrendData] = useState([]);
  const [yearOverYearData, setYearOverYearData] = useState([]);
  const [trendLoading, setTrendLoading] = useState(false);
  const [monthlyTrendChartType, setMonthlyTrendChartType] = useState('bar'); // 'bar' or 'line'
  const [yearlyTrendChartType, setYearlyTrendChartType] = useState('bar'); // 'bar' or 'line'
  const [categoriesByMonthData, setCategoriesByMonthData] = useState({ labels: [], datasets: [] });
  const [categoriesByMonthLoading, setCategoriesByMonthLoading] = useState(false);
  // Category month-to-month comparison
  // Category exclusion for charts (resets on page navigation)
  const [excludedCategories, setExcludedCategories] = useState([]);
  
  // Year-to-year comparison state
  const [comparisonCategory, setComparisonCategory] = useState('');
  const [comparisonYearA, setComparisonYearA] = useState(new Date().getFullYear());
  const [comparisonYearB, setComparisonYearB] = useState(new Date().getFullYear() - 1);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonData, setComparisonData] = useState({ labels: [], datasets: [] });
  // UI transition state for smooth chart swaps
  const [chartVisible, setChartVisible] = useState(true);
  const [monthlyTrendVisible, setMonthlyTrendVisible] = useState(true);
  const [showLoadingMsg, setShowLoadingMsg] = useState(false);
  const [showSkeleton, setShowSkeleton] = useState(false);
  // Refs for pre-mounted charts
  const pieRef = useRef(null);
  const barRef = useRef(null);
  const lineRef = useRef(null);
  const monthlyTrendBarRef = useRef(null);
  const monthlyTrendLineRef = useRef(null);
  const yearOverYearRef = useRef(null);
  const comparisonRef = useRef(null);
  const [disableAnim, setDisableAnim] = useState(false);
  
  // Generate stable keys for charts to prevent artifact flashing
  const categoryChartKey = `category-${chartType}-${chartTimeRange}-${chartYear}-${chartMonth}-${excludedCategories.sort().join(',')}`;
  const trendChartKey = `spending-trend-${trendYear}-${monthlyTrendChartType}`;
  const yoyChartKey = `spending-yoy-${yearOverYearData.length}`;
  const comparisonChartKey = `category-comp-${comparisonCategory}-${comparisonYearA}-${comparisonYearB}`;

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

  // Fetch chart data based on time range
  useEffect(() => {
    const fetchChartData = async () => {
      setChartLoading(true);
      try {
        let url;
        if (chartTimeRange === 'monthly') {
          url = `http://localhost:8000/api/charts/category_spending_monthly?month=${chartMonth}&year=${chartYear}`;
        } else {
          url = `http://localhost:8000/api/charts/category_spending_yearly?year=${chartYear}`;
        }
        
        const response = await fetch(url);
        if (response.ok) {
          const data = await response.json();
          // data is list of tuples: [["Food & Dining", 234.56], ...]
          setChartData(data);
        }
      } catch (err) {
        console.error('Error fetching chart data:', err);
      } finally {
        setChartLoading(false);
      }
    };

    fetchChartData();
  }, [chartTimeRange, chartMonth, chartYear, excludedCategories]);

  // Fetch trend data
  useEffect(() => {
    const fetchTrendData = async () => {
      setTrendLoading(true);
      try {
        // Fetch monthly trend for selected year
        const monthlyResponse = await fetch(`http://localhost:8000/api/reports/yearly?year=${trendYear}`);
        if (monthlyResponse.ok) {
          const data = await monthlyResponse.json();
          setYearlyTrendData(data[0]); // spending_per_month array
        }

        // Fetch year-over-year data
        const yearlyResponse = await fetch('http://localhost:8000/api/charts/spending_by_year');
        if (yearlyResponse.ok) {
          const data = await yearlyResponse.json();
          setYearOverYearData(data); // [(2023, 15234.56), ...]
        }
      } catch (err) {
        console.error('Error fetching trend data:', err);
      } finally {
        setTrendLoading(false);
      }
    };

    fetchTrendData();
  }, [trendYear]);

  // Fetch per-category monthly series for the selected trend year
  useEffect(() => {
    // only fetch when the category-line (multi-line) view is active
    if (chartType !== 'line') return;

    const fetchCategoriesByMonth = async () => {
      setCategoriesByMonthLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/charts/categories_by_month?year=${chartYear}`);
        if (!res.ok) {
          setCategoriesByMonthData({ labels: [], datasets: [] });
          return;
        }
        const data = await res.json();

        // Fetch yearly totals to match pie ordering (API returns categories ordered by total desc)
        const yearlyRes = await fetch(`http://localhost:8000/api/charts/category_spending_yearly?year=${chartYear}`);
        const yearlyList = yearlyRes.ok ? await yearlyRes.json() : [];

        // categoriesMap from API data
        const categories = Object.keys(data || {});
        if (categories.length === 0) {
          setCategoriesByMonthData({ labels: [], datasets: [] });
          return;
        }
        // Determine ordering to match pie: use yearlyList order filtered to categories present
        const orderedNames = yearlyList.map(([name]) => name).filter(n => categories.includes(n));

        // For any categories not present in yearlyList, append them after
        const remaining = categories.filter(n => !orderedNames.includes(n));
        const finalOrder = [...orderedNames, ...remaining];

        const colors = generateColors(finalOrder.length);
        const rawDatasets = finalOrder.map((name, i) => {
          const vals = (data[name] || []).map(v => Number(v) || 0);
          return {
            label: name,
            data: vals,
            borderColor: colors[i],
            backgroundColor: colors[i],
            fill: false,
            tension: 0.3,
            pointRadius: 0,
            pointHoverRadius: 6,
            pointBackgroundColor: colors[i],
            borderWidth: 3
          };
        });

        const datasets = rawDatasets
          .filter(ds => (ds.data || []).some(v => Number(v) > 0))
          .filter(ds => !excludedCategories.includes(ds.label));

        setCategoriesByMonthData({ labels: monthNames, datasets });
      } catch (err) {
        console.error('Error fetching categories by month:', err);
        setCategoriesByMonthData({ labels: [], datasets: [] });
      } finally {
        setCategoriesByMonthLoading(false);
      }
    };

    fetchCategoriesByMonth();
  }, [chartType, chartYear, excludedCategories]);

  // Fetch year-to-year comparison for a single category across all 12 months
  useEffect(() => {
    const fetchComparison = async () => {
      if (!comparisonCategory) {
        setComparisonData({ labels: [], datasets: [] });
        return;
      }

      setComparisonLoading(true);
      try {
        // Use the new dedicated endpoint
        const years = `${comparisonYearA},${comparisonYearB}`;
        const res = await fetch(
          `http://localhost:8000/api/charts/category_year_comparison?category=${encodeURIComponent(comparisonCategory)}&years=${years}`
        );
        
        if (!res.ok) {
          setComparisonData({ labels: [], datasets: [] });
          return;
        }

        const data = await res.json();
        // data format: {"2024": [12.34, 23.45, ...], "2025": [45.67, ...]}
        
        const valuesA = data[String(comparisonYearA)] || Array(12).fill(0);
        const valuesB = data[String(comparisonYearB)] || Array(12).fill(0);

        const colorA = '#2196F3'; // blue
        const colorB = '#FF9800'; // orange

        const datasetA = {
          label: `${comparisonYearA}`,
          data: valuesA,
          backgroundColor: colorA,
          borderColor: '#1976D2',
          borderWidth: 1
        };

        const datasetB = {
          label: `${comparisonYearB}`,
          data: valuesB,
          backgroundColor: colorB,
          borderColor: '#E65100',
          borderWidth: 1
        };

        setComparisonData({ labels: monthNames, datasets: [datasetA, datasetB] });
      } catch (err) {
        console.error('Error fetching year-to-year comparison:', err);
        setComparisonData({ labels: [], datasets: [] });
      } finally {
        setComparisonLoading(false);
      }
    };

    fetchComparison();
  }, [comparisonCategory, comparisonYearA, comparisonYearB]);

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  // Generate distinct colors for categories
  const generateColors = (count) => {
    const colors = [];
    for (let i = 0; i < count; i++) {
      const hue = (i * 360 / count) % 360;
      colors.push(`hsl(${hue}, 70%, 60%)`);
    }
    return colors;
  };

  // Trigger fade when major chart inputs change (type, range, year/month, exclusions, comparison selection)
  useEffect(() => {
    // Disable animations first, then hide, then show after data loads
    setDisableAnim(true);
    setChartVisible(false);
    const t = setTimeout(() => {
      setChartVisible(true);
      // Re-enable animations after charts are visible
      setTimeout(() => setDisableAnim(false), 100);
    }, 150);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartType, chartTimeRange, chartYear, chartMonth, excludedCategories.join(','), comparisonCategory, comparisonYearA, comparisonYearB]);

  // Separate transition for monthly trend chart only (not year-over-year which doesn't depend on trendYear)
  useEffect(() => {
    setShowSkeleton(true);
    setDisableAnim(true);
    setMonthlyTrendVisible(false);
    const t = setTimeout(() => {
      setShowSkeleton(false);
      setMonthlyTrendVisible(true);
      setTimeout(() => setDisableAnim(false), 100);
    }, 180);
    return () => clearTimeout(t);
  }, [trendYear, monthlyTrendChartType]);

  // Delayed loading message - only show if loading takes > 200ms
  useEffect(() => {
    if (chartLoading || categoriesByMonthLoading || comparisonLoading || trendLoading) {
      const timer = setTimeout(() => setShowLoadingMsg(true), 200);
      return () => clearTimeout(timer);
    } else {
      setShowLoadingMsg(false);
    }
  }, [chartLoading, categoriesByMonthLoading, comparisonLoading, trendLoading]);

  // Respect loading states: hide while any chart data is loading, show when done
  useEffect(() => {
    if (chartLoading || categoriesByMonthLoading || comparisonLoading) {
      setChartVisible(false);
    } else {
      const t = setTimeout(() => setChartVisible(true), 80);
      return () => clearTimeout(t);
    }
  }, [chartLoading, categoriesByMonthLoading, comparisonLoading]);

  // Precompute filtered chart data and data objects for each chart type
  const filteredChartData = useMemo(() => chartData.filter(([name]) => !excludedCategories.includes(name)), [chartData, excludedCategories]);

  const pieData = useMemo(() => ({
    labels: filteredChartData.map(([name]) => name),
    datasets: [{ data: filteredChartData.map(([_, amount]) => amount), backgroundColor: generateColors(filteredChartData.length), borderWidth: 1 }]
  }), [filteredChartData]);

  const barData = useMemo(() => ({
    labels: filteredChartData.map(([name]) => name),
    datasets: [{ label: 'Spending', data: filteredChartData.map(([_, amount]) => amount), backgroundColor: '#36A2EB', borderColor: '#2196F3', borderWidth: 1 }]
  }), [filteredChartData]);

  const commonOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: true,
    animation: { duration: disableAnim ? 0 : 300 },
    plugins: { tooltip: { callbacks: { label: (ctx) => {
      const val = ctx.parsed?.y ?? ctx.parsed ?? 0; return `$${Number(val).toFixed(2)}`;
    } } } }
  }), [disableAnim]);

  // Precompute monthly trend data objects for pre-mounted charts
  const monthlyTrendBarData = useMemo(() => ({
    labels: monthNames,
    datasets: [{ label: `Spending in ${trendYear}`, data: yearlyTrendData, backgroundColor: '#2196F3', borderColor: '#1976D2', borderWidth: 1 }]
  }), [yearlyTrendData, trendYear]);

  const monthlyTrendLineData = useMemo(() => ({
    labels: monthNames,
    datasets: [{ label: `Spending in ${trendYear}`, data: yearlyTrendData, borderColor: '#2196F3', backgroundColor: 'rgba(33, 150, 243, 0.1)', tension: 0.4, fill: true }]
  }), [yearlyTrendData, trendYear]);

  const yearOverYearBarData = useMemo(() => ({
    labels: yearOverYearData.map(([year]) => year.toString()),
    datasets: [{ label: 'Total Spending', data: yearOverYearData.map(([_, amount]) => amount), backgroundColor: '#4CAF50', borderColor: '#388E3C', borderWidth: 1 }]
  }), [yearOverYearData]);

  // Update chart instances in-place when their data changes to avoid remounts
  useEffect(() => {
    try {
      if (pieRef.current && pieRef.current.update) pieRef.current.update();
    } catch (e) {}
  }, [pieData, disableAnim]);

  useEffect(() => {
    try {
      if (barRef.current && barRef.current.update) barRef.current.update();
    } catch (e) {}
  }, [barData, disableAnim]);

  useEffect(() => {
    try {
      if (lineRef.current && lineRef.current.update) lineRef.current.update();
    } catch (e) {}
  }, [categoriesByMonthData, disableAnim]);

  // Update monthly trend pre-mounted charts
  useEffect(() => {
    try {
      if (monthlyTrendBarRef.current && monthlyTrendBarRef.current.update) monthlyTrendBarRef.current.update();
    } catch (e) {}
  }, [monthlyTrendBarData, disableAnim]);

  useEffect(() => {
    try {
      if (monthlyTrendLineRef.current && monthlyTrendLineRef.current.update) monthlyTrendLineRef.current.update();
    } catch (e) {}
  }, [monthlyTrendLineData, disableAnim]);

  // Update year-over-year chart in-place
  useEffect(() => {
    try {
      if (yearOverYearRef.current && yearOverYearRef.current.update) yearOverYearRef.current.update();
    } catch (e) {}
  }, [yearOverYearBarData, disableAnim]);

  // Update comparison chart in-place
  useEffect(() => {
    try {
      if (comparisonRef.current && comparisonRef.current.update) comparisonRef.current.update();
    } catch (e) {}
  }, [comparisonData, disableAnim]);

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
            <div className="chart-card" style={{ minHeight: '360px' }}>
              <h4>Spending by Category</h4>
              
              {/* Chart Controls */}
              <div style={{ marginBottom: '20px', display: 'flex', gap: '15px', alignItems: 'center', flexWrap: 'wrap' }}>
                {/* Chart Type Toggle */}
                <div>
                  <label style={{ marginRight: '10px', fontWeight: '500' }}>Chart Type:</label>
                  <button 
                    onClick={() => setChartType('pie')} 
                    style={{ 
                      padding: '6px 12px', 
                      marginRight: '5px',
                      backgroundColor: chartType === 'pie' ? '#4CAF50' : '#f0f0f0',
                      color: chartType === 'pie' ? 'white' : 'black',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Pie
                  </button>
                  <button 
                    onClick={() => setChartType('bar')} 
                    style={{ 
                      padding: '6px 12px',
                      backgroundColor: chartType === 'bar' ? '#4CAF50' : '#f0f0f0',
                      color: chartType === 'bar' ? 'white' : 'black',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Bar
                  </button>
                  <button 
                    onClick={() => { setChartType('line'); setChartTimeRange('yearly'); }} 
                    style={{ 
                      padding: '6px 12px',
                      marginLeft: '6px',
                      backgroundColor: chartType === 'line' ? '#4CAF50' : '#f0f0f0',
                      color: chartType === 'line' ? 'white' : 'black',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Line
                  </button>
                </div>

                {/* Time Range Toggle */}
                <div>
                  <label style={{ marginRight: '10px', fontWeight: '500' }}>Time Range:</label>
                  <button 
                    onClick={() => setChartTimeRange('monthly')} 
                    disabled={chartType === 'line'}
                    style={{ 
                      padding: '6px 12px', 
                      marginRight: '5px',
                      backgroundColor: chartTimeRange === 'monthly' && chartType !== 'line' ? '#2196F3' : '#f0f0f0',
                      color: chartTimeRange === 'monthly' && chartType !== 'line' ? 'white' : 'black',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      cursor: chartType === 'line' ? 'not-allowed' : 'pointer',
                      opacity: chartType === 'line' ? 0.6 : 1
                    }}
                  >
                    Monthly
                  </button>
                  <button 
                    onClick={() => setChartTimeRange('yearly')} 
                    style={{ 
                      padding: '6px 12px',
                      backgroundColor: chartTimeRange === 'yearly' ? '#2196F3' : '#f0f0f0',
                      color: chartTimeRange === 'yearly' ? 'white' : 'black',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Yearly
                  </button>
                </div>

                {/* Date Selectors */}
                {chartTimeRange === 'monthly' && (
                  <select 
                    value={chartMonth} 
                    onChange={(e) => setChartMonth(Number(e.target.value))}
                    style={{ padding: '6px 12px', borderRadius: '4px', border: '1px solid #ddd' }}
                  >
                    {monthNames.map((month, idx) => (
                      <option key={idx} value={idx + 1}>{month}</option>
                    ))}
                  </select>
                )}
                <select 
                  value={chartYear} 
                  onChange={(e) => setChartYear(Number(e.target.value))}
                  style={{ padding: '6px 12px', borderRadius: '4px', border: '1px solid #ddd' }}
                >
                  {[2023, 2024, 2025, 2026].map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>

              {/* Category Exclusion Toggles */}
              {(['pie', 'bar', 'line'].includes(chartType) && (chartData.length > 0 || (categoriesByMonthData.datasets || []).length > 0)) && (
                <div style={{ marginBottom: '20px', padding: '12px', background: '#f8f9fa', borderRadius: '6px' }}>
                  <div style={{ marginBottom: '8px', fontWeight: '500', fontSize: '13px', color: '#555' }}>Show/Hide Categories:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                    {(categoryBreakdown.length > 0 ? categoryBreakdown.map(([name]) => name) : (chartData.map(([name]) => name))).map(categoryName => (
                      <label key={categoryName} style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', padding: '4px 8px', background: '#fff', borderRadius: '4px', border: '1px solid #ddd' }}>
                        <input
                          type="checkbox"
                          checked={!excludedCategories.includes(categoryName)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setExcludedCategories(excludedCategories.filter(c => c !== categoryName));
                            } else {
                              setExcludedCategories([...excludedCategories, categoryName]);
                            }
                          }}
                          style={{ cursor: 'pointer' }}
                        />
                        <span style={{ fontSize: '13px' }}>{categoryName}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Chart Display */}
              <div className={`chart-transition-wrapper ${chartVisible ? 'chart-transition-visible' : 'chart-transition-hidden'}`}>
                <div style={{ maxWidth: '900px', margin: '0 auto', padding: '10px', minHeight: '350px' }}>
                  {chartLoading ? (
                    showLoadingMsg && (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px', color: '#666' }}>
                        <p>Loading chart...</p>
                      </div>
                    )
                  ) : filteredChartData.length === 0 && chartType !== 'line' ? (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px', color: '#666' }}>
                      <p>All categories are excluded</p>
                    </div>
                  ) : (
                    <>
                      {chartType === 'pie' && (
                        <Pie key={categoryChartKey} data={pieData} options={{ ...commonOptions, plugins: { ...commonOptions.plugins, legend: { position: 'bottom' }, tooltip: commonOptions.plugins.tooltip } }} />
                      )}
                      {chartType === 'bar' && (
                        <Bar key={categoryChartKey} data={barData} options={{ ...commonOptions, plugins: { ...commonOptions.plugins, legend: { display: false }, tooltip: commonOptions.plugins.tooltip }, scales: { y: { beginAtZero: true, ticks: { callback: v => `$${v}` } } } }} />
                      )}
                      {chartType === 'line' && (
                        categoriesByMonthLoading ? (
                          showLoadingMsg && (
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px', color: '#666' }}>
                              <p>Loading category series...</p>
                            </div>
                          )
                        ) : (categoriesByMonthData && categoriesByMonthData.datasets && categoriesByMonthData.datasets.length > 0) ? (
                          <Line key={categoryChartKey} data={categoriesByMonthData} options={{
                            ...commonOptions,
                            plugins: { ...commonOptions.plugins, legend: { position: 'bottom', labels: { usePointStyle: true, pointStyle: 'rect', boxWidth: 26, boxHeight: 12, padding: 14, font: { size: 13 }, color: '#666' } }, tooltip: { callbacks: { label: (context) => `${context.dataset.label}: $${(context.parsed?.y ?? context.parsed)?.toFixed(2)}` } } },
                            scales: { y: { beginAtZero: true, ticks: { callback: v => `$${v}` } } }
                          }} />
                        ) : (
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px', color: '#666' }}>
                            <p>No category series available for {chartYear}</p>
                          </div>
                        )
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Time-based Charts Section */}
            <div className="chart-card" id="spending-over-time-section" style={{ position: 'relative', overflow: 'clip', isolation: 'isolate', zIndex: 10 }}>
              <h4>Spending Over Time</h4>
              
              {/* Year Selector for Trends */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{ marginRight: '10px', fontWeight: '500' }}>Select Year:</label>
                <select 
                  value={trendYear} 
                  onChange={(e) => setTrendYear(Number(e.target.value))}
                  style={{ padding: '6px 12px', borderRadius: '4px', border: '1px solid #ddd' }}
                >
                  {[2023, 2024, 2025, 2026].map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>

              {trendLoading ? (
                showLoadingMsg && <p>Loading trends...</p>
              ) : (
                <>
                  {/* Monthly Trend Chart - isolated transitions */}
                  <div style={{ marginBottom: '40px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                      <h5 style={{ margin: 0 }}>Monthly Spending Trend ({trendYear})</h5>
                      <div>
                        <button 
                          onClick={() => setMonthlyTrendChartType('bar')} 
                          style={{ 
                            padding: '6px 12px', 
                            marginRight: '5px',
                            backgroundColor: monthlyTrendChartType === 'bar' ? '#4CAF50' : '#f0f0f0',
                            color: monthlyTrendChartType === 'bar' ? 'white' : 'black',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          Bar
                        </button>
                        <button 
                          onClick={() => setMonthlyTrendChartType('line')} 
                          style={{ 
                            padding: '6px 12px',
                            backgroundColor: monthlyTrendChartType === 'line' ? '#4CAF50' : '#f0f0f0',
                            color: monthlyTrendChartType === 'line' ? 'white' : 'black',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          Line
                        </button>
                      </div>
                    </div>
                    <div style={{ position: 'relative', minHeight: '320px', overflow: 'hidden' }}>
                      {showSkeleton && (
                        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8fafc', zIndex: 1000, borderRadius: '8px' }}>
                          <div style={{ color: '#64748b', fontSize: '14px', fontWeight: 500 }}>Updating chart...</div>
                        </div>
                      )}
                      {yearlyTrendData && yearlyTrendData.length > 0 ? (
                        <div className={`chart-transition-wrapper ${monthlyTrendVisible ? 'chart-transition-visible' : 'chart-transition-hidden'}`}>
                          <div key={`trend-container-${trendYear}-${monthlyTrendChartType}`} style={{ maxWidth: '800px', margin: '0 auto', isolation: 'isolate' }}>
                            {monthlyTrendChartType === 'bar' ? (
                              <Bar key={trendChartKey} data={monthlyTrendBarData} options={{ ...commonOptions, plugins: { ...commonOptions.plugins, legend: { display: false }, tooltip: commonOptions.plugins.tooltip }, scales: { y: { beginAtZero: true, ticks: { callback: v => `$${v}` } } } }} />
                            ) : (
                              <Line key={trendChartKey} data={monthlyTrendLineData} options={{ ...commonOptions, plugins: { ...commonOptions.plugins, tooltip: { callbacks: { label: (context) => `${context.dataset.label}: $${(context.parsed?.y ?? context.parsed)?.toFixed(2)}` } } }, scales: { y: { beginAtZero: true, ticks: { callback: v => `$${v}` } } } }} />
                            )}
                          </div>
                        </div>
                      ) : (
                        <p>No data for {trendYear}</p>
                      )}
                    </div>
                  </div>

                  {/* Year-over-Year Chart - always visible, not affected by trendYear changes */}
                  <div>
                    <h5 style={{ marginBottom: '15px' }}>Year-over-Year Comparison</h5>
                    {yearOverYearData && yearOverYearData.length > 0 ? (
                      <div key={`yoy-container-${yoyChartKey}`} style={{ maxWidth: '800px', margin: '0 auto', minHeight: '320px', isolation: 'isolate' }}>
                        <Bar key={yoyChartKey} data={yearOverYearBarData} options={{ ...commonOptions, plugins: { ...commonOptions.plugins, legend: { display: false }, tooltip: commonOptions.plugins.tooltip }, scales: { y: { beginAtZero: true, ticks: { callback: v => `$${v}` } } } }} />
                      </div>
                    ) : (
                      <p>No year-over-year data available</p>
                    )}
                  </div>
                </>
              )}
            </div>

            {/* Category Year-to-Year Comparison */}
            <div className="chart-card" id="category-comparison-section" style={{ position: 'relative', overflow: 'clip', isolation: 'isolate', visibility: showSkeleton ? 'hidden' : 'visible', zIndex: 1 }}>
              <h4>Category Year-to-Year Comparison</h4>
              <div style={{ marginBottom: '12px', display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
                <div>
                  <label style={{ fontWeight: 500, marginRight: 6 }}>Category:</label>
                  <select 
                    value={comparisonCategory} 
                    onChange={(e) => setComparisonCategory(e.target.value)} 
                    style={{ padding: '6px 12px', borderRadius: '4px', border: '1px solid #ddd' }}
                  >
                    <option value="">Choose category...</option>
                    {categoryBreakdown.map(([name]) => (
                      <option key={name} value={name}>{name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontWeight: 500, marginRight: 6 }}>Year A:</label>
                  <select value={comparisonYearA} onChange={(e) => setComparisonYearA(Number(e.target.value))} style={{ padding: '6px 12px', borderRadius: '4px', border: '1px solid #ddd' }}>
                    {[2023,2024,2025,2026].map(y => <option key={y} value={y}>{y}</option>)}
                  </select>
                </div>

                <div>
                  <label style={{ fontWeight: 500, marginRight: 6 }}>Year B:</label>
                  <select value={comparisonYearB} onChange={(e) => setComparisonYearB(Number(e.target.value))} style={{ padding: '6px 12px', borderRadius: '4px', border: '1px solid #ddd' }}>
                    {[2023,2024,2025,2026].map(y => <option key={y} value={y}>{y}</option>)}
                  </select>
                </div>
              </div>

              <div style={{ maxWidth: '900px', margin: '0 auto', padding: '10px', minHeight: '360px', isolation: 'isolate' }}>
                {!comparisonCategory ? (
                  <div style={{ height: '320px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999', fontSize: '15px' }}>
                    Choose a category and years to compare
                  </div>
                ) : comparisonLoading ? (
                  <div style={{ height: '320px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666' }}>
                    Loading comparison...
                  </div>
                ) : (comparisonData && comparisonData.labels && comparisonData.labels.length > 0) ? (
                  <div key={`comp-container-${comparisonChartKey}`} style={{ isolation: 'isolate' }}>
                    <Bar key={comparisonChartKey} data={comparisonData} options={{ ...commonOptions, plugins: { ...commonOptions.plugins, legend: { position: 'bottom' }, tooltip: { callbacks: { label: (context) => `${context.dataset.label}: $${(context.parsed?.y ?? context.parsed)?.toFixed(2)}` } } }, scales: { y: { beginAtZero: true, ticks: { callback: (v) => `$${v}` } } } }} />
                  </div>
                ) : (
                  <div style={{ height: '320px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666' }}>
                    No data available
                  </div>
                )}
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
