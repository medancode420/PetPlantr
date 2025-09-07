# Docker Monitoring Setup Guide
## Enable Production-Grade Monitoring for PetPlantr

### 🚨 **Current Status:** Docker Daemon Not Running

**Issue:** Docker Desktop must be started to enable container monitoring
**Impact:** Missing cAdvisor metrics, container performance data
**Solution:** Start Docker Desktop and run monitoring stack

---

## 🐳 **Step 1: Start Docker Desktop**

### **On macOS:**
1. **Open Docker Desktop** from Applications folder
2. **Wait for Docker to start** (whale icon in menu bar)
3. **Verify Docker is running:**
   ```bash
   docker --version
   docker ps
   ```

### **Expected Output:**
```bash
Docker version 28.3.2, build 578ccf6
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

---

## 📊 **Step 2: Start Monitoring Stack**

Once Docker is running, execute:

```bash
cd /Users/medan/Downloads/PetPlantr
./start-monitoring.sh
```

### **Expected Services:**
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/admin)
- **Alertmanager:** http://localhost:9093
- **cAdvisor:** http://localhost:8080
- **Node Exporter:** http://localhost:9100

---

## 🎯 **Step 3: Configure Grafana Dashboards**

### **Access Grafana:**
1. Open http://localhost:3000
2. Login with `admin` / `admin`
3. Change password when prompted

### **Add Prometheus Data Source:**
1. **Configuration** → **Data Sources** → **Add data source**
2. **Select Prometheus**
3. **URL:** http://prometheus:9090
4. **Save & Test**

### **Import PetPlantr Dashboard:**
1. **Dashboards** → **Import**
2. **Upload JSON:** `monitoring/grafana/dashboards/petplantr-dashboard.json`
3. **Select Prometheus data source**
4. **Import**

---

## 📈 **Step 4: Verify Monitoring**

### **Check Service Health:**
```bash
# Test all monitoring endpoints
curl -f http://localhost:9090/-/healthy
curl -f http://localhost:3000/api/health
curl -f http://localhost:8080/containers/
curl -f http://localhost:9100/metrics
```

### **View Metrics:**
- **PetPlantr API:** http://localhost:9090/targets
- **System Metrics:** http://localhost:9100/metrics
- **Container Metrics:** http://localhost:8080/

---

## 🚨 **Step 5: Configure Alerts**

### **Alertmanager Configuration:**
```yaml
# monitoring/alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@petplantr.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email'
  routes:
  - match:
      severity: critical
    receiver: 'email'

receivers:
- name: 'email'
  email_configs:
  - to: 'admin@petplantr.com'
```

### **Prometheus Alert Rules:**
```yaml
# monitoring/prometheus/alerting-rules.yml
groups:
  - name: petplantr
    rules:
      - alert: HighResponseTime
        expr: rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API response time detected"
          description: "API response time is {{ $value }}s"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}%"
```

---

## 📊 **Step 6: Custom Dashboards**

### **PetPlantr Metrics to Monitor:**
- **API Response Time:** `http_request_duration_seconds`
- **Request Rate:** `http_requests_total`
- **Error Rate:** `http_requests_total{status=~"5.."}`
- **Model Inference Time:** `petplantr_inference_duration_seconds`
- **Memory Usage:** `process_resident_memory_bytes`
- **CPU Usage:** `process_cpu_user_seconds_total`

### **System Metrics:**
- **Container CPU:** `container_cpu_usage_seconds_total`
- **Container Memory:** `container_memory_usage_bytes`
- **Disk I/O:** `container_fs_reads_bytes_total`
- **Network I/O:** `container_network_receive_bytes_total`

---

## 🔧 **Step 7: Production Integration**

### **Update Production Scripts:**
```bash
# Add to production deployment
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Health checks
curl -f http://localhost:9090/-/healthy
curl -f http://localhost:3000/api/health
```

### **Environment Variables:**
```bash
# .env.production
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
ALERTMANAGER_URL=http://alertmanager:9093
```

---

## 🎯 **Step 8: Monitoring Dashboard**

### **Streamlit Dashboard:**
```bash
cd /Users/medan/Downloads/PetPlantr
streamlit run monitoring-dashboard.py
```

### **Features:**
- **Real-time Metrics:** API performance, system resources
- **Alert Status:** Active alerts and resolutions
- **Container Health:** Docker container monitoring
- **ML Pipeline:** Model performance metrics
- **Historical Trends:** Performance over time

---

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **Docker Not Starting:**
```bash
# Check Docker Desktop
ps aux | grep Docker
# Restart Docker Desktop
```

#### **Port Conflicts:**
```bash
# Check port usage
lsof -i :9090
lsof -i :3000
# Kill conflicting processes
kill -9 <PID>
```

#### **Permission Issues:**
```bash
# Fix Docker permissions
sudo chown -R $USER ~/.docker
```

#### **Grafana Login Issues:**
```bash
# Reset Grafana admin password
docker exec -it petplantr_grafana grafana-cli admin reset-admin-password admin
```

---

## 📈 **Next Steps**

### **Immediate (Today):**
1. ✅ Start Docker Desktop
2. ✅ Run `./start-monitoring.sh`
3. ✅ Configure Grafana dashboards
4. ✅ Test all monitoring endpoints

### **Short-term (This Week):**
1. ⏳ Set up email alerts
2. ⏳ Create custom dashboards
3. ⏳ Configure production integration
4. ⏳ Test monitoring in production

### **Long-term (This Month):**
1. ⏳ Implement advanced alerting
2. ⏳ Set up log aggregation
3. ⏳ Configure automated scaling
4. ⏳ Implement anomaly detection

---

## 🎉 **Success Criteria**

- ✅ **Docker monitoring stack running**
- ✅ **Grafana dashboards configured**
- ✅ **Prometheus collecting metrics**
- ✅ **Alertmanager configured**
- ✅ **All services healthy**
- ✅ **Production integration ready**

---

**🚀 Ready to enable enterprise-grade monitoring for PetPlantr!**

*Last Updated: September 6, 2025*
