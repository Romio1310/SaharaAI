#!/usr/bin/env python3
"""
Comprehensive Test Suite for Mood-Aware Chat Implementation
Tests all workflows, entry points, and edge cases
"""

import requests
import json
import sys
import time
from datetime import datetime

class MoodChatTester:
    def __init__(self, base_url="http://127.0.0.1:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_server_running(self):
        """Test 1: Verify server is running"""
        try:
            response = self.session.get(self.base_url)
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
        except Exception as e:
            passed = False
            details = f"Error: {e}"
        
        self.log_test("Server Running", passed, details)
        return passed
    
    def test_mood_context_pipeline_anonymous(self):
        """Test 2: Mood context pipeline for anonymous users"""
        try:
            # Simulate anonymous user chat with mood data
            chat_data = {
                "message": "I'm feeling stressed about my physics exam",
                "context": {
                    "session_id": "test_session_123",
                    "mood": "stressed",
                    "history": [],
                    "timestamp": datetime.now().isoformat(),
                    "user_journey": {
                        "entry_point": "mood_analytics_referral",
                        "user_state": "seeking_support",
                        "has_tracked_mood": True,
                        "session_duration": 5
                    }
                },
                "mood_data": {
                    "recent_rating": 4,
                    "recent_emotion": "stressed", 
                    "dominant_emotions": ["stressed", "anxious"],
                    "wellness_trend": "declining"
                }
            }
            
            response = self.session.post(f"{self.base_url}/chat", 
                                       json=chat_data,
                                       headers={'Content-Type': 'application/json'})
            
            passed = response.status_code == 200
            if passed:
                data = response.json()
                # Check if response contains mood-aware elements
                has_mood_awareness = any(word in data.get('message', '').lower() 
                                       for word in ['stress', 'physics', 'exam', 'tough'])
                passed = passed and has_mood_awareness
                details = f"Response received, mood-aware: {has_mood_awareness}"
            else:
                details = f"HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            passed = False
            details = f"Error: {e}"
        
        self.log_test("Anonymous Mood Context Pipeline", passed, details)
        return passed
    
    def test_user_journey_tracking(self):
        """Test 3: User journey tracking and entry point detection"""
        try:
            # Test different entry points
            entry_points = [
                "direct_chat_access",
                "mood_analytics_referral", 
                "mood_checkin_referral",
                "external_referral"
            ]
            
            all_passed = True
            for entry_point in entry_points:
                chat_data = {
                    "message": "Hello, how can you help me?",
                    "context": {
                        "session_id": f"test_{entry_point}",
                        "user_journey": {
                            "entry_point": entry_point,
                            "user_state": "seeking_support"
                        }
                    }
                }
                
                response = self.session.post(f"{self.base_url}/chat", 
                                           json=chat_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code != 200:
                    all_passed = False
                    break
            
            passed = all_passed
            details = f"Tested {len(entry_points)} entry points"
            
        except Exception as e:
            passed = False
            details = f"Error: {e}"
        
        self.log_test("User Journey Tracking", passed, details)
        return passed
    
    def test_mood_aware_greetings(self):
        """Test 4: Mood-aware greeting generation"""
        try:
            # Test different mood states
            mood_scenarios = [
                {"emotion": "happy", "rating": 8, "trend": "improving"},
                {"emotion": "sad", "rating": 3, "trend": "declining"},
                {"emotion": "stressed", "rating": 4, "trend": "stable"},
                {"emotion": "excited", "rating": 9, "trend": "improving"}
            ]
            
            greeting_responses = []
            for scenario in mood_scenarios:
                chat_data = {
                    "message": "Hi there!",
                    "context": {
                        "session_id": f"greeting_test_{scenario['emotion']}"
                    },
                    "mood_data": {
                        "recent_rating": scenario["rating"],
                        "recent_emotion": scenario["emotion"],
                        "wellness_trend": scenario["trend"]
                    }
                }
                
                response = self.session.post(f"{self.base_url}/chat", 
                                           json=chat_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    greeting_responses.append(data.get('message', ''))
            
            # Check if different emotions produce different responses
            unique_responses = len(set(greeting_responses))
            passed = unique_responses > 1 and len(greeting_responses) == len(mood_scenarios)
            details = f"Generated {unique_responses} unique responses from {len(mood_scenarios)} scenarios"
            
        except Exception as e:
            passed = False
            details = f"Error: {e}"
        
        self.log_test("Mood-Aware Greetings", passed, details)
        return passed
    
    def test_context_aware_responses(self):
        """Test 5: Context-aware response enhancement"""
        try:
            # Test academic stress with mood context
            chat_data = {
                "message": "Physics is so difficult, I can't understand anything",
                "context": {
                    "session_id": "context_test",
                    "user_journey": {
                        "entry_point": "mood_analytics_referral",
                        "user_state": "analyzing_mood_data"
                    }
                },
                "mood_data": {
                    "recent_rating": 3,
                    "recent_emotion": "overwhelmed",
                    "wellness_trend": "declining"
                }
            }
            
            response = self.session.post(f"{self.base_url}/chat", 
                                       json=chat_data,
                                       headers={'Content-Type': 'application/json'})
            
            passed = response.status_code == 200
            if passed:
                data = response.json()
                message = data.get('message', '').lower()
                # Check for academic context + mood awareness
                has_academic_response = 'physics' in message
                has_mood_enhancement = any(word in message for word in ['tough', 'difficult', 'challenge', 'understand'])
                passed = has_academic_response and has_mood_enhancement
                details = f"Academic response: {has_academic_response}, Mood enhancement: {has_mood_enhancement}"
            else:
                details = f"HTTP {response.status_code}"
                
        except Exception as e:
            passed = False
            details = f"Error: {e}"
        
        self.log_test("Context-Aware Responses", passed, details)
        return passed
    
    def test_error_handling(self):
        """Test 6: Error handling and edge cases"""
        try:
            # Test empty message
            response1 = self.session.post(f"{self.base_url}/chat", 
                                        json={"message": ""},
                                        headers={'Content-Type': 'application/json'})
            
            # Test malformed data
            response2 = self.session.post(f"{self.base_url}/chat", 
                                        json={"invalid": "data"},
                                        headers={'Content-Type': 'application/json'})
            
            # Check if errors are handled gracefully
            error1_handled = response1.status_code == 400  # Bad request for empty message
            error2_handled = response2.status_code in [400, 500]  # Should handle malformed data
            
            passed = error1_handled and error2_handled
            details = f"Empty message: {response1.status_code}, Malformed data: {response2.status_code}"
            
        except Exception as e:
            passed = False
            details = f"Error: {e}"
        
        self.log_test("Error Handling", passed, details)
        return passed
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Mood-Aware Chat Test Suite\n")
        
        tests = [
            self.test_server_running,
            self.test_mood_context_pipeline_anonymous,
            self.test_user_journey_tracking,
            self.test_mood_aware_greetings,
            self.test_context_aware_responses,
            self.test_error_handling
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
            time.sleep(0.5)  # Small delay between tests
        
        print(f"\n📊 Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Mood-aware chat system is fully functional.")
            return True
        else:
            print(f"⚠️  {total_tests - passed_tests} tests failed. Check implementation.")
            return False

if __name__ == "__main__":
    tester = MoodChatTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)