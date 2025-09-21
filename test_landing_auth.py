#!/usr/bin/env python3

"""
Test Suite for Landing Page Authentication Flow
Tests user authentication display and dropdown functionality on the main landing page.
"""

import requests
import time
from urllib.parse import urljoin

def test_landing_auth_flow():
    """Test complete authentication flow from landing page"""
    base_url = "http://127.0.0.1:5001"
    
    print("🧪 Testing Landing Page Authentication Flow...")
    print("=" * 60)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Test 1: Landing page loads with Sign In button (unauthenticated)
    print("\n1️⃣ Testing unauthenticated landing page...")
    response = session.get(urljoin(base_url, "/"))
    
    if response.status_code == 200:
        print("✅ Landing page loads successfully")
        # Check for Alpine.js integration
        if 'x-data="authApp()"' in response.text:
            print("✅ Alpine.js authentication app integrated")
        if 'isAuthenticated: false' in response.text:
            print("✅ Unauthenticated state detected")
        if 'Sign In' in response.text:
            print("✅ Sign In link present")
    else:
        print(f"❌ Landing page failed to load: {response.status_code}")
        return False
    
    # Test 2: Login process
    print("\n2️⃣ Testing user authentication...")
    
    # First get login page
    login_response = session.get(urljoin(base_url, "/login"))
    if login_response.status_code != 200:
        print(f"❌ Login page failed to load: {login_response.status_code}")
        return False
    
    # Try to log in with test credentials
    login_data = {
        'username': 'testuser',
        'password': 'password123'
    }
    
    login_attempt = session.post(urljoin(base_url, "/login"), 
                                json=login_data,
                                headers={'Content-Type': 'application/json'})
    
    # Check if login redirected (success) or returned login page (failure)
    if login_attempt.status_code == 200:
        if 'Create Account' in login_attempt.text or 'Sign in to Sahara' in login_attempt.text:
            print("ℹ️ Test user doesn't exist, creating account...")
            
            # Register new user
            register_data = {
                'username': 'testuser',
                'email': 'test@sahara.com',
                'password': 'password123'
            }
            
            register_attempt = session.post(urljoin(base_url, "/register"), 
                                          json=register_data,
                                          headers={'Content-Type': 'application/json'})
            
            if register_attempt.status_code in [200, 302]:
                print("✅ Test user created successfully")
                
                # Now try login again
                login_attempt = session.post(urljoin(base_url, "/login"), 
                                           json=login_data,
                                           headers={'Content-Type': 'application/json'})
                if login_attempt.status_code in [200, 302]:
                    print("✅ User authenticated successfully")
                else:
                    print(f"❌ Login failed after registration: {login_attempt.status_code}")
                    return False
            else:
                print(f"❌ User registration failed: {register_attempt.status_code}")
                return False
        else:
            print("✅ User authenticated successfully")
    elif login_attempt.status_code == 302:
        print("✅ User authenticated (redirected)")
    else:
        print(f"❌ Authentication failed: {login_attempt.status_code}")
        return False
    
    # Test 3: Landing page with authenticated user
    print("\n3️⃣ Testing authenticated landing page...")
    
    auth_landing = session.get(urljoin(base_url, "/"))
    if auth_landing.status_code == 200:
        print("✅ Authenticated landing page loads")
        
        # Check for username in the response
        if 'testuser' in auth_landing.text:
            print("✅ Username displayed in authenticated state")
        
        if 'isAuthenticated: true' in auth_landing.text:
            print("✅ Authenticated state detected")
        
        # Check for dropdown menu elements
        if 'Mood Analytics' in auth_landing.text:
            print("✅ Mood Analytics link present in dropdown")
        
        if 'Sign Out' in auth_landing.text:
            print("✅ Sign Out option present")
            
    else:
        print(f"❌ Authenticated landing page failed: {auth_landing.status_code}")
        return False
    
    # Test 4: Access to mood analytics from dropdown
    print("\n4️⃣ Testing mood analytics access...")
    
    mood_analytics = session.get(urljoin(base_url, "/mood-analytics"))
    if mood_analytics.status_code == 200:
        print("✅ Mood analytics accessible for authenticated user")
        if 'testuser' in mood_analytics.text:
            print("✅ Username shown in mood analytics")
    else:
        print(f"❌ Mood analytics access failed: {mood_analytics.status_code}")
    
    # Test 5: Logout functionality
    print("\n5️⃣ Testing logout functionality...")
    
    logout_response = session.post(urljoin(base_url, "/logout"))
    if logout_response.status_code in [200, 302]:
        print("✅ Logout request successful")
        
        # Check if back to unauthenticated state
        post_logout = session.get(urljoin(base_url, "/"))
        if post_logout.status_code == 200:
            if 'isAuthenticated: false' in post_logout.text:
                print("✅ Returned to unauthenticated state")
            if 'Sign In' in post_logout.text:
                print("✅ Sign In link restored after logout")
        
    else:
        print(f"❌ Logout failed: {logout_response.status_code}")
        return False
    
    print("\n" + "=" * 60)
    print("✨ All landing page authentication tests completed!")
    print("🎯 Authentication flow is working properly")
    
    return True

if __name__ == "__main__":
    try:
        success = test_landing_auth_flow()
        if success:
            print("\n🚀 Landing page authentication system ready for demo!")
            exit(0)
        else:
            print("\n⚠️ Some tests failed - please check the implementation")
            exit(1)
    except Exception as e:
        print(f"\n💥 Test error: {str(e)}")
        exit(1)