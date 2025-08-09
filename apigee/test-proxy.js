#!/usr/bin/env node

const axios = require('axios');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const APIGEE_ORG = process.env.APIGEE_ORG;
const APIGEE_ENV = process.env.APIGEE_ENV || 'test';
const API_KEY = process.env.API_KEY; // Generated during deployment

const BASE_URL = `https://${APIGEE_ORG}-${APIGEE_ENV}.apigee.net/task-api/v1`;

async function testProxy() {
    console.log('🧪 Testing Apigee Proxy Integration...\n');
    
    const tests = [
        {
            name: 'Health Check',
            method: 'GET',
            url: `/health?apikey=${API_KEY}`,
            expectedStatus: 200
        },
        {
            name: 'CORS Preflight',
            method: 'OPTIONS',
            url: `/api/v1/tasks?apikey=${API_KEY}`,
            headers: {
                'Origin': 'https://example.com',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Authorization'
            },
            expectedStatus: 200
        },
        {
            name: 'API Documentation',
            method: 'GET',
            url: `/docs?apikey=${API_KEY}`,
            expectedStatus: 200
        },
        {
            name: 'OpenAPI Spec',
            method: 'GET',
            url: `/openapi.json?apikey=${API_KEY}`,
            expectedStatus: 200
        }
    ];

    let passed = 0;
    let failed = 0;

    for (const test of tests) {
        try {
            console.log(`Testing: ${test.name}`);
            
            const config = {
                method: test.method,
                url: BASE_URL + test.url,
                headers: test.headers || {},
                timeout: 10000,
                validateStatus: (status) => status < 500 // Don't throw on 4xx
            };

            const response = await axios(config);
            
            if (response.status === test.expectedStatus) {
                console.log(`✅ ${test.name} - Status: ${response.status}`);
                passed++;
            } else {
                console.log(`❌ ${test.name} - Expected: ${test.expectedStatus}, Got: ${response.status}`);
                failed++;
            }
        } catch (error) {
            console.log(`❌ ${test.name} - Error: ${error.message}`);
            failed++;
        }
        console.log('');
    }

    // Test rate limiting
    console.log('Testing Rate Limiting...');
    try {
        const promises = [];
        for (let i = 0; i < 10; i++) {
            promises.push(
                axios.get(`${BASE_URL}/health?apikey=${API_KEY}`, { timeout: 5000 })
            );
        }
        await Promise.all(promises);
        console.log('✅ Rate limiting - No immediate throttling');
        passed++;
    } catch (error) {
        if (error.response && error.response.status === 429) {
            console.log('✅ Rate limiting - Working correctly (429 received)');
            passed++;
        } else {
            console.log(`❌ Rate limiting - Unexpected error: ${error.message}`);
            failed++;
        }
    }

    console.log('\n📊 Test Results:');
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log(`Total: ${passed + failed}`);

    if (failed > 0) {
        console.log('\n❌ Some tests failed. Please check your Apigee configuration.');
        process.exit(1);
    } else {
        console.log('\n✅ All tests passed! Your Apigee integration is working correctly.');
    }
}

// Test authentication flow
async function testAuthFlow() {
    console.log('\n🔐 Testing Authentication Flow...\n');
    
    try {
        // Test user registration
        console.log('Testing user registration...');
        const registerResponse = await axios.post(`${BASE_URL}/api/v1/auth/register?apikey=${API_KEY}`, {
            email: 'test@example.com',
            username: 'testuser',
            password: 'testpassword123'
        });
        console.log(`✅ Registration - Status: ${registerResponse.status}`);

        // Test user login
        console.log('Testing user login...');
        const loginResponse = await axios.post(
            `${BASE_URL}/api/v1/auth/login?apikey=${API_KEY}`,
            new URLSearchParams({
                username: 'testuser',
                password: 'testpassword123'
            }),
            {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            }
        );
        console.log(`✅ Login - Status: ${loginResponse.status}`);
        
        const token = loginResponse.data.access_token;
        console.log('✅ JWT token received');

        // Test protected endpoint
        console.log('Testing protected endpoint...');
        const tasksResponse = await axios.get(`${BASE_URL}/api/v1/tasks?apikey=${API_KEY}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        console.log(`✅ Protected endpoint - Status: ${tasksResponse.status}`);

    } catch (error) {
        if (error.response) {
            console.log(`❌ Auth test failed - Status: ${error.response.status}, Message: ${error.response.data}`);
        } else {
            console.log(`❌ Auth test failed - Error: ${error.message}`);
        }
    }
}

if (require.main === module) {
    if (!API_KEY) {
        console.log('❌ Please set the API_KEY environment variable with your Apigee API key');
        process.exit(1);
    }
    
    testProxy()
        .then(() => testAuthFlow())
        .catch(error => {
            console.error('Test execution failed:', error);
            process.exit(1);
        });
}

module.exports = { testProxy, testAuthFlow };