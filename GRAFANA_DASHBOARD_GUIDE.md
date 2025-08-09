# Task Management API - Grafana Dashboard Guide

## Accessing Grafana

1. **Open Grafana in your browser**: http://localhost:3000
2. **Login credentials**:
   - Username: `admin`
   - Password: `admin_change_me` (or your custom `GRAFANA_PASSWORD` from .env)

## Dashboard Overview

The **Task Management API Dashboard** provides comprehensive monitoring of your FastAPI application with the following panels:

### 📊 Key Metrics Panels

#### 1. **HTTP Request Rate**
- Shows requests per second over time
- Grouped by HTTP method and endpoint
- Helps identify traffic patterns and load

#### 2. **HTTP Status Codes**
- Distribution of response status codes (2xx, 4xx, 5xx)
- Quickly identify error rates
- Green = success, Yellow = client errors, Red = server errors

#### 3. **Average Response Time**
- Mean response time for each endpoint
- Tracks performance degradation
- Threshold: Green < 0.5s, Yellow < 1s, Red > 1s

#### 4. **Response Time P95**
- 95th percentile response time
- Shows worst-case performance for most users
- Better indicator of user experience than averages

#### 5. **Memory Usage**
- Resident and virtual memory usage
- Tracks memory leaks and optimization needs
- Important for container resource planning

#### 6. **CPU Usage**
- CPU utilization percentage
- Helps with capacity planning
- Threshold: Green < 70%, Yellow < 90%, Red > 90%

### 📈 Status Panels (Bottom Row)

#### 7. **API Uptime**
- Shows if the API is currently up (1) or down (0)
- Instant health status indicator

#### 8. **Current Request Rate**
- Real-time requests per second
- Single number showing current load

#### 9. **Current Response Time**
- Real-time average response time
- Performance at a glance

#### 10. **Success Rate**
- Percentage of non-5xx responses
- Service reliability indicator
- Target: > 99% (green)

## Using the Dashboard

### Time Range Selection
- Use the time picker (top right) to change the viewing window
- Default: Last 1 hour
- Common ranges: Last 5m, 15m, 1h, 6h, 24h

### Refresh Rate
- Auto-refresh is set to 5 seconds
- Can be changed in the refresh dropdown (top right)
- Use "5s" for real-time monitoring, "1m" for general monitoring

### Filtering and Drilling Down
- Click on legend items to show/hide specific metrics
- Use Ctrl+Click to isolate specific metrics
- Hover over panels for detailed tooltips

## Alerting (Advanced)

To set up alerts:

1. **Go to Alerting** → **Alert Rules**
2. **Create alerts for**:
   - High error rate: `> 5% 5xx responses`
   - High response time: `> 2 seconds P95`
   - Low success rate: `< 95% success rate`
   - High CPU usage: `> 80% for 5 minutes`

## Customization

### Adding New Panels
1. Click **"Add panel"** (top toolbar)
2. Select **"Add a new panel"**
3. Choose **prometheus** as data source
4. Write PromQL queries for your metrics

### Common Metrics to Add
- **Database connections**: `pg_stat_database_*` (if you add postgres_exporter)
- **Request size**: `http_request_size_bytes`
- **Active connections**: `uvicorn_active_connections`

### Useful PromQL Queries

```promql
# Error rate by endpoint
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])

# Request duration 99th percentile
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Requests per minute
increase(http_requests_total[1m])

# Memory usage percentage (if you know container limits)
process_resident_memory_bytes / (512 * 1024 * 1024) * 100
```

## Troubleshooting

### No Data Showing
1. **Check Prometheus connection**: Go to Data Sources → prometheus → Test
2. **Verify metrics endpoint**: Visit http://localhost:8000/metrics
3. **Check time range**: Ensure you're looking at a time range with data
4. **Generate traffic**: Make API calls to create metrics

### Dashboard Not Loading
1. **Restart Grafana**: `docker-compose -f docker-compose.prod.yml restart grafana`
2. **Check logs**: `docker-compose -f docker-compose.prod.yml logs grafana`
3. **Verify file permissions**: Ensure dashboard files are readable

### Metrics Missing
- Some metrics only appear after specific API calls
- Authentication metrics require login attempts
- Database metrics need database queries

## Dashboard Maintenance

### Regular Tasks
1. **Monitor disk usage**: Prometheus data grows over time
2. **Update retention**: Default is 30 days in prometheus.yml
3. **Backup dashboards**: Export dashboard JSON for version control
4. **Review alerts**: Adjust thresholds based on actual usage patterns

### Performance Optimization
- Use recording rules for complex queries
- Adjust scrape intervals for less critical metrics
- Use grafana variables for dynamic dashboards

## Getting Help

- **Grafana docs**: https://grafana.com/docs/
- **PromQL guide**: https://prometheus.io/docs/prometheus/latest/querying/
- **FastAPI metrics**: Check prometheus-fastapi-instrumentator docs

Enjoy monitoring your Task Management API! 📊🚀