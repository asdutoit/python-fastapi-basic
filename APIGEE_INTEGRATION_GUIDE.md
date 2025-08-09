# Google Apigee Integration Guide
## Task Management API - FastAPI to Apigee

This guide provides comprehensive instructions for integrating your Task Management FastAPI with Google Apigee API Gateway.

## 🎯 Overview

Google Apigee provides enterprise-grade API management with features like:
- **API Proxy Management** - Route and transform requests
- **Authentication & Authorization** - JWT verification, API keys, OAuth
- **Rate Limiting & Quotas** - Protect your backend from abuse
- **Analytics & Monitoring** - Track API usage and performance
- **Developer Portal** - Self-service API documentation
- **Security Policies** - CORS, threat protection, data masking

## 📋 Prerequisites

1. **Google Cloud Account** with Apigee enabled
2. **Apigee Organization** (trial or paid)
3. **FastAPI Backend** deployed and accessible
4. **Node.js** (for deployment scripts)
5. **apigeetool** CLI tool

## 🛠️ Installation & Setup

### 1. Install Required Tools

```bash
# Install Node.js dependencies
cd apigee/
npm install

# Install Apigee CLI tool globally
npm install -g apigeetool
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.template .env

# Edit configuration
nano .env
```

Required environment variables:
```bash
APIGEE_ORG=your-apigee-organization
APIGEE_ENV=test
APIGEE_USERNAME=your-apigee-username
APIGEE_PASSWORD=your-apigee-password
BACKEND_URL=https://your-fastapi-backend.com
JWT_SECRET_KEY=your-jwt-secret-key-must-match-fastapi
```

### 3. Update Backend URL

Update the target endpoint in `apiproxy/targets/task-api-backend.xml`:
```xml
<URL>https://your-actual-fastapi-backend.com</URL>
```

## 🚀 Deployment

### Automated Deployment

```bash
# Deploy to test environment
./deploy.sh test your-org

# Deploy to production
./deploy.sh prod your-org
```

### Manual Deployment Steps

1. **Create API Proxy**
   ```bash
   apigeetool deployproxy \
     -u $APIGEE_USERNAME -p $APIGEE_PASSWORD \
     -o $APIGEE_ORG -e $APIGEE_ENV \
     -n task-management-api \
     -d ./apiproxy
   ```

2. **Create API Product**
   ```bash
   apigeetool createProduct \
     -u $APIGEE_USERNAME -p $APIGEE_PASSWORD \
     -o $APIGEE_ORG \
     -f task-management-product \
     -d "Task Management API Product" \
     -p task-management-api \
     -e $APIGEE_ENV
   ```

3. **Create Developer & App**
   ```bash
   # Create developer
   apigeetool createDeveloper \
     -u $APIGEE_USERNAME -p $APIGEE_PASSWORD \
     -o $APIGEE_ORG \
     -e api-developer@example.com \
     -f API -s Developer

   # Create app
   apigeetool createApp \
     -u $APIGEE_USERNAME -p $APIGEE_PASSWORD \
     -o $APIGEE_ORG \
     -e api-developer@example.com \
     -f task-management-app \
     -p task-management-product
   ```

## 🔧 Configuration Details

### API Proxy Structure

```
apiproxy/
├── task-management-api.xml    # Main proxy definition
├── proxies/
│   └── default.xml            # Proxy endpoint with flows
├── targets/
│   └── task-api-backend.xml   # Target endpoint configuration
├── policies/                  # Policy definitions
│   ├── JWT-Verify.xml         # JWT token verification
│   ├── CORS-Policy.xml        # CORS handling
│   ├── Rate-Limiting.xml      # Rate limiting
│   ├── Spike-Arrest.xml       # Spike arrest protection
│   └── ...more policies
└── resources/
    └── node/
        └── openapi-spec.json  # API specification
```

### Request Flow

1. **Client Request** → Apigee Proxy
2. **API Key Verification** (query parameter `?apikey=xxx`)
3. **CORS Headers** added for browser requests
4. **Rate Limiting** applied per client
5. **JWT Verification** for protected endpoints
6. **Request Forwarding** to FastAPI backend
7. **Response Transformation** and header cleanup
8. **CORS Headers** added to response

