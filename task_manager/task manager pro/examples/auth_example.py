"""
Example usage of Task Manager Pro API with authentication.

This script demonstrates:
1. Registering a new user
2. Logging in and getting JWT tokens
3. Using the token to access protected endpoints
4. Refreshing the token
"""

import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8001"  # Adjust port if needed


async def main():
    """Main example flow."""
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("Task Manager Pro - API Example")
        print("=" * 60)

        # Step 1: Register
        print("\n1. Registering a new user...")
        register_data = {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "securepass123",
        }
        response = await client.post(
            f"{BASE_URL}/api/auth/register",
            json=register_data,
        )
        if response.status_code == 201:
            user = response.json()
            print(f"✅ Registered: {user['username']} ({user['email']})")
        else:
            print(f"❌ Registration failed: {response.text}")
            return

        # Step 2: Login
        print("\n2. Logging in...")
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            params={
                "email": "john@example.com",
                "password": "securepass123",
            },
        )
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens["access_token"]
            refresh_token = tokens["refresh_token"]
            print(f"✅ Logged in successfully")
            print(f"   Token type: {tokens['token_type']}")
            print(f"   Access token: {access_token[:20]}...")
        else:
            print(f"❌ Login failed: {response.text}")
            return

        # Step 3: Access protected endpoint
        print("\n3. Accessing protected endpoint...")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(
            f"{BASE_URL}/health",
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data['status']}")
        else:
            print(f"❌ Request failed: {response.text}")

        # Step 4: Refresh token
        print("\n4. Refreshing access token...")
        response = await client.post(
            f"{BASE_URL}/api/auth/refresh",
            params={"refresh_token": refresh_token},
        )
        if response.status_code == 200:
            new_tokens = response.json()
            print(f"✅ Token refreshed successfully")
            print(f"   New access token: {new_tokens['access_token'][:20]}...")
        else:
            print(f"❌ Refresh failed: {response.text}")

        # Step 5: Logout
        print("\n5. Logging out...")
        response = await client.post(f"{BASE_URL}/api/auth/logout")
        if response.status_code == 200:
            print(f"✅ Logged out successfully")
        else:
            print(f"❌ Logout failed: {response.text}")

        print("\n" + "=" * 60)
        print("Example completed!")
        print("=" * 60)


if __name__ == "__main__":
    print("\n⚠️  Make sure the API server is running on http://localhost:8001")
    print("   Run: uvicorn app.main_pro:app --port 8001\n")

    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the API server is running!")
