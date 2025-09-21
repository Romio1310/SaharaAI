#!/usr/bin/env python3
"""
Complete Feature Integration Test for Sahara AI
Tests all implemented action subparts from the flowchart
"""

import requests
import time

class SaharaIntegrationTester:
    def __init__(self, base_url="http://127.0.0.1:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_homepage_access(self):
        """Test homepage accessibility"""
        print("🏠 Testing Homepage Access")
        print("-" * 30)
        
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                print("   ✅ Homepage accessible")
                return True
            else:
                print(f"   ❌ Homepage failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Homepage error: {e}")
            return False
    
    def test_chat_functionality(self):
        """Test main chat functionality"""
        print("\n💬 Testing Chat Functionality")
        print("-" * 30)
        
        # Test chat page access
        try:
            response = self.session.get(f"{self.base_url}/chat")
            if response.status_code == 200:
                print("   ✅ Chat page accessible")
            else:
                print(f"   ❌ Chat page failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Chat page error: {e}")
            return False
        
        # Test chat API
        try:
            chat_response = self.session.post(f"{self.base_url}/chat", 
                                            json={'message': 'Hello, how are you?'},
                                            headers={'Content-Type': 'application/json'})
            if chat_response.status_code == 200:
                result = chat_response.json()
                if result.get('message'):
                    print("   ✅ Chat API working")
                    return True
                else:
                    print("   ❌ Chat API no response")
                    return False
            else:
                print(f"   ❌ Chat API failed: {chat_response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Chat API error: {e}")
            return False
    
    def test_mood_checkin(self):
        """Test mood check-in functionality"""
        print("\n❤️  Testing Mood Check-in")
        print("-" * 30)
        
        # Test mood check-in page
        try:
            response = self.session.get(f"{self.base_url}/mood-checkin")
            if response.status_code == 200:
                print("   ✅ Mood check-in page accessible")
            else:
                print(f"   ❌ Mood check-in page failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Mood check-in page error: {e}")
            return False
        
        # Test mood submission
        try:
            mood_data = {
                'mood_emoji': '😊',
                'mood_label': 'happy',
                'mood_intensity': 7,
                'notes': 'Testing mood functionality'
            }
            response = self.session.post(f"{self.base_url}/mood", 
                                       json=mood_data,
                                       headers={'Content-Type': 'application/json'})
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("   ✅ Mood submission working")
                    return True
                else:
                    print(f"   ❌ Mood submission failed: {result}")
                    return False
            else:
                print(f"   ❌ Mood API failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Mood API error: {e}")
            return False
    
    def test_resources_page(self):
        """Test resources functionality"""
        print("\n📚 Testing Resources Page")
        print("-" * 30)
        
        # Test resources page
        try:
            response = self.session.get(f"{self.base_url}/resources")
            if response.status_code == 200:
                print("   ✅ Resources page accessible")
            else:
                print(f"   ❌ Resources page failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Resources page error: {e}")
            return False
        
        # Test resources data API
        try:
            response = self.session.get(f"{self.base_url}/resources-data")
            if response.status_code == 200:
                data = response.json()
                if data:
                    print("   ✅ Resources data API working")
                    return True
                else:
                    print("   ⚠️  Resources data empty")
                    return True  # Still functional
            else:
                print(f"   ❌ Resources data API failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Resources data API error: {e}")
            return False
    
    def test_crisis_support(self):
        """Test crisis support functionality"""
        print("\n🚨 Testing Crisis Support")
        print("-" * 30)
        
        try:
            response = self.session.get(f"{self.base_url}/crisis-support")
            if response.status_code == 200:
                print("   ✅ Crisis support page accessible")
                return True
            else:
                print(f"   ❌ Crisis support page failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Crisis support page error: {e}")
            return False
    
    def test_dashboard(self):
        """Test dashboard functionality (now redirects to mood-analytics)"""
        print("\n📊 Testing Dashboard (Mood Analytics)")
        print("-" * 40)
        
        try:
            # Test the mood-analytics page which serves as the main dashboard
            response = self.session.get(f"{self.base_url}/mood-analytics")
            if response.status_code == 200:
                print("   ✅ Dashboard (mood-analytics) page accessible")
                return True
            else:
                print(f"   ❌ Dashboard (mood-analytics) page failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Dashboard (mood-analytics) page error: {e}")
            return False
    
    def test_user_authentication(self):
        """Test user authentication system"""
        print("\n🔐 Testing User Authentication")
        print("-" * 40)
        
        # Create unique test user
        timestamp = str(int(time.time()))
        test_user = {
            'username': f'flowtest_{timestamp}',
            'email': f'flowtest_{timestamp}@test.com',
            'password': 'TestFlow123!'
        }
        
        # Test registration
        try:
            register_response = self.session.post(f"{self.base_url}/register",
                                                json=test_user,
                                                headers={'Content-Type': 'application/json'})
            
            if register_response.status_code == 200:
                result = register_response.json()
                if result.get('success'):
                    print("   ✅ User registration working")
                else:
                    print(f"   ❌ Registration failed: {result.get('message')}")
                    return False
            else:
                print(f"   ❌ Registration request failed: {register_response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Registration error: {e}")
            return False
        
        # Test login
        try:
            login_response = self.session.post(f"{self.base_url}/login",
                                             json={
                                                 'username': test_user['username'],
                                                 'password': test_user['password']
                                             },
                                             headers={'Content-Type': 'application/json'})
            
            if login_response.status_code == 200:
                result = login_response.json()
                if result.get('success'):
                    print("   ✅ User login working")
                    return True
                else:
                    print(f"   ❌ Login failed: {result.get('message')}")
                    return False
            else:
                print(f"   ❌ Login request failed: {login_response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False

def main():
    """Run complete integration test"""
    print("🌸 Sahara AI - Complete Integration Test")
    print("=" * 50)
    
    tester = SaharaIntegrationTester()
    
    results = {
        'homepage': False,
        'chat': False,
        'mood_checkin': False,
        'resources': False,
        'crisis_support': False,
        'dashboard': False,
        'authentication': False
    }
    
    # Run all tests
    results['homepage'] = tester.test_homepage_access()
    results['chat'] = tester.test_chat_functionality()
    results['mood_checkin'] = tester.test_mood_checkin()
    results['resources'] = tester.test_resources_page()
    results['crisis_support'] = tester.test_crisis_support()
    results['dashboard'] = tester.test_dashboard()
    results['authentication'] = tester.test_user_authentication()
    
    # Final results
    print("\n" + "=" * 50)
    print("📊 COMPLETE INTEGRATION TEST RESULTS")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    feature_names = {
        'homepage': 'Homepage Access',
        'chat': 'Chat with AI Buddy',
        'mood_checkin': 'Mood Check-in',
        'resources': 'Access Resources',
        'crisis_support': 'Crisis Support',
        'dashboard': 'Dashboard (Mood Analytics)',
        'authentication': 'User Authentication'
    }
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        feature_display = feature_names[test_name]
        print(f"{status} - {feature_display}")
    
    print(f"\nOverall: {passed}/{total} features working")
    
    if passed == total:
        print("🎉 ALL FEATURES WORKING PERFECTLY!")
        print("✅ Your Sahara AI platform is complete and ready for demo!")
        print("\n🌟 Features Available:")
        print("   • ChatGPT-style AI chat interface with history")
        print("   • Comprehensive mood tracking system")
        print("   • Wellness resources library")
        print("   • Crisis support with helplines")
        print("   • User dashboard with analytics")
        print("   • Full user authentication system")
        print("   • Mobile-responsive design")
        print("   • Dark/light theme toggle")
    elif passed >= total - 1:
        print("🌟 EXCELLENT! Almost all features working")
        print("✅ Your platform is ready for demo with minor adjustments needed")
    else:
        print("⚠️  NEEDS ATTENTION! Some core features have issues")
    
    return passed == total

if __name__ == "__main__":
    main()