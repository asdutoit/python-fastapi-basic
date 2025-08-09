#!/bin/bash

# Apigee Deployment Script for Task Management API
# Usage: ./deploy.sh [environment] [organization]

set -e

# Configuration
PROXY_NAME="task-management-api"
APIGEE_ORG=${2:-"your-org"}
APIGEE_ENV=${1:-"test"}
BACKEND_URL=${BACKEND_URL:-"https://your-backend-url.com"}

echo "🚀 Deploying Task Management API to Apigee..."
echo "Organization: $APIGEE_ORG"
echo "Environment: $APIGEE_ENV"
echo "Backend URL: $BACKEND_URL"

# Check if apigeetool is installed
if ! command -v apigeetool &> /dev/null; then
    echo "❌ apigeetool is not installed. Installing..."
    npm install -g apigeetool
fi

# Check authentication
if [[ -z "$APIGEE_USERNAME" || -z "$APIGEE_PASSWORD" ]]; then
    echo "❌ Please set APIGEE_USERNAME and APIGEE_PASSWORD environment variables"
    exit 1
fi

# Update target URL in the configuration
sed -i.bak "s|https://your-fastapi-backend.com|$BACKEND_URL|g" apiproxy/targets/task-api-backend.xml

# Create API proxy bundle
echo "📦 Creating API proxy bundle..."
cd apiproxy
zip -r "../${PROXY_NAME}.zip" . -x "*.DS_Store"
cd ..

# Deploy to Apigee
echo "🌐 Deploying to Apigee..."
apigeetool deployproxy \
    -u "$APIGEE_USERNAME" \
    -p "$APIGEE_PASSWORD" \
    -o "$APIGEE_ORG" \
    -e "$APIGEE_ENV" \
    -n "$PROXY_NAME" \
    -d "./apiproxy"

# Create API Product
echo "📋 Creating API Product..."
apigeetool createProduct \
    -u "$APIGEE_USERNAME" \
    -p "$APIGEE_PASSWORD" \
    -o "$APIGEE_ORG" \
    -f "task-management-product" \
    -d "Task Management API Product" \
    -p "$PROXY_NAME" \
    -e "$APIGEE_ENV" \
    -a "read,write,admin" \
    -s "approved"

# Create Developer
echo "👨‍💻 Creating Developer..."
apigeetool createDeveloper \
    -u "$APIGEE_USERNAME" \
    -p "$APIGEE_PASSWORD" \
    -o "$APIGEE_ORG" \
    -e "api-developer@example.com" \
    -f "API" \
    -s "Developer"

# Create App
echo "📱 Creating Developer App..."
apigeetool createApp \
    -u "$APIGEE_USERNAME" \
    -p "$APIGEE_PASSWORD" \
    -o "$APIGEE_ORG" \
    -e "api-developer@example.com" \
    -f "task-management-app" \
    -d "Task Management Application" \
    -p "task-management-product"

# Get the API key
echo "🔑 Retrieving API Key..."
API_KEY=$(apigeetool getApp \
    -u "$APIGEE_USERNAME" \
    -p "$APIGEE_PASSWORD" \
    -o "$APIGEE_ORG" \
    -e "api-developer@example.com" \
    -f "task-management-app" | jq -r '.credentials[0].consumerKey')

# Restore original configuration
mv apiproxy/targets/task-api-backend.xml.bak apiproxy/targets/task-api-backend.xml

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📝 API Details:"
echo "  Proxy URL: https://$APIGEE_ORG-$APIGEE_ENV.apigee.net/task-api/v1"
echo "  API Key: $API_KEY"
echo "  Documentation: https://$APIGEE_ORG-$APIGEE_ENV.apigee.net/task-api/v1/docs"
echo ""
echo "🧪 Test your API:"
echo "  curl -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\"
echo "       'https://$APIGEE_ORG-$APIGEE_ENV.apigee.net/task-api/v1/health?apikey=$API_KEY'"
echo ""
echo "🔧 Next steps:"
echo "  1. Update your frontend to use the Apigee proxy URL"
echo "  2. Configure JWT secret in Apigee encrypted KVMs"
echo "  3. Set up monitoring and analytics in Apigee console"
echo "  4. Configure custom domains and SSL certificates"

# Clean up
rm -f "${PROXY_NAME}.zip"

echo "🎉 Done!"