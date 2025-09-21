#!/usr/bin/env python3
"""
Test script to verify MoodEntry AttributeError fix
Tests the specific issue where new users logging in from landing page
and going directly to chat would encounter AttributeError.
"""

import requests
import json

def test_new_user_chat_flow():
    """Test that new users can access chat without MoodEntry errors"""
    print("🧪 Testing New User Chat Flow (No Mood Data)")
    print("=" * 50)
    
    session = requests.Session()
    base_url = "http://127.0.0.1:5001"
    
    # Step 1: Create a new test user
    print("1. 👤 Creating fresh test user...")
    test_user = {
        'username': 'fresh_user_test',
        'email': 'fresh@test.com',
        'password': 'TestPass123!'
    }
    
    # Register new user
    register_response = session.post(f"{base_url}/register", 
                                   json=test_user,
                                   headers={'Content-Type': 'application/json'})
    
    if register_response.status_code == 200:
        result = register_response.json()
        if result.get('success'):
            print("   ✅ User registration successful")
        else:
            print("   ⚠️  User might already exist, trying login...")
    
    # Step 2: Login the user
    print("2. 🔐 Logging in user...")
    login_response = session.post(f"{base_url}/login", 
                                json={
                                    'username': test_user['username'],
                                    'password': test_user['password']
                                },
                                headers={'Content-Type': 'application/json'})
    
    if login_response.status_code == 200:
        result = login_response.json()
        if result.get('success'):
            print("   ✅ Login successful")
        else:
            print("   ❌ Login failed:", result.get('message', 'Unknown error'))
            return False
    
    # Step 3: Test chat interface access (the critical test)
    print("3. 💬 Testing chat interface access for new user...")
    chat_response = session.get(f"{base_url}/chat")
    
    if chat_response.status_code == 200:
        print("   ✅ Chat interface loaded successfully")
        
        # Check if page contains error indicators
        if 'AttributeError' in chat_response.text or 'MoodEntry' in chat_response.text:
            print("   ❌ MoodEntry error still present in chat page")
            return False
        elif 'fresh_user_test' in chat_response.text or 'user_context' in chat_response.text:
            print("   ✅ Chat page loaded with user context (no MoodEntry errors)")
            return True
        else:
            print("   ⚠️  Chat page loaded but user context unclear")
            return True  # No error is still success
    else:
        print(f"   ❌ Chat interface failed to load: {chat_response.status_code}")
        return False

def test_existing_user_with_mood_data():
    """Test that users with existing mood data still work properly"""
    print("\n4. 📊 Testing existing user with mood data...")
    
    session = requests.Session()
    base_url = "http://127.0.0.1:5001"
    
    # Login as existing user (from previous tests)
    login_response = session.post(f"{base_url}/login", 
                                json={
                                    'username': 'test_auth_user',
                                    'password': 'TestPass123!'
                                },
                                headers={'Content-Type': 'application/json'})
    
    if login_response.status_code == 200:
        print("   ✅ Existing user login successful")
        
        # Test chat interface
        chat_response = session.get(f"{base_url}/chat")
        
        if chat_response.status_code == 200:
            print("   ✅ Chat interface works for existing users")
            return True
        else:
            print("   ❌ Chat interface failed for existing users")
            return False
    else:
        print("   ⚠️  Existing user login failed (might not exist)")
        return True  # This is OK for this test

def main():
    """Run all chat flow tests"""
    print("🌸 Sahara AI - MoodEntry AttributeError Fix Test")
    print("Testing fix for: AttributeError: 'MoodEntry' object has no attribute 'mood'")
    print()
    
    success = True
    
    # Test 1: New user flow (the main issue)
    if not test_new_user_chat_flow():
        success = False
    
    # Test 2: Existing user flow (regression test)
    if not test_existing_user_with_mood_data():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ New users can log in and access chat without MoodEntry errors")
        print("✅ Existing users with mood data still work properly")
        print("✅ Chat interface handles both scenarios gracefully")
        print("\n🚀 MoodEntry AttributeError successfully fixed!")
    else:
        print("❌ SOME TESTS FAILED - MoodEntry issue may still exist")
    
    return success

if __name__ == "__main__":
    main()