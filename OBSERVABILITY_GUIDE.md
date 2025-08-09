# Task Management API - Complete Observability Guide

## 🔭 Three Pillars of Observability

Your Task Management API now has complete observability with the **Three Pillars**:

1. **📊 Metrics** - Quantitative data (Prometheus + Grafana)
2. **📝 Logs** - Event records (Loki + Promtail + Grafana)  
3. **🔍 Traces** - Request journey (Jaeger + OpenTelemetry + Grafana)

## 🌐 Access Points

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Grafana** | http://localhost:3000 | admin / admin_change_me | Unified dashboard for metrics, logs, traces |
| **Prometheus** | http://localhost:9090 | - | Metrics storage and querying |
| **Loki** | http://localhost:3100 | - | Log aggregation and querying |
| **Jaeger UI** | http://localhost:16686 | - | Distributed tracing interface |
| **API Docs** | https://localhost/docs | - | FastAPI Swagger documentation |

## 📊 Metrics (Prometheus + Grafana)

### Available Dashboards
- **Task Management API Dashboard** - Main metrics dashboard
  - HTTP request rates and response times
  - Status code distributions  
  - Memory and CPU usage
  - Real-time health indicators

### Key Metrics
```promql
# Request rate
rate(http_requests_total[5m])

# Response time percentiles
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])

# Memory usage
process_resident_memory_bytes

# CPU usage
rate(process_cpu_seconds_total[5m]) * 100
```

## 📝 Logs (Loki + Promtail + Grafana)

### Available Dashboards  
- **Task API - Logs Dashboard** - Comprehensive log analysis
  - Live log stream
  - Log volume by level
  - Error rate tracking
  - Recent errors and HTTP requests

### Log Structure
Our application uses structured JSON logging:

```json
{
  "timestamp": "2025-01-08T19:30:45.123Z",
  "level": "INFO",
  "logger": "app.api.tasks",
  "message": "Task created successfully",
  "module": "tasks", 
  "function": "create_task",
  "line": 45,
  "service": "task-api",
  "version": "1.0.0",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "request_id": "req-456",
  "method": "POST",
  "url": "/api/v1/tasks/",
  "status_code": 201,
  "duration": 0.045
}
```

### LogQL Queries
```logql
# All API logs
{job="containerlogs"} |~ "taskapi-app"

# Error logs only
{job="containerlogs"} |~ "taskapi-app" | json | level="ERROR"

# HTTP requests with status codes
{job="containerlogs"} |~ "taskapi-app" | json | status_code != ""

# Slow requests (>1 second)
{job="containerlogs"} |~ "taskapi-app" | json | duration > 1.0

# Logs for specific user
{job="containerlogs"} |~ "taskapi-app" | json | user_id="user-123"

# Authentication failures
{job="containerlogs"} |~ "taskapi-app" | json | message =~ "Authentication.*failed"
```

## 🔍 Traces (Jaeger + OpenTelemetry)

### Automatic Instrumentation
The following components are automatically traced:
- **FastAPI** - All HTTP requests
- **SQLAlchemy** - Database queries  
- **Redis** - Cache operations
- **HTTP requests** - Outbound calls

### Trace Information
Each trace includes:
- **Span duration** - How long each operation took
- **Service name** - task-api  
- **Operation name** - HTTP method + endpoint
- **Tags** - HTTP status, method, URL, user ID
- **Error details** - Exception info if errors occur

### Viewing Traces
1. **From Logs** - Click trace IDs in log messages (if enabled)
2. **Direct Jaeger** - Browse http://localhost:16686
3. **Grafana** - Use Jaeger data source for correlation

### Trace Queries
In Jaeger UI:
- **Service**: `task-api`
- **Operation**: `POST /api/v1/tasks/`
- **Tags**: `http.status_code=500` (find errors)
- **Tags**: `user.id=user-123` (user-specific traces)

## 🔗 Correlation Between Pillars

### Metrics → Logs
1. See high error rate in metrics dashboard
2. Click time range to filter
3. Switch to logs dashboard  
4. View error logs from same time period

### Logs → Traces  
1. Find error in logs dashboard
2. Extract trace ID from log message
3. Search trace ID in Jaeger
4. Analyze full request journey

### Traces → Metrics
1. Identify slow operation in trace
2. Note the service/endpoint
3. Create custom metric query for that endpoint
4. Set up alerting for performance regression

## 🚨 Alerting Setup

### Recommended Alerts

#### High Error Rate
```yaml
# Alert if >5% error rate for 5 minutes
- alert: HighErrorRate
  expr: rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100 > 5
  for: 5m
```

#### High Response Time  
```yaml
# Alert if P95 response time >2 seconds
- alert: HighResponseTime
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
```

#### Log Error Spike
```yaml  
# Alert on sudden increase in error logs
- alert: LogErrorSpike
  expr: increase(loki_ingester_log_entries_total{level="error"}[5m]) > 10
  for: 2m
```

## 🔧 Development & Debugging

### Local Development
- **Tracing disabled** in debug mode (performance impact)
- **Structured logging enabled** for consistency
- **Metrics always enabled** for development insights

### Production Troubleshooting

#### Performance Issues
1. **Check metrics** - Identify slow endpoints
2. **View traces** - Find bottleneck operations  
3. **Analyze logs** - Look for error patterns
4. **Correlate timeline** - Match events across all three pillars

#### Error Investigation
1. **Metrics** - When did errors start?
2. **Logs** - What are the error messages?
3. **Traces** - Which component failed?
4. **Correlation** - Are errors clustered by user/time/endpoint?

### Custom Instrumentation

#### Adding Custom Metrics
```python
from prometheus_client import Counter, Histogram

# Custom counters
task_created_total = Counter('task_created_total', 'Total tasks created')
task_created_total.inc()
```

#### Adding Custom Traces
```python  
from app.core.tracing import trace_function, get_tracer

@trace_function("custom_operation")
def my_function():
    # Automatically traced
    pass

# Manual tracing
tracer = get_tracer(__name__)
with tracer.start_as_current_span("manual_operation") as span:
    span.set_attribute("custom.attribute", "value")
    # Your code here
```

#### Adding Custom Logs
```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Structured logging with extra context
logger.info(
    "Custom event occurred",
    extra={
        "user_id": user_id,
        "operation": "custom_op",  
        "duration": 0.123,
        "custom_field": "value"
    }
)
```

## 📈 Performance Optimization

### Using Observability Data

#### Identify Bottlenecks
1. **Traces** - Find slowest spans
2. **Metrics** - Confirm with P95/P99 data
3. **Logs** - Look for related errors/warnings

#### Database Optimization
1. **Trace SQL queries** - Find slow queries
2. **Log query patterns** - Identify N+1 problems  
3. **Metric database connections** - Monitor pool usage

#### API Optimization
1. **Endpoint metrics** - Find slowest routes
2. **Request tracing** - Analyze request flow
3. **Error logs** - Fix reliability issues

## 🏗️ Infrastructure Monitoring

### Container Health
```promql
# Container uptime
up{job="task-api"}

# Container restarts  
increase(container_start_time_seconds[1h])

# Memory usage percentage
process_resident_memory_bytes / container_spec_memory_limit_bytes * 100
```

### Service Dependencies
- **Database connections** - Monitor PostgreSQL metrics
- **Redis performance** - Track cache hit rates
- **Network latency** - Measure request/response times

## 🔒 Security Monitoring

### Authentication Events
```logql
# Failed logins
{job="containerlogs"} |~ "taskapi-app" | json | message =~ "Authentication.*failed"

# Suspicious activity
{job="containerlogs"} |~ "taskapi-app" | json | message =~ "suspicious.*activity"
```

### Rate Limiting
```promql  
# Rate limit hits
rate(http_requests_total{status_code="429"}[5m])
```

## 📚 Best Practices

### Log Levels
- **DEBUG** - Development only, very verbose
- **INFO** - Normal operations, business events  
- **WARN** - Recoverable issues, degraded performance
- **ERROR** - Application errors requiring attention
- **CRITICAL** - System-level failures

### Trace Sampling
- **Development** - 100% sampling
- **Production** - 10-20% sampling for performance
- **High-traffic** - 1-5% sampling, focus on errors

### Metric Cardinality
- **Avoid high-cardinality labels** (user IDs, timestamps)
- **Use meaningful labels** (endpoint, status, method)
- **Pre-aggregate when possible** (rate, histogram)

## 🚀 Getting Started Checklist

1. **✅ Start services**: `docker-compose -f docker-compose.prod.yml up -d`
2. **✅ Open Grafana**: http://localhost:3000 (admin/admin_change_me)  
3. **✅ Check dashboards**: Task API Dashboard + Logs Dashboard
4. **✅ Generate traffic**: Make some API calls
5. **✅ View traces**: http://localhost:16686
6. **✅ Explore logs**: Use Loki queries in Grafana
7. **✅ Set up alerts**: Create alerting rules
8. **✅ Customize**: Add your own metrics/logs/traces

## 🆘 Troubleshooting

### No Metrics Data
- Check Prometheus targets: http://localhost:9090/targets
- Verify API `/metrics` endpoint: http://localhost:8000/metrics
- Ensure containers are healthy: `docker ps`

### No Log Data  
- Check Promtail status: `docker logs taskapi-promtail`
- Verify Loki connection: http://localhost:3100/ready
- Check log volume mounts in docker-compose

### No Trace Data
- Verify Jaeger UI: http://localhost:16686
- Check OTLP endpoint configuration
- Ensure tracing is enabled (production mode only)
- Look for OpenTelemetry errors in application logs

### Service Discovery Issues
```bash
# Check network connectivity
docker-compose -f docker-compose.prod.yml exec grafana ping prometheus
docker-compose -f docker-compose.prod.yml exec grafana ping loki
docker-compose -f docker-compose.prod.yml exec grafana ping jaeger
```

---

🎉 **Congratulations!** You now have complete observability for your Task Management API. You can monitor, debug, and optimize your application with confidence using metrics, logs, and traces working together! 

For questions or advanced configurations, refer to the official documentation:
- [Grafana Docs](https://grafana.com/docs/)
- [Prometheus Docs](https://prometheus.io/docs/)  
- [Loki Docs](https://grafana.com/docs/loki/)
- [Jaeger Docs](https://www.jaegertracing.io/docs/)
- [OpenTelemetry Docs](https://opentelemetry.io/docs/)