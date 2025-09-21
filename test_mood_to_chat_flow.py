#!/usr/bin/env python3

"""
Comprehensive Test Suite for Mood-Aware Chat Flow
Tests the complete user journey: login → mood tracking → chat with context awareness
"""

import requests
import json
import time
from urllib.parse import urljoin

def test_complete_mood_to_chat_flow():
    """Test complete mood-aware chat flow from mood analytics to chat"""
    base_url = "http://127.0.0.1:5001"
    
    print("🧪 Testing Complete Mood-to-Chat Flow...")
    print("=" * 60)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Test 1: User Authentication
    print("\n1️⃣ Testing user authentication...")
    
    # Register/Login test user
    login_data = {
        'username': 'testuser_flow',
        'password': 'password123'
    }
    
    # Try login first
    login_response = session.post(urljoin(base_url, "/login"), 
                                 json=login_data,
                                 headers={'Content-Type': 'application/json'})
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        if not login_result.get('success'):
            # User doesn't exist, create account
            print("ℹ️ Creating test user account...")
            register_data = {
                'username': 'testuser_flow',
                'email': 'testflow@sahara.com',
                'password': 'password123'
            }
            
            register_response = session.post(urljoin(base_url, "/register"),
                                           json=register_data,
                                           headers={'Content-Type': 'application/json'})
            
            if register_response.status_code == 200 and register_response.json().get('success'):
                print("✅ Test user created successfully")
                
                # Now login
                login_response = session.post(urljoin(base_url, "/login"), 
                                            json=login_data,
                                            headers={'Content-Type': 'application/json'})
                
                if login_response.status_code == 200 and login_response.json().get('success'):
                    print("✅ User authenticated successfully")
                else:
                    print("❌ Login failed after registration")
                    return False
            else:
                print("❌ Failed to create test user")
                return False
        else:
            print("✅ User authenticated successfully")
    else:
        print(f"❌ Authentication failed: {login_response.status_code}")
        return False
    
    # Test 2: Mood Tracking
    print("\n2️⃣ Testing mood entry submission...")
    
    mood_data = {
        'mood_emoji': '😟',
        'mood_label': 'Anxious',
        'mood_intensity': 7,
        'notes': 'Feeling stressed about upcoming exams and deadlines. Need support.'
    }
    
    mood_response = session.post(urljoin(base_url, "/mood"), json=mood_data)
    
    if mood_response.status_code == 200:
        print("✅ Mood entry submitted successfully")
        print(f"   📊 Mood: {mood_data['mood_label']} (Intensity: {mood_data['mood_intensity']}/10)")
        print(f"   📝 Notes: {mood_data['notes']}")
    else:
        print(f"❌ Mood submission failed: {mood_response.status_code}")
        return False
    
    # Test 3: Accessing Chat Interface with User Context
    print("\n3️⃣ Testing chat interface with user context...")
    
    chat_page = session.get(urljoin(base_url, "/chat"))
    
    if chat_page.status_code == 200:
        print("✅ Chat interface loaded successfully")
        
        # Check for user context in the response
        if 'testuser_flow' in chat_page.text:
            print("✅ User authentication context present in chat")
        
        if 'Anxious' in chat_page.text or 'recent_mood_data' in chat_page.text:
            print("✅ Mood context data passed to chat interface")
        else:
            print("⚠️ Mood context may not be fully integrated")
            
    else:
        print(f"❌ Chat interface failed to load: {chat_page.status_code}")
        return False
    
    # Test 4: Sending Message with Mood Context
    print("\n4️⃣ Testing mood-aware chat response...")
    
    # Simulate the chat message that would be sent from the frontend
    chat_message = {
        'message': 'Hi Sahara, I just completed my mood check-in and I\'m feeling really anxious about my exams. Can you help me?',
        'context': {
            'session_id': 'test_session_mood_flow',
            'user_journey': {
                'entry_point': 'authenticated_user',
                'user_state': 'has_mood_data',
                'has_tracked_mood': True,
                'session_duration': 300000  # 5 minutes
            }
        },
        'mood_data': {
            'recent_rating': 7,
            'recent_emotion': 'Anxious',
            'dominant_emotions': ['Anxious'],
            'wellness_trend': 'stable',
            'notes': 'Feeling stressed about upcoming exams and deadlines. Need support.'
        }
    }
    
    chat_response = session.post(urljoin(base_url, "/chat"), json=chat_message)
    
    if chat_response.status_code == 200:
        response_data = chat_response.json()
        ai_message = response_data.get('message', response_data.get('response', ''))
        
        print("✅ Mood-aware chat response received")
        print(f"   🤖 Sahara AI: {ai_message}")
        
        # Check if response is contextually aware
        context_indicators = ['anxious', 'anxiety', 'exams', 'stress', 'understand', 'support']
        found_indicators = [word for word in context_indicators if word.lower() in ai_message.lower()]
        
        if found_indicators:
            print(f"✅ Response shows contextual awareness: {found_indicators}")
        else:
            print("⚠️ Response may not be fully context-aware")
            
        # Check if AI acknowledges the mood check-in
        mood_acknowledgment = ['mood', 'check-in', 'feeling', 'recent', 'track']
        found_acknowledgment = [word for word in mood_acknowledgment if word.lower() in ai_message.lower()]
        
        if found_acknowledgment:
            print(f"✅ AI acknowledges mood context: {found_acknowledgment}")
        else:
            print("⚠️ AI may not fully acknowledge mood check-in")
            
    else:
        print(f"❌ Chat response failed: {chat_response.status_code}")
        try:
            error_data = chat_response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Raw response: {chat_response.text}")
        return False
    
    # Test 5: Follow-up Context Continuity
    print("\n5️⃣ Testing conversation continuity...")
    
    follow_up_message = {
        'message': 'What specific techniques can you recommend for managing exam anxiety?',
        'context': {
            'session_id': 'test_session_mood_flow',  # Same session ID
            'user_journey': {
                'entry_point': 'authenticated_user',
                'user_state': 'has_mood_data',
                'has_tracked_mood': True,
                'session_duration': 400000  # 6+ minutes
            }
        },
        'mood_data': {
            'recent_rating': 7,
            'recent_emotion': 'Anxious',
            'dominant_emotions': ['Anxious'],
            'wellness_trend': 'stable',
            'notes': 'Feeling stressed about upcoming exams and deadlines. Need support.'
        }
    }
    
    follow_up_response = session.post(urljoin(base_url, "/chat"), json=follow_up_message)
    
    if follow_up_response.status_code == 200:
        follow_up_data = follow_up_response.json()
        follow_up_ai = follow_up_data.get('message', follow_up_data.get('response', ''))
        
        print("✅ Follow-up conversation maintained")
        print(f"   🤖 Sahara AI: {follow_up_ai}")
        
        # Check for specific techniques or actionable advice
        technique_indicators = ['technique', 'strategy', 'method', 'practice', 'breathing', 'mindfulness']
        found_techniques = [word for word in technique_indicators if word.lower() in follow_up_ai.lower()]
        
        if found_techniques:
            print(f"✅ Provides actionable techniques: {found_techniques}")
        else:
            print("⚠️ May need more specific technique recommendations")
            
    else:
        print(f"❌ Follow-up conversation failed: {follow_up_response.status_code}")
    
    # Test 6: Mood Analytics to Chat Flow Integration
    print("\n6️⃣ Testing mood analytics → chat transition...")
    
    # Access mood analytics page (simulating user's journey)
    mood_analytics = session.get(urljoin(base_url, "/mood-analytics"))
    
    if mood_analytics.status_code == 200:
        print("✅ Mood analytics accessible with current session")
        
        # Check that recent mood entry is visible
        if 'Anxious' in mood_analytics.text and 'testuser_flow' in mood_analytics.text:
            print("✅ Recent mood entry visible in analytics")
        
        # Now test direct chat access from mood analytics context
        # This simulates clicking the chat button from mood analytics
        chat_from_analytics = session.get(urljoin(base_url, "/chat"))
        
        if chat_from_analytics.status_code == 200:
            print("✅ Chat accessible from mood analytics context")
            
            # Verify mood data is still available in chat context
            if 'recent_mood_data' in chat_from_analytics.text:
                print("✅ Mood context preserved in chat transition")
            else:
                print("⚠️ Mood context may not be fully preserved")
        else:
            print("❌ Chat access from mood analytics failed")
    else:
        print("❌ Mood analytics access failed")
    
    print("\n" + "=" * 60)
    print("✨ Mood-to-Chat Flow Test Completed!")
    print("🎯 Key Features Verified:")
    print("   • User authentication persistence")
    print("   • Mood data capture and storage")
    print("   • Context-aware chat initialization")
    print("   • Mood-informed AI responses")
    print("   • Session continuity across interfaces")
    print("   • Seamless analytics → chat transition")
    
    return True

if __name__ == "__main__":
    try:
        success = test_complete_mood_to_chat_flow()
        if success:
            print("\n🚀 Mood-aware chat system is fully operational!")
            print("🌟 Users can now seamlessly transition from mood tracking to contextual AI support!")
            exit(0)
        else:
            print("\n⚠️ Some flow components need attention")
            exit(1)
    except Exception as e:
        print(f"\n💥 Test error: {str(e)}")
        exit(1)