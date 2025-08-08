# Task Management API - Production Deployment Guide

## Overview

This guide covers deploying the Task Management API to production using Docker and Docker Compose with PostgreSQL, Redis, Nginx, and monitoring.

## Prerequisites

- Docker and Docker Compose installed
- Domain name with SSL certificate
- At least 2GB RAM and 2 CPU cores
- PostgreSQL 15+ (or use included Docker PostgreSQL)

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd task-api

# Copy and configure environment variables
cp .env.example .env
nano .env
```

### 2. Configure Environment Variables

Update `.env` with production values:

```bash
# Application
APP_NAME="Task Management API"
DEBUG=false
LOG_LEVEL=INFO

# Database (PostgreSQL)
DATABASE_URL=postgresql://taskapi_user:secure_password@db:5432/taskapi
POSTGRES_DB=taskapi
POSTGRES_USER=taskapi_user
POSTGRES_PASSWORD=your_secure_database_password_here

# Security (CRITICAL: Change these!)
SECRET_KEY=$(openssl rand -hex 32)
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (Update with your domains)
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Monitoring
GRAFANA_PASSWORD=your_secure_grafana_password
```

### 3. SSL Certificate Setup

Place your SSL certificates in `nginx/ssl/`:

```bash
mkdir -p nginx/ssl
# Copy your certificate files
cp /path/to/your/cert.pem nginx/ssl/cert.pem
cp /path/to/your/private.key nginx/ssl/key.pem
```

Or generate self-signed certificates for testing:

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=localhost"
```

### 4. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

### 5. Database Migration

```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### 6. Verify Deployment

```bash
# Check health endpoints
curl -k https://localhost/health
curl -k https://localhost/health/ready

# Test API endpoints
curl -k https://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","username":"admin","password":"securepass123"}'
```

## Service Architecture

### Services Included

1. **FastAPI Application** (Port 8000)
   - Main API service
   - JWT authentication
   - Rate limiting
   - Health checks

2. **PostgreSQL Database** (Port 5432)
   - Primary data storage
   - Persistent volumes
   - Health monitoring

3. **Redis Cache** (Port 6379)
   - Session storage (future)
   - Rate limiting storage
   - Caching layer

4. **Nginx Reverse Proxy** (Ports 80/443)
   - SSL termination
   - Load balancing
   - Rate limiting
   - Security headers

5. **Prometheus** (Port 9090)
   - Metrics collection
   - API monitoring
   - Performance tracking

6. **Grafana** (Port 3000)
   - Metrics visualization
   - Dashboards
   - Alerting

## Configuration Details

### Production Security

```bash
# Generate secure secrets
export SECRET_KEY=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)
export GRAFANA_PASSWORD=$(openssl rand -base64 16)

# Update .env with these values
echo "SECRET_KEY=$SECRET_KEY" >> .env
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> .env
echo "REDIS_PASSWORD=$REDIS_PASSWORD" >> .env  
echo "GRAFANA_PASSWORD=$GRAFANA_PASSWORD" >> .env
```

### CORS Configuration

Update CORS origins for your frontend domains:

```bash
# Single domain
CORS_ORIGINS=["https://yourdomain.com"]

# Multiple domains
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com","https://admin.yourdomain.com"]
```

### Resource Limits

The Docker Compose configuration includes resource limits:

- **API Service**: 512M RAM, 0.5 CPU
- **Database**: Default limits (adjust based on load)
- **Redis**: Default limits (lightweight)

## Monitoring and Maintenance

### Access Monitoring

- **Grafana Dashboard**: https://localhost:3000 (admin/your_grafana_password)
- **Prometheus**: https://localhost:9090
- **API Documentation**: https://localhost/docs

### Log Management

```bash
# View API logs
docker-compose -f docker-compose.prod.yml logs -f api

# View all service logs
docker-compose -f docker-compose.prod.yml logs -f

# View database logs
docker-compose -f docker-compose.prod.yml logs -f db
```

### Database Backup

```bash
# Create database backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U taskapi_user taskapi > backup.sql

# Restore database backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U taskapi_user taskapi < backup.sql
```

### Health Monitoring

Monitor these endpoints:

- `GET /health` - Overall health status
- `GET /health/live` - Kubernetes liveness probe
- `GET /health/ready` - Kubernetes readiness probe

## Scaling and Performance

### Horizontal Scaling

To scale the API service:

```bash
# Scale to 3 API instances
docker-compose -f docker-compose.prod.yml up -d --scale api=3
```

### Database Optimization

For high-traffic applications:

1. **Connection Pooling**: Already configured in SQLAlchemy
2. **Read Replicas**: Add read-only database replicas
3. **Caching**: Implement Redis caching for frequent queries
4. **Indexing**: Add database indexes for common queries

### Performance Monitoring

Key metrics to monitor:

- Response times (< 200ms for most endpoints)
- Database connection pool usage
- Memory usage (should stay under 80% of allocated)
- CPU usage (should stay under 70% average)

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   ```bash
   # Check certificate validity
   openssl x509 -in nginx/ssl/cert.pem -text -noout
   ```

2. **Database Connection Issues**
   ```bash
   # Check database connectivity
   docker-compose -f docker-compose.prod.yml exec api python -c "from app.database import engine; engine.connect()"
   ```

3. **Rate Limiting Issues**
   ```bash
   # Check Nginx error logs
   docker-compose -f docker-compose.prod.yml logs nginx
   ```

### Recovery Procedures

1. **Service Recovery**
   ```bash
   # Restart all services
   docker-compose -f docker-compose.prod.yml restart
   
   # Restart specific service
   docker-compose -f docker-compose.prod.yml restart api
   ```

2. **Database Recovery**
   ```bash
   # Restore from backup
   docker-compose -f docker-compose.prod.yml stop api
   docker-compose -f docker-compose.prod.yml exec -T db psql -U taskapi_user taskapi < backup.sql
   docker-compose -f docker-compose.prod.yml start api
   ```

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong SSL certificates
- [ ] Configure proper CORS origins
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security updates
- [ ] Database backups configured
- [ ] Log monitoring in place
- [ ] Network security groups configured
- [ ] Regular vulnerability scanning

## Maintenance Tasks

### Daily
- Monitor service health
- Check error logs
- Verify backup completion

### Weekly  
- Review performance metrics
- Update security patches
- Test backup restoration

### Monthly
- Security audit
- Performance optimization
- Dependency updates
- Capacity planning review

## Support

For issues and questions:

1. Check service logs first
2. Verify configuration settings
3. Test connectivity between services
4. Review monitoring dashboards
5. Check resource usage

For additional help, refer to the main documentation in `README.md` and `CLAUDE.md`.