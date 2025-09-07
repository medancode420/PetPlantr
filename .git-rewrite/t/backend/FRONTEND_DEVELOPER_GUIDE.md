# 🎨 Frontend Developer Integration Guide

## PetPlantr Backend API - Frontend Integration

### 🚀 Quick Start for Frontend Developers

The enhanced PetPlantr backend now provides frontend-optimized endpoints designed specifically for modern web and mobile applications.

---

## 📡 Base Configuration

```typescript
// API Configuration
const API_BASE_URL = 'https://your-api-gateway-url.amazonaws.com/dev';

// Headers for all requests
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-auth-token'
};
```

---

## 🎯 Customer Dashboard Integration

### **React Example: Customer Dashboard Component**

```typescript
import React, { useState, useEffect } from 'react';

interface CustomerDashboard {
  customer: {
    id: string;
    totalOrders: number;
    activeOrders: number;
  };
  currentOrders: Array<{
    id: string;
    petName: string;
    breed: string;
    status: string;
    progress: {
      current: number;
      total: number;
      percentage: number;
      stage: string;
    };
    planter: {
      material: string;
      color: string;
      quality: string;
    };
    timeline: {
      ordered: string;
      printingStarted?: string;
      estimatedCompletion?: string;
    };
    printer?: {
      id: string;
      name: string;
      status: string;
    };
  }>;
  farmStatus: {
    queuePosition?: number;
    estimatedWaitTime: string;
    activePrinters: number;
    totalCapacity: number;
    utilizationRate: number;
  };
  notifications: {
    unread: number;
    latest: Array<{
      type: string;
      title: string;
      message: string;
      timestamp: string;
    }>;
  };
}

const CustomerDashboard: React.FC<{ customerId: string }> = ({ customerId }) => {
  const [dashboard, setDashboard] = useState<CustomerDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboard();
  }, [customerId]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${API_BASE_URL}/api/farm/frontend?customerId=${customerId}`,
        { headers }
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard');
      }
      
      const data = await response.json();
      setDashboard(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading dashboard...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!dashboard) return <div>No data available</div>;

  return (
    <div className="customer-dashboard">
      <header>
        <h1>Welcome Back!</h1>
        <p>{dashboard.customer.totalOrders} total orders</p>
        <p>{dashboard.customer.activeOrders} active orders</p>
      </header>

      <section className="current-orders">
        <h2>Current Orders</h2>
        {dashboard.currentOrders.map(order => (
          <div key={order.id} className="order-card">
            <h3>{order.petName} ({order.breed})</h3>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${order.progress.percentage}%` }}
              />
              <span>{order.progress.stage}</span>
            </div>
            <p>Material: {order.planter.material} - {order.planter.color}</p>
            <p>Quality: {order.planter.quality}</p>
            {order.printer && (
              <p>Printer: {order.printer.name} ({order.printer.status})</p>
            )}
            {order.timeline.estimatedCompletion && (
              <p>Estimated completion: {new Date(order.timeline.estimatedCompletion).toLocaleString()}</p>
            )}
          </div>
        ))}
      </section>

      <section className="farm-status">
        <h2>Farm Status</h2>
        <p>Queue position: {dashboard.farmStatus.queuePosition || 'N/A'}</p>
        <p>Estimated wait time: {dashboard.farmStatus.estimatedWaitTime}</p>
        <p>Active printers: {dashboard.farmStatus.activePrinters}/{dashboard.farmStatus.totalCapacity}</p>
        <div className="utilization">
          <span>Farm utilization: {dashboard.farmStatus.utilizationRate}%</span>
          <div className="utilization-bar">
            <div 
              style={{ width: `${dashboard.farmStatus.utilizationRate}%` }}
              className="utilization-fill"
            />
          </div>
        </div>
      </section>

      <section className="notifications">
        <h2>Notifications ({dashboard.notifications.unread} unread)</h2>
        {dashboard.notifications.latest.map((notification, index) => (
          <div key={index} className="notification">
            <h4>{notification.title}</h4>
            <p>{notification.message}</p>
            <small>{new Date(notification.timestamp).toLocaleString()}</small>
          </div>
        ))}
      </section>
    </div>
  );
};

export default CustomerDashboard;
```

---

## 📊 Real-Time Farm Monitoring

### **Vue.js Example: Live Farm Dashboard**

```vue
<template>
  <div class="farm-monitor">
    <div class="farm-overview">
      <h2>Farm Status: {{ farmData?.farmOverview.status }}</h2>
      <div class="metrics">
        <div class="metric">
          <span>Active Printers</span>
          <strong>{{ farmData?.farmOverview.activePrinters }}/{{ farmData?.farmOverview.totalPrinters }}</strong>
        </div>
        <div class="metric">
          <span>Utilization</span>
          <strong>{{ farmData?.farmOverview.utilizationRate }}%</strong>
        </div>
        <div class="metric">
          <span>Queue Size</span>
          <strong>{{ farmData?.farmOverview.queueSize }}</strong>
        </div>
      </div>
    </div>

    <div class="printers-grid">
      <div 
        v-for="printer in farmData?.printers" 
        :key="printer.id"
        :class="['printer-card', printer.status]"
      >
        <h3>{{ printer.name }}</h3>
        <div class="status-badge">{{ printer.status }}</div>
        <div v-if="printer.currentJob" class="current-job">
          <p>Printing: {{ printer.currentJob.petName }}</p>
          <div class="progress">
            <div 
              class="progress-bar" 
              :style="{ width: printer.progress + '%' }"
            ></div>
            <span>{{ printer.progress }}%</span>
          </div>
        </div>
        <div class="realtime-data">
          <span>Bed: {{ printer.realtime?.temperatureBed }}°C</span>
          <span>Nozzle: {{ printer.realtime?.temperatureNozzle }}°C</span>
          <span>Health: {{ printer.healthScore }}%</span>
        </div>
      </div>
    </div>

    <div class="recent-events">
      <h3>Recent Events</h3>
      <div 
        v-for="event in farmData?.recentEvents" 
        :key="event.id"
        :class="['event', event.severity]"
      >
        <span class="timestamp">{{ formatTime(event.timestamp) }}</span>
        <span class="message">{{ event.message }}</span>
      </div>
    </div>

    <div class="alerts" v-if="farmData?.alerts.length">
      <h3>Active Alerts</h3>
      <div 
        v-for="alert in farmData.alerts" 
        :key="alert.type"
        :class="['alert', alert.severity]"
      >
        {{ alert.message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

interface LiveFarmData {
  timestamp: string;
  farmOverview: {
    status: string;
    activePrinters: number;
    totalPrinters: number;
    utilizationRate: number;
    queueSize: number;
    estimatedWaitTime: string;
  };
  printers: Array<{
    id: string;
    name: string;
    status: string;
    progress: number;
    currentJob?: any;
    realtime?: any;
    healthScore: number;
  }>;
  recentEvents: Array<{
    id: string;
    type: string;
    message: string;
    timestamp: string;
    severity: string;
  }>;
  alerts: Array<any>;
}

const farmData = ref<LiveFarmData | null>(null);
let updateInterval: NodeJS.Timeout;

const fetchLiveData = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/farm/live`, { headers });
    if (response.ok) {
      farmData.value = await response.json();
    }
  } catch (error) {
    console.error('Failed to fetch live data:', error);
  }
};

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString();
};

onMounted(() => {
  fetchLiveData();
  // Update every 30 seconds
  updateInterval = setInterval(fetchLiveData, 30000);
});

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval);
  }
});
</script>

<style scoped>
.farm-monitor {
  padding: 20px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  text-align: center;
}

.printers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.printer-card {
  padding: 16px;
  border: 2px solid #ddd;
  border-radius: 8px;
  background: white;
}

.printer-card.printing {
  border-color: #4CAF50;
}

.printer-card.idle {
  border-color: #2196F3;
}

.printer-card.error {
  border-color: #f44336;
}

.progress-bar {
  background: #4CAF50;
  height: 4px;
  border-radius: 2px;
}

.event {
  padding: 8px;
  margin: 4px 0;
  border-radius: 4px;
}

.event.success {
  background: #e8f5e8;
}

.event.info {
  background: #e3f2fd;
}

.alert.warning {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
}

.alert.error {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
}
</style>
```

---

## 🔄 Job Management Integration

### **Angular Service Example**

```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';

interface PrintJob {
  id: string;
  customerId: string;
  customerEmail: string;
  petName: string;
  breed: string;
  status: string;
  progress: {
    current: number;
    total: number;
    percentage: number;
    stage: string;
  };
  planter: {
    material: string;
    color: string;
    quality: string;
  };
  timeline: {
    ordered: string;
    printingStarted?: string;
    estimatedCompletion?: string;
  };
  printer?: {
    id: string;
    name: string;
    status: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class FarmService {
  private apiUrl = 'https://your-api-gateway-url.amazonaws.com/dev/api/farm';
  private jobsSubject = new BehaviorSubject<PrintJob[]>([]);
  
  public jobs$ = this.jobsSubject.asObservable();

  constructor(private http: HttpClient) {}

  // Get customer dashboard
  getCustomerDashboard(customerId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/frontend?customerId=${customerId}`);
  }

  // Get live farm data
  getLiveFarmData(): Observable<any> {
    return this.http.get(`${this.apiUrl}/live`);
  }

  // Get jobs with filtering
  getJobs(filters?: {
    status?: string;
    priority?: number;
    limit?: number;
  }): Observable<{ jobs: PrintJob[]; total: number }> {
    let params = '';
    if (filters) {
      const queryParams = new URLSearchParams();
      if (filters.status) queryParams.append('status', filters.status);
      if (filters.priority) queryParams.append('priority', filters.priority.toString());
      if (filters.limit) queryParams.append('limit', filters.limit.toString());
      params = `?${queryParams.toString()}`;
    }
    
    return this.http.get<{ jobs: PrintJob[]; total: number }>(`${this.apiUrl}/jobs${params}`);
  }

  // Create new print job
  createJob(jobData: {
    customerId: string;
    customerEmail: string;
    petName: string;
    breed: string;
    stlFile: string;
    estimatedTime: number;
    materialType: string;
    materialColor: string;
    priority?: number;
    qualityRequirements?: string;
  }): Observable<any> {
    return this.http.post(`${this.apiUrl}/jobs`, jobData);
  }

  // Update job
  updateJob(jobId: string, updates: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/jobs/${jobId}`, updates);
  }

  // Assign job to printer
  assignJob(jobId: string, printerId?: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/assign`, { jobId, printerId });
  }

  // Complete job
  completeJob(jobId: string, success: boolean, qualityScore?: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/complete`, { jobId, success, qualityScore });
  }

  // Get farm status
  getFarmStatus(): Observable<any> {
    return this.http.get(`${this.apiUrl}/status`);
  }

  // Get farm metrics
  getFarmMetrics(timeframe: string = '24h'): Observable<any> {
    return this.http.get(`${this.apiUrl}/metrics?timeframe=${timeframe}`);
  }

  // Get farm optimization recommendations
  getFarmOptimization(): Observable<any> {
    return this.http.get(`${this.apiUrl}/optimization`);
  }

  // Real-time updates (would integrate with WebSocket)
  subscribeToJobUpdates(customerId: string): void {
    // WebSocket implementation would go here
    // For now, polling example:
    setInterval(() => {
      this.getJobs({ status: 'active' }).subscribe(data => {
        this.jobsSubject.next(data.jobs);
      });
    }, 30000);
  }
}
```

---

## 📱 Mobile App Integration

### **React Native Example**

```typescript
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, RefreshControl, StyleSheet } from 'react-native';

const PetPlantrApp = () => {
  const [orders, setOrders] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [farmStatus, setFarmStatus] = useState(null);

  const fetchData = async () => {
    try {
      const customerId = 'customer_123'; // From user auth
      
      // Fetch customer dashboard
      const dashboardResponse = await fetch(
        `${API_BASE_URL}/api/farm/frontend?customerId=${customerId}`,
        { headers }
      );
      const dashboardData = await dashboardResponse.json();
      
      setOrders(dashboardData.currentOrders);
      setFarmStatus(dashboardData.farmStatus);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const renderOrder = ({ item }) => (
    <View style={styles.orderCard}>
      <Text style={styles.petName}>{item.petName}</Text>
      <Text style={styles.breed}>{item.breed}</Text>
      <View style={styles.progressContainer}>
        <View style={[styles.progressBar, { width: `${item.progress.percentage}%` }]} />
        <Text style={styles.progressText}>{item.progress.stage}</Text>
      </View>
      <Text style={styles.material}>
        {item.planter.material} - {item.planter.color}
      </Text>
      {item.printer && (
        <Text style={styles.printer}>
          Printer: {item.printer.name}
        </Text>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>My Pet Planters</Text>
      
      {farmStatus && (
        <View style={styles.farmStatus}>
          <Text>Queue position: {farmStatus.queuePosition || 'N/A'}</Text>
          <Text>Wait time: {farmStatus.estimatedWaitTime}</Text>
          <Text>Farm utilization: {farmStatus.utilizationRate}%</Text>
        </View>
      )}

      <FlatList
        data={orders}
        renderItem={renderOrder}
        keyExtractor={(item) => item.id}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        style={styles.ordersList}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  farmStatus: {
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  orderCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  petName: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  breed: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  progressContainer: {
    marginVertical: 8,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#4CAF50',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    marginTop: 4,
    color: '#4CAF50',
  },
  material: {
    fontSize: 12,
    color: '#888',
  },
  printer: {
    fontSize: 12,
    color: '#2196F3',
  },
  ordersList: {
    flex: 1,
  },
});

export default PetPlantrApp;
```

---

## 🔔 WebSocket Integration (Planned)

### **Real-Time Updates Setup**

```typescript
// WebSocket client setup
class PetPlantrWebSocket {
  private socket: WebSocket | null = null;
  private customerId: string;

  constructor(customerId: string) {
    this.customerId = customerId;
  }

  connect() {
    this.socket = new WebSocket('wss://your-websocket-url.amazonaws.com');
    
    this.socket.onopen = () => {
      // Subscribe to customer-specific updates
      this.socket?.send(JSON.stringify({
        action: 'subscribe',
        customerId: this.customerId
      }));
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleUpdate(data);
    };
  }

  private handleUpdate(data: any) {
    switch (data.type) {
      case 'job_status_update':
        // Update job status in your app
        this.onJobUpdate(data.payload);
        break;
      case 'printer_status_update':
        // Update printer status
        this.onPrinterUpdate(data.payload);
        break;
      case 'farm_alert':
        // Show farm alerts
        this.onFarmAlert(data.payload);
        break;
    }
  }

  onJobUpdate(payload: any) {
    // Implement your job update logic
  }

  onPrinterUpdate(payload: any) {
    // Implement your printer update logic
  }

  onFarmAlert(payload: any) {
    // Implement your alert logic
  }
}
```

---

## 🎨 CSS Styling Examples

### **Modern Dashboard Styles**

```css
/* Customer Dashboard */
.customer-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Inter', sans-serif;
}

.order-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.order-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin: 8px 0;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #66BB6A);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.printing {
  background: #e8f5e8;
  color: #2e7d2e;
}

.status-badge.queued {
  background: #e3f2fd;
  color: #1976d2;
}

.status-badge.completed {
  background: #f3e5f5;
  color: #7b1fa2;
}

/* Farm Monitor Styles */
.farm-overview {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px;
  border-radius: 16px;
  margin-bottom: 24px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.metric {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}

.printer-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  border-left: 4px solid #ddd;
  transition: all 0.3s ease;
}

.printer-card.printing {
  border-left-color: #4CAF50;
}

.printer-card.idle {
  border-left-color: #2196F3;
}

.printer-card.error {
  border-left-color: #f44336;
}

/* Responsive Design */
@media (max-width: 768px) {
  .customer-dashboard {
    padding: 16px;
  }
  
  .metrics {
    grid-template-columns: 1fr;
  }
  
  .printers-grid {
    grid-template-columns: 1fr;
  }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
  .customer-dashboard {
    background: #121212;
    color: white;
  }
  
  .order-card {
    background: #1e1e1e;
    color: white;
  }
  
  .progress-bar {
    background: #333;
  }
}
```

---

## 🚀 Deployment & Environment Setup

### **Environment Variables**

```bash
# .env file for frontend development
REACT_APP_API_BASE_URL=https://your-api-gateway-url.amazonaws.com/dev
REACT_APP_WS_URL=wss://your-websocket-url.amazonaws.com
REACT_APP_AUTH_DOMAIN=your-auth-domain.com
REACT_APP_CLIENT_ID=your-client-id

# For production
REACT_APP_API_BASE_URL=https://api.petplantr.com
REACT_APP_WS_URL=wss://ws.petplantr.com
```

### **API Client Setup**

```typescript
// api-client.ts
class PetPlantrAPI {
  private baseURL: string;
  private headers: Record<string, string>;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_BASE_URL || '';
    this.headers = {
      'Content-Type': 'application/json',
    };
  }

  setAuthToken(token: string) {
    this.headers['Authorization'] = `Bearer ${token}`;
  }

  async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: this.headers,
      ...options,
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Farm API methods
  getFarmStatus() {
    return this.request('/api/farm/status');
  }

  getCustomerDashboard(customerId: string) {
    return this.request(`/api/farm/frontend?customerId=${customerId}`);
  }

  getLiveFarmData() {
    return this.request('/api/farm/live');
  }

  createJob(jobData: any) {
    return this.request('/api/farm/jobs', {
      method: 'POST',
      body: JSON.stringify(jobData),
    });
  }
}

export const apiClient = new PetPlantrAPI();
```

---

## 📊 Performance Optimization Tips

1. **Caching**: Implement client-side caching for farm status data
2. **Polling**: Use smart polling intervals (30s for live data, 5min for metrics)
3. **WebSocket**: Prefer WebSocket for real-time updates over polling
4. **Lazy Loading**: Load detailed printer data only when needed
5. **Error Boundaries**: Implement proper error handling for API failures

---

## 🛡️ Security Considerations

1. **Authentication**: Always include valid JWT tokens in requests
2. **Rate Limiting**: Respect API rate limits (documented in headers)
3. **CORS**: Ensure your domain is allowlisted for CORS
4. **Data Validation**: Validate all data on the frontend before sending
5. **Error Handling**: Don't expose sensitive error details to users

---

This enhanced backend provides everything needed for modern frontend development with PetPlantr's 3D printing farm management system. The API is designed to be frontend-friendly, performant, and scalable for both web and mobile applications.
