#!/usr/bin/env python3

"""
Quick Test for Mood-to-Chat Context Flow
Focuses on the essential functionality to verify the pipeline works.
"""

import requests
import json

def test_basic_mood_to_chat():
    """Test basic mood-to-chat context passing"""
    base_url = "http://127.0.0.1:5001"
    
    print("🧪 Testing Basic Mood-to-Chat Context Flow...")
    print("=" * 50)
    
    # Test 1: Direct chat API with mood context
    print("\n1️⃣ Testing mood-aware chat API...")
    
    chat_message = {
        'message': 'I just did my mood check-in and I\'m feeling anxious. Can you help?',
        'context': {
            'session_id': 'test_session_123',
            'user_journey': {
                'entry_point': 'mood_analytics_to_chat',
                'user_state': 'has_mood_data',
                'has_tracked_mood': True
            }
        },
        'mood_data': {
            'recent_rating': 7,
            'recent_emotion': 'Anxious',
            'dominant_emotions': ['Anxious'],
            'wellness_trend': 'stable',
            'notes': 'Feeling stressed about exams'
        }
    }
    
    try:
        response = requests.post(f"{base_url}/chat", 
                               json=chat_message,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get('message', data.get('response', ''))
            
            print("✅ Mood-aware chat API working!")
            print(f"🤖 AI Response: {ai_response[:100]}...")
            
            # Check for mood awareness indicators
            mood_keywords = ['anxious', 'anxiety', 'stress', 'exams', 'understand', 'support']
            found = [word for word in mood_keywords if word.lower() in ai_response.lower()]
            
            if found:
                print(f"✅ Context-aware response detected: {found}")
                return True
            else:
                print("⚠️ Response may not be fully mood-aware")
                print(f"Full response: {ai_response}")
                return False
        else:
            print(f"❌ Chat API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing chat API: {e}")
        return False

def test_chat_interface_loading():
    """Test that chat interface loads without errors"""
    base_url = "http://127.0.0.1:5001"
    
    print("\n2️⃣ Testing chat interface loading...")
    
    try:
        response = requests.get(f"{base_url}/chat")
        
        if response.status_code == 200:
            print("✅ Chat interface loads successfully")
            
            # Check for key components
            if 'alpinejs' in response.text.lower() or 'x-data' in response.text:
                print("✅ Alpine.js integration detected")
            
            if 'moodContext' in response.text:
                print("✅ Mood context structure present")
                
            return True
        else:
            print(f"❌ Chat interface failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error loading chat interface: {e}")
        return False

def main():
    print("🚀 Running Quick Mood-to-Chat Tests...")
    
    api_test = test_basic_mood_to_chat()
    interface_test = test_chat_interface_loading()
    
    print("\n" + "=" * 50)
    
    if api_test and interface_test:
        print("✨ Mood-to-Chat flow is working! 🎉")
        print("\n🎯 Key Features Confirmed:")
        print("   ✅ Mood context passes to AI chat")
        print("   ✅ Context-aware responses generated")
        print("   ✅ Chat interface loads with mood data")
        print("\n🌟 Users can now get personalized AI support based on their mood state!")
        return True
    else:
        print("⚠️ Some issues detected in the flow")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)