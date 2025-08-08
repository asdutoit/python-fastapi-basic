import httpx
import asyncio


async def test_endpoints():
    async with httpx.AsyncClient() as client:
        # Test root endpoint
        response = await client.get("http://localhost:8000/")
        print("Root endpoint (/):")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}\n")
        
        # Test health endpoint
        response = await client.get("http://localhost:8000/health")
        print("Health endpoint (/health):")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}\n")
        
        # Test docs availability
        response = await client.get("http://localhost:8000/docs")
        print("API Documentation (/docs):")
        print(f"  Status: {response.status_code}")
        print(f"  Available: {'Yes' if response.status_code == 200 else 'No'}\n")
        
        # Test ReDoc availability
        response = await client.get("http://localhost:8000/redoc")
        print("ReDoc Documentation (/redoc):")
        print(f"  Status: {response.status_code}")
        print(f"  Available: {'Yes' if response.status_code == 200 else 'No'}")


if __name__ == "__main__":
    print("Testing Task Management API endpoints...\n")
    asyncio.run(test_endpoints())
    print("\nAll tests completed!")