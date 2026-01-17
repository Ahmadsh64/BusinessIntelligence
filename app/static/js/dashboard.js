// Dashboard JavaScript

let filterData = {};

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set default dates
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 1);
    
    document.getElementById('date_start').value = startDate.toISOString().split('T')[0];
    document.getElementById('date_end').value = endDate.toISOString().split('T')[0];
    
    // Load filter options
    loadFilters();
    
    // Load dashboard data
    loadDashboard();
});

// Load filter options
async function loadFilters() {
    try {
        const response = await fetch('/api/filters');
        const data = await response.json();
        
        // Populate stores
        const storesSelect = document.getElementById('stores');
        storesSelect.innerHTML = '';
        data.stores.forEach(store => {
            const option = document.createElement('option');
            option.value = store.store_id;
            option.textContent = `${store.store_name} (${store.city})`;
            storesSelect.appendChild(option);
        });
        
        // Populate categories
        const categoriesSelect = document.getElementById('categories');
        categoriesSelect.innerHTML = '';
        data.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoriesSelect.appendChild(option);
        });
        
        // Populate regions
        const regionsSelect = document.getElementById('regions');
        regionsSelect.innerHTML = '';
        data.regions.forEach(region => {
            const option = document.createElement('option');
            option.value = region;
            option.textContent = region;
            regionsSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

// Get filter values
function getFilters() {
    const dateStart = document.getElementById('date_start').value;
    const dateEnd = document.getElementById('date_end').value;
    const stores = Array.from(document.getElementById('stores').selectedOptions)
        .map(opt => opt.value).join(',');
    const categories = Array.from(document.getElementById('categories').selectedOptions)
        .map(opt => opt.value).join(',');
    const regions = Array.from(document.getElementById('regions').selectedOptions)
        .map(opt => opt.value).join(',');
    
    return { dateStart, dateEnd, stores, categories, regions };
}

// Build query string
function buildQueryString(filters) {
    const params = new URLSearchParams();
    if (filters.dateStart) params.append('date_start', filters.dateStart);
    if (filters.dateEnd) params.append('date_end', filters.dateEnd);
    if (filters.stores) params.append('stores', filters.stores);
    if (filters.categories) params.append('categories', filters.categories);
    if (filters.regions) params.append('regions', filters.regions);
    return params.toString();
}

// Load dashboard data
async function loadDashboard() {
    const filters = getFilters();
    const queryString = buildQueryString(filters);
    
    try {
        // Load KPIs
        const kpiResponse = await fetch(`/api/kpis?${queryString}`);
        const kpiData = await kpiResponse.json();
        updateKPIs(kpiData);
        
        // Load sales trend
        const trendResponse = await fetch(`/api/sales-trend?${queryString}`);
        const trendData = await trendResponse.json();
        updateSalesTrend(trendData);
        
        // Load store performance
        const storeResponse = await fetch(`/api/store-performance?${queryString}`);
        const storeData = await storeResponse.json();
        updateStorePerformance(storeData);
        
        // Load product performance
        const productResponse = await fetch(`/api/product-performance?${queryString}`);
        const productData = await productResponse.json();
        updateProductPerformance(productData);
        
        // Load category revenue
        const categoryResponse = await fetch(`/api/category-revenue?${queryString}`);
        const categoryData = await categoryResponse.json();
        updateCategoryRevenue(categoryData);
        
        // Load customer insights
        const customerResponse = await fetch(`/api/customer-insights?${queryString}`);
        const customerData = await customerResponse.json();
        updateCustomerInsights(customerData);
        
        // Load seasonal analysis
        const seasonalResponse = await fetch(`/api/seasonal-analysis?${queryString}`);
        const seasonalData = await seasonalResponse.json();
        updateSeasonalAnalysis(seasonalData);
        
        // Load forecast
        loadForecast();
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load sales forecast
async function loadForecast() {
    const filters = getFilters();
    const forecastMonths = document.getElementById('forecast-months')?.value || '6';
    
    // Use a date range that includes historical data (last 2 years)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 2);
    
    // Override filters with historical date range for forecast
    const forecastFilters = {
        ...filters,
        dateStart: startDate.toISOString().split('T')[0],
        dateEnd: endDate.toISOString().split('T')[0],
        months: forecastMonths
    };
    
    const queryString = buildQueryString(forecastFilters);
    
    try {
        const response = await fetch(`/api/sales-forecast?${queryString}`);
        if (!response.ok) {
            const errorData = await response.json();
            if (document.getElementById('forecast-chart')) {
                document.getElementById('forecast-chart').innerHTML = 
                    `<div class="loading">${errorData.error || 'שגיאה בטעינת חיזוי'}</div>`;
            }
            return;
        }
        const data = await response.json();
        if (data.error) {
            if (document.getElementById('forecast-chart')) {
                document.getElementById('forecast-chart').innerHTML = 
                    `<div class="loading">${data.error}</div>`;
            }
            return;
        }
        updateForecast(data);
    } catch (error) {
        console.error('Error loading forecast:', error);
        if (document.getElementById('forecast-chart')) {
            document.getElementById('forecast-chart').innerHTML = 
                `<div class="loading">שגיאה בטעינת חיזוי: ${error.message}</div>`;
        }
    }
}

// Update KPI cards
function updateKPIs(data) {
    if (!data || !data.total_revenue) return;
    
    document.getElementById('total_revenue').textContent = 
        `₪${Number(data.total_revenue).toLocaleString('he-IL', {maximumFractionDigits: 0})}`;
    document.getElementById('total_profit').textContent = 
        `₪${Number(data.total_profit).toLocaleString('he-IL', {maximumFractionDigits: 0})}`;
    document.getElementById('profit_margin').textContent = 
        `${Number(data.profit_margin).toFixed(1)}%`;
    document.getElementById('avg_order_value').textContent = 
        `₪${Number(data.avg_order_value).toLocaleString('he-IL', {maximumFractionDigits: 0})}`;
    document.getElementById('total_transactions').textContent = 
        Number(data.total_transactions).toLocaleString('he-IL');
}

// Update sales trend charts
function updateSalesTrend(data) {
    if (!data || data.length === 0) return;
    
    const months = data.map(d => d.month_name);
    const revenue = data.map(d => d.revenue);
    const profit = data.map(d => d.profit);
    
    // Revenue trend
    Plotly.newPlot('revenue-trend', [{
        x: months,
        y: revenue,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'הכנסות',
        line: { color: '#667eea', width: 3 },
        marker: { size: 8 }
    }], {
        title: 'מגמת הכנסות חודשית',
        xaxis: { title: 'חודש' },
        yaxis: { title: 'הכנסות (₪)' },
        font: { family: 'Arial', size: 12 }
    }, {responsive: true});
    
    // Profit trend
    Plotly.newPlot('profit-trend', [{
        x: months,
        y: profit,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'רווח',
        line: { color: '#48bb78', width: 3 },
        marker: { size: 8 }
    }], {
        title: 'מגמת רווח חודשית',
        xaxis: { title: 'חודש' },
        yaxis: { title: 'רווח (₪)' },
        font: { family: 'Arial', size: 12 }
    }, {responsive: true});
}

// Update store performance charts
function updateStorePerformance(data) {
    if (!data || data.length === 0) return;
    
    const stores = data.map(d => d.store_name).reverse();
    const revenue = data.map(d => d.revenue).reverse();
    const margin = data.map(d => d.profit_margin).reverse();
    
    // Store revenue
    Plotly.newPlot('store-revenue', [{
        x: revenue,
        y: stores,
        type: 'bar',
        orientation: 'h',
        marker: { color: '#667eea' }
    }], {
        title: 'סניפים מובילים לפי הכנסות',
        xaxis: { title: 'הכנסות (₪)' },
        yaxis: { title: 'סניף' },
        font: { family: 'Arial', size: 12 },
        height: 500
    }, {responsive: true});
    
    // Store margin
    Plotly.newPlot('store-margin', [{
        x: margin,
        y: stores,
        type: 'bar',
        orientation: 'h',
        marker: { color: '#48bb78' }
    }], {
        title: 'שולי רווח לפי סניף',
        xaxis: { title: 'שולי רווח (%)' },
        yaxis: { title: 'סניף' },
        font: { family: 'Arial', size: 12 },
        height: 500
    }, {responsive: true});
    
    // Store table
    let tableHTML = '<table><thead><tr><th>סניף</th><th>עיר</th><th>אזור</th><th>הכנסות</th><th>רווח</th><th>שולי רווח</th><th>עסקאות</th></tr></thead><tbody>';
    data.forEach(store => {
        tableHTML += `<tr>
            <td>${store.store_name}</td>
            <td>${store.city}</td>
            <td>${store.region}</td>
            <td>₪${Number(store.revenue).toLocaleString('he-IL', {maximumFractionDigits: 0})}</td>
            <td>₪${Number(store.profit).toLocaleString('he-IL', {maximumFractionDigits: 0})}</td>
            <td>${Number(store.profit_margin).toFixed(1)}%</td>
            <td>${Number(store.transactions).toLocaleString('he-IL')}</td>
        </tr>`;
    });
    tableHTML += '</tbody></table>';
    document.getElementById('store-table').innerHTML = tableHTML;
}

// Update product performance charts
function updateProductPerformance(data) {
    if (!data || data.length === 0) return;
    
    const top10 = data.slice(0, 10).reverse();
    const products = top10.map(d => d.product_name);
    const revenue = top10.map(d => d.revenue);
    
    Plotly.newPlot('top-products', [{
        x: revenue,
        y: products,
        type: 'bar',
        orientation: 'h',
        marker: { color: '#764ba2' }
    }], {
        title: '10 המוצרים המובילים לפי הכנסות',
        xaxis: { title: 'הכנסות (₪)' },
        yaxis: { title: 'מוצר' },
        font: { family: 'Arial', size: 12 },
        height: 400
    }, {responsive: true});
}

// Update category revenue chart
function updateCategoryRevenue(data) {
    if (!data || data.length === 0) return;
    
    const categories = data.map(d => d.category);
    const revenue = data.map(d => d.revenue);
    
    Plotly.newPlot('category-revenue', [{
        values: revenue,
        labels: categories,
        type: 'pie',
        hole: 0.4,
        textinfo: 'label+percent',
        textposition: 'outside'
    }], {
        title: 'הכנסות לפי קטגוריה',
        font: { family: 'Arial', size: 12 },
        height: 400
    }, {responsive: true});
}

// Update customer insights charts
function updateCustomerInsights(data) {
    if (!data || data.length === 0) return;
    
    // Group by age group
    const ageGroups = {};
    data.forEach(d => {
        if (!ageGroups[d.age_group]) {
            ageGroups[d.age_group] = 0;
        }
        ageGroups[d.age_group] += d.revenue;
    });
    
    // Group by gender
    const genders = {};
    data.forEach(d => {
        if (!genders[d.gender]) {
            genders[d.gender] = 0;
        }
        genders[d.gender] += d.revenue;
    });
    
    // Age group chart
    Plotly.newPlot('age-revenue', [{
        x: Object.keys(ageGroups),
        y: Object.values(ageGroups),
        type: 'bar',
        marker: { color: '#ed8936' }
    }], {
        title: 'הכנסות לפי קבוצת גיל',
        xaxis: { title: 'קבוצת גיל' },
        yaxis: { title: 'הכנסות (₪)' },
        font: { family: 'Arial', size: 12 },
        height: 350
    }, {responsive: true});
    
    // Gender chart
    Plotly.newPlot('gender-revenue', [{
        values: Object.values(genders),
        labels: Object.keys(genders),
        type: 'pie',
        hole: 0.4,
        textinfo: 'label+percent'
    }], {
        title: 'הכנסות לפי מגדר',
        font: { family: 'Arial', size: 12 },
        height: 350
    }, {responsive: true});
}

// Update seasonal analysis charts
function updateSeasonalAnalysis(data) {
    if (!data || !data.quarterly || data.quarterly.length === 0) return;
    
    // Quarterly trend
    const quarters = data.quarterly.map(d => `${d.year} ${d.quarter_name}`);
    const qRevenue = data.quarterly.map(d => d.revenue);
    const qProfit = data.quarterly.map(d => d.profit);
    
    if (document.getElementById('quarterly-trend')) {
        Plotly.newPlot('quarterly-trend', [
            {
                x: quarters,
                y: qRevenue,
                type: 'bar',
                name: 'הכנסות',
                marker: { color: '#667eea' }
            },
            {
                x: quarters,
                y: qProfit,
                type: 'bar',
                name: 'רווח',
                marker: { color: '#48bb78' }
            }
        ], {
            title: 'מגמות רבעוניות',
            xaxis: { title: 'רבעון' },
            yaxis: { title: 'סכום (₪)' },
            barmode: 'group',
            font: { family: 'Arial', size: 12 },
            height: 400
        }, {responsive: true});
    }
    
    // Monthly pattern (average across years)
    if (data.monthly && data.monthly.length > 0 && document.getElementById('monthly-pattern')) {
        const months = data.monthly.map(d => d.month_name);
        const avgRevenue = data.monthly.map(d => d.avg_revenue);
        
        Plotly.newPlot('monthly-pattern', [{
            x: months,
            y: avgRevenue,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'הכנסה ממוצעת',
            line: { color: '#ed8936', width: 3, shape: 'spline' },
            marker: { size: 10 }
        }], {
            title: 'דפוס חודשי ממוצע (על פני שנים)',
            xaxis: { title: 'חודש' },
            yaxis: { title: 'הכנסה ממוצעת (₪)' },
            font: { family: 'Arial', size: 12 },
            height: 400
        }, {responsive: true});
    }
    
    // Display insights
    if (data.insights && data.insights.length > 0 && document.getElementById('seasonal-insights')) {
        let insightsHTML = '<h3>💡 תובנות עונתיות:</h3><ul>';
        data.insights.forEach(insight => {
            if (insight.type === 'peak_month') {
                insightsHTML += `<li><strong>חודש שיא:</strong> ${insight.month} - 
                    הכנסות של ₪${Number(insight.revenue).toLocaleString('he-IL', {maximumFractionDigits: 0})} 
                    (${insight.percentage_above_avg.toFixed(1)}% מעל הממוצע)</li>`;
            } else if (insight.type === 'low_month') {
                insightsHTML += `<li><strong>חודש נמוך:</strong> ${insight.month} - 
                    הכנסות של ₪${Number(insight.revenue).toLocaleString('he-IL', {maximumFractionDigits: 0})} 
                    (${insight.percentage_below_avg.toFixed(1)}% מתחת לממוצע)</li>`;
            }
        });
        insightsHTML += '</ul>';
        document.getElementById('seasonal-insights').innerHTML = insightsHTML;
    }
}

// Update forecast chart
function updateForecast(data) {
    if (!data || !data.historical || !data.forecast || !document.getElementById('forecast-chart')) return;
    
    // Combine historical and forecast
    const allData = [...data.historical, ...data.forecast];
    const labels = allData.map(d => `${d.year}-${String(d.month).padStart(2, '0')}`);
    const revenue = allData.map(d => d.revenue);
    const profit = allData.map(d => d.profit);
    const isForecast = allData.map(d => d.is_forecast || false);
    
    // Create traces
    const traces = [
        {
            x: labels,
            y: revenue,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'הכנסות',
            line: { color: '#667eea', width: 3 },
            marker: { 
                size: 8,
                color: isForecast.map(f => f ? '#ff6b6b' : '#667eea')
            }
        },
        {
            x: labels,
            y: profit,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'רווח',
            line: { color: '#48bb78', width: 3 },
            marker: { 
                size: 8,
                color: isForecast.map(f => f ? '#ff6b6b' : '#48bb78')
            }
        }
    ];
    
    // Add vertical line separating historical from forecast
    const forecastStart = data.historical.length;
    const maxRevenue = Math.max(...revenue);
    const shapes = [{
        type: 'line',
        x0: labels[forecastStart - 1],
        x1: labels[forecastStart - 1],
        y0: 0,
        y1: maxRevenue,
        line: {
            color: '#ff6b6b',
            width: 2,
            dash: 'dash'
        }
    }];
    
    const annotations = [{
        x: labels[forecastStart],
        y: maxRevenue * 0.9,
        text: 'תחילת חיזוי',
        showarrow: true,
        arrowhead: 2,
        ax: 0,
        ay: -40
    }];
    
    Plotly.newPlot('forecast-chart', traces, {
        title: 'חיזוי מכירות עתידי',
        xaxis: { title: 'חודש' },
        yaxis: { title: 'סכום (₪)' },
        shapes: shapes,
        annotations: annotations,
        font: { family: 'Arial', size: 12 },
        height: 500
    }, {responsive: true});
    
    // Display accuracy
    if (data.model_accuracy && document.getElementById('forecast-accuracy')) {
        const accuracyHTML = `
            <h3>📊 דיוק המודל:</h3>
            <p><strong>דיוק חיזוי הכנסות (R²):</strong> ${(data.model_accuracy.revenue_r2 * 100).toFixed(1)}%</p>
            <p><strong>דיוק חיזוי רווח (R²):</strong> ${(data.model_accuracy.profit_r2 * 100).toFixed(1)}%</p>
            <p class="note">* R² של 1.0 = חיזוי מושלם, 0.0 = חיזוי אקראי</p>
        `;
        document.getElementById('forecast-accuracy').innerHTML = accuracyHTML;
    }
}

