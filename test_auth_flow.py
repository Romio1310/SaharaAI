#!/usr/bin/env python3
"""
Authentication Flow Test
Tests login, register, and logout flows with proper redirections
"""

import requests
import json
import sys
from urllib.parse import urlparse, parse_qs

class AuthFlowTester:
    def __init__(self, base_url="http://127.0.0.1:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_register_with_redirect(self):
        """Test registration with redirect parameter"""
        print("🔄 Testing registration with mood-analytics redirect...")
        
        # Test data
        register_data = {
            "username": f"testuser_{int(time.time()) % 10000}",
            "email": f"test_{int(time.time()) % 10000}@example.com", 
            "password": "testpassword123",
            "next": "/mood-analytics"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/register",
                json=register_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('redirect') == '/mood-analytics':
                    print("✅ Registration with redirect - PASS")
                    return True, register_data['username']
                else:
                    print(f"❌ Registration failed: {data.get('message', 'Unknown error')}")
                    return False, None
            else:
                print(f"❌ Registration request failed: {response.status_code}")
                return False, None
                
        except Exception as e:
            print(f"❌ Registration test error: {e}")
            return False, None
    
    def test_login_with_redirect(self, username):
        """Test login with redirect parameter"""
        print("🔄 Testing login with mood-analytics redirect...")
        
        login_data = {
            "username": username,
            "password": "testpassword123",
            "next": "/mood-analytics"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/login",
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('redirect') == '/mood-analytics':
                    print("✅ Login with redirect - PASS")
                    return True
                else:
                    print(f"❌ Login failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Login request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Login test error: {e}")
            return False
    
    def test_logout_redirect(self):
        """Test logout redirect functionality"""
        print("🔄 Testing logout redirect...")
        
        try:
            # Test logout with from parameter
            response = self.session.get(
                f"{self.base_url}/logout?from=/mood-analytics",
                allow_redirects=False
            )
            
            if response.status_code in [302, 301]:
                location = response.headers.get('Location', '')
                if '/mood-analytics' in location:
                    print("✅ Logout redirect - PASS")
                    return True
                else:
                    print(f"❌ Logout redirected to wrong location: {location}")
                    return False
            else:
                print(f"❌ Logout request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Logout test error: {e}")
            return False
    
    def test_mood_analytics_access(self):
        """Test mood analytics page accessibility"""
        print("🔄 Testing mood analytics page access...")
        
        try:
            response = self.session.get(f"{self.base_url}/mood-analytics")
            
            if response.status_code == 200:
                # Check if page contains expected elements
                content = response.text
                has_auth_links = 'create an account' in content and 'sign in' in content
                has_logout_link = 'Logout' in content
                
                if has_auth_links or has_logout_link:
                    print("✅ Mood analytics page access - PASS")
                    return True
                else:
                    print("❌ Mood analytics page missing auth elements")
                    return False
            else:
                print(f"❌ Mood analytics page failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Mood analytics access test error: {e}")
            return False
    
    def run_all_tests(self):
        """Run complete authentication flow test"""
        print("🚀 Starting Authentication Flow Tests\n")
        
        tests_passed = 0
        total_tests = 4
        
        # Test 1: Mood analytics page access
        if self.test_mood_analytics_access():
            tests_passed += 1
            
        # Test 2: Registration with redirect
        success, username = self.test_register_with_redirect()
        if success:
            tests_passed += 1
            
            # Test 3: Login with redirect (only if registration succeeded)
            if self.test_login_with_redirect(username):
                tests_passed += 1
                
                # Test 4: Logout redirect (only if login succeeded)
                if self.test_logout_redirect():
                    tests_passed += 1
        
        print(f"\n📊 Authentication Tests: {tests_passed}/{total_tests} passed")
        
        if tests_passed == total_tests:
            print("🎉 All authentication flows working correctly!")
            return True
        else:
            print(f"⚠️  {total_tests - tests_passed} authentication tests failed.")
            return False

if __name__ == "__main__":
    import time
    tester = AuthFlowTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)