### Endpoint Routing

| Original FastAPI Path | Apigee Proxy Path | Authentication |
|-----------------------|-------------------|----------------|
| `/health` | `/task-api/v1/health` | API Key only |
| `/api/v1/auth/*` | `/task-api/v1/api/v1/auth/*` | API Key only |
| `/api/v1/tasks/*` | `/task-api/v1/api/v1/tasks/*` | API Key + JWT |
| `/docs` | `/task-api/v1/docs` | API Key only |

## 🔐 Security Configuration

### JWT Verification

The proxy verifies JWT tokens for protected endpoints:

```xml
<VerifyJWT name="JWT-Verify">
    <Algorithm>HS256</Algorithm>
    <Source>request.header.authorization</Source>
    <SecretKey>
        <Value ref="jwt.secret.key"/>
    </SecretKey>
    <!-- Claims extraction -->
    <AdditionalClaims>
        <Claim name="user_id" ref="jwt.claim.user_id"/>
        <Claim name="email" ref="jwt.claim.email"/>
    </AdditionalClaims>
</VerifyJWT>
```

### API Key Management

Each client application requires an API key:
- Obtained from Apigee Developer Portal
- Passed as query parameter: `?apikey=your-key`
- Used for rate limiting and analytics

### Rate Limiting

Two levels of protection:
1. **Quota Policy** - 100 requests per minute per API key
2. **Spike Arrest** - Maximum 10 requests per second burst

## 📊 Monitoring & Analytics

### Apigee Analytics

Access analytics in the Apigee console:
- **Traffic Analysis** - Request volume, response times
- **Error Analysis** - 4xx/5xx error rates and patterns
- **Developer Analytics** - Usage by API key/developer
- **Geo Analytics** - Request origins and locations

### Integration with Existing Monitoring

Your existing observability stack (Prometheus/Grafana) will continue monitoring the backend. Apigee provides additional API gateway metrics.

### Custom Metrics

Add custom analytics policies:
```xml
<StatisticsCollector name="Collect-Custom-Stats">
    <Statistics>
        <Statistic name="user_requests" ref="jwt.claim.user_id"/>
        <Statistic name="endpoint_usage" ref="request.uri"/>
    </Statistics>
</StatisticsCollector>
```

## 🧪 Testing

### Automated Testing

```bash
# Set your API key
export API_KEY=your-generated-api-key

# Run tests
node test-proxy.js
```

### Manual Testing

1. **Health Check**
   ```bash
   curl "https://your-org-test.apigee.net/task-api/v1/health?apikey=YOUR_KEY"
   ```

2. **User Registration**
   ```bash
   curl -X POST "https://your-org-test.apigee.net/task-api/v1/api/v1/auth/register?apikey=YOUR_KEY" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","username":"testuser","password":"testpass123"}'
   ```

3. **User Login**
   ```bash
   curl -X POST "https://your-org-test.apigee.net/task-api/v1/api/v1/auth/login?apikey=YOUR_KEY" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=testuser&password=testpass123"
   ```

4. **Protected Endpoint**
   ```bash
   curl "https://your-org-test.apigee.net/task-api/v1/api/v1/tasks?apikey=YOUR_KEY" \
        -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

## 🚦 Environment Management

### Test Environment

- **URL**: `https://your-org-test.apigee.net/task-api/v1`
- **Purpose**: Development and testing
- **Rate Limits**: Relaxed for testing
- **Backend**: Test instance of FastAPI

### Production Environment

- **URL**: `https://your-org-prod.apigee.net/task-api/v1`
- **Purpose**: Live production traffic
- **Rate Limits**: Strict production limits
- **Backend**: Production FastAPI instance
- **SSL**: Custom domain with SSL certificate

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Apigee
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: cd apigee && npm install
        
      - name: Deploy to Apigee
        env:
          APIGEE_USERNAME: ${{ secrets.APIGEE_USERNAME }}
          APIGEE_PASSWORD: ${{ secrets.APIGEE_PASSWORD }}
          APIGEE_ORG: ${{ secrets.APIGEE_ORG }}
        run: cd apigee && ./deploy.sh prod $APIGEE_ORG
```

## 🛡️ Security Best Practices

### 1. JWT Secret Management

- Store JWT secrets in Apigee Encrypted KVMs
- Rotate secrets regularly
- Use different secrets for test/prod

### 2. API Key Security

- Enable API key rotation
- Set expiration dates for keys
- Monitor key usage for anomalies

### 3. Network Security

- Use HTTPS only (enforce in policies)
- Implement IP restrictions if needed
- Enable threat protection policies

### 4. CORS Configuration

- Restrict origins to known domains
- Avoid wildcard (`*`) in production
- Configure appropriate headers

## 🐛 Troubleshooting

### Common Issues

1. **JWT Verification Fails**
   - Check secret key matches FastAPI configuration
   - Verify token format and claims
   - Check token expiration

2. **CORS Issues**
   - Verify origin headers in requests
   - Check preflight response headers
   - Ensure CORS policy is applied to all flows

3. **Rate Limiting Too Strict**
   - Adjust quota policies
   - Check spike arrest configuration
   - Monitor analytics for usage patterns

4. **Backend Connection Issues**
   - Verify target URL is correct and accessible
   - Check SSL certificates for HTTPS
   - Review health monitoring configuration

### Debug Steps

1. **Check Apigee Trace**
   - Use Apigee console trace tool
   - Monitor request/response flow
   - Identify policy failures

2. **Review Logs**
   - Check Apigee system logs
   - Review custom logging policies
   - Monitor backend application logs

3. **Test Policies Individually**
   - Temporarily disable policies
   - Test flows step by step
   - Validate policy configurations

## 📈 Scaling & Performance

### Backend Scaling

- Configure load balancer as target
- Use target server groups for multiple backends
- Implement health checks and failover

### Apigee Scaling

- Apigee automatically scales proxy traffic
- Monitor quotas and adjust as needed
- Use caching policies for frequently accessed data

### Performance Optimization

1. **Response Caching**
   ```xml
   <ResponseCache name="Cache-GET-Responses">
       <CacheKey>
           <KeyFragment ref="request.uri"/>
           <KeyFragment ref="request.header.authorization"/>
       </CacheKey>
       <ExpirySettings>
           <TimeoutInSec>300</TimeoutInSec>
       </ExpirySettings>
   </ResponseCache>
   ```

2. **Backend Connection Pooling**
   ```xml
   <HTTPTargetConnection>
       <MaxConnections>50</MaxConnections>
       <ConnectionTimeoutMs>30000</ConnectionTimeoutMs>
   </HTTPTargetConnection>
   ```

## 🎯 Next Steps

After successful deployment:

1. **Update Frontend Applications**
   - Change API base URL to Apigee proxy
   - Include API key in all requests
   - Handle rate limiting responses

2. **Configure Custom Domains**
   - Set up custom domain in Apigee
   - Configure SSL certificates
   - Update DNS records

3. **Set Up Monitoring**
   - Configure alerting rules
   - Set up dashboards for API metrics
   - Integrate with existing monitoring

4. **Developer Portal**
   - Publish APIs to developer portal
   - Create documentation and guides
   - Manage developer registration

5. **Advanced Policies**
   - Implement data transformation
   - Add threat protection
   - Configure OAuth/OIDC if needed

## 📚 Additional Resources

- [Apigee Documentation](https://docs.apigee.com/)
- [Apigee Policy Reference](https://docs.apigee.com/api-platform/reference/policies/)
- [OpenAPI with Apigee](https://docs.apigee.com/api-platform/openapi/openapi-overview)
- [Apigee Best Practices](https://docs.apigee.com/api-platform/fundamentals/best-practices-api-proxy-design-and-development)

## 🆘 Support

For issues and questions:
1. Check Apigee Community forums
2. Review trace logs in Apigee console
3. Contact your Apigee support team
4. Reference this documentation and test scripts

---

🎉 **Congratulations!** Your Task Management API is now enterprise-ready with Google Apigee integration, providing robust API management, security, and analytics capabilities.