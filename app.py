from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import json
import os
import random
import re
from datetime import datetime
import uuid
from dotenv import load_dotenv
import google.generativeai as genai
import logging
import bcrypt

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sahara-wellness-secret-key-' + str(uuid.uuid4()))

# Database configuration - use environment variable for production or SQLite for local
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Production: Use provided database URL (e.g., PostgreSQL)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Development: Use SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sahara_wellness.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chats = db.relationship('ChatHistory', backref='user', lazy=True)
    mood_entries = db.relationship('MoodEntry', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    mood = db.Column(db.String(50))
    session_id = db.Column(db.String(100))

class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Allow anonymous entries
    mood_emoji = db.Column(db.String(10), nullable=False)  # Emoji representation
    mood_label = db.Column(db.String(50), nullable=False)  # Text label (happy, sad, etc.)
    mood_intensity = db.Column(db.Integer, nullable=False)  # 1-5 scale
    notes = db.Column(db.Text)  # Optional user notes
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100))  # For anonymous users
    
    def to_dict(self):
        return {
            'id': self.id,
            'mood_emoji': self.mood_emoji,
            'mood_label': self.mood_label,
            'mood_intensity': self.mood_intensity,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Load AI responses and resources
def load_data():
    try:
        with open('data/responses.json', 'r', encoding='utf-8') as f:
            responses = json.load(f)
        with open('data/resources.json', 'r', encoding='utf-8') as f:
            resources = json.load(f)
        return responses, resources
    except FileNotFoundError:
        return {}, {}

responses_data, resources_data = load_data()

class GeminiAI:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.use_gemini = os.getenv('USE_GEMINI_API', 'false').lower() == 'true'
        self.model = None
        
        if self.use_gemini and self.api_key and self.api_key != 'demo_mode_no_api_key':
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name
                print("✅ Gemini AI initialized successfully")
            except Exception as e:
                print(f"⚠️ Gemini AI initialization failed: {e}")
                self.use_gemini = False
        else:
            print("🔄 Running in local mode - Gemini API disabled")
    
    def get_gemini_response(self, user_message, context_info, conversation_history=None):
        """Get intelligent response from Gemini API"""
        if not self.use_gemini or not self.model:
            return None
        
        try:
            # Create a natural, human-like response prompt
            emotional_context = self._get_emotional_response_style(user_message, context_info.get('emotion', 'neutral'))
            
            prompt = f"""
You are Sahara, a caring friend who understands Indian youth culture perfectly. You talk like a real person - not like a formal counselor or AI assistant. You're the friend someone would text when they're feeling overwhelmed.

Current situation: "{user_message}"
How the person seems to be feeling: {context_info.get('emotion', 'neutral')}
Conversation flow: {conversation_history[-1] if conversation_history else "This is their first message to you"}

BE A REAL FRIEND. Here's how:

EMOTIONAL REACTIONS - React naturally first:
- If they're stressed: "Arre yaar, that sounds really tough 😔" 
- If excited: "Omg that's amazing! 🎉"
- If sad: "Aww man, मुझे really sad लग रहा है hearing this 💙"
- If confused: "Haan I totally get why you'd feel confused about this"
- If angry: "That's so frustrating! Anyone would be mad about this"

NATURAL LANGUAGE - Talk like their friend:
- Use "yaar", "arre", "bas", "matlab", "seriously", "honestly"
- Mix Hindi/English naturally: "Mujhe लगता है", "that's so relatable yaar"
- Use casual expressions: "I totally get it", "That makes complete sense", "uff that's rough"
- React with genuine surprise: "Wait what?", "Seriously?", "No way!"

REAL RESPONSES - Not generic advice:
- Share relatable thoughts: "Yaar everyone goes through this phase"
- Acknowledge their specific situation: Don't give generic responses
- Be conversational: "You know what I think?", "Here's what I've noticed"
- Ask like a real friend: "But tell me, how are YOU feeling about all this?"

CULTURAL UNDERSTANDING:
- Understand Indian family dynamics without explaining them
- Know about boards, JEE, NEET pressure naturally 
- Get the "log kya kahenge" mentality
- Understand joint family issues, arranged marriage pressure, career expectations

Keep it to 2-3 short paragraphs. Sound like you're genuinely responding to a friend's message, not giving a counseling session.

{emotional_context}

Respond naturally as Sahara:
"""
            
            response = self.model.generate_content(prompt)
            if response and response.text:
                return {
                    'message': response.text.strip(),
                    'context': context_info.get('main_topic', 'gemini_response'),
                    'source': 'gemini'
                }
        except Exception as e:
            print(f"Gemini API error: {e}")
        
        return None
    
    def _get_emotional_response_style(self, message, emotion):
        """Generate appropriate emotional response style based on user's state"""
        message_lower = message.lower()
        
        # Detect emotional intensity and context
        if any(word in message_lower for word in ['crying', 'रो रहा', 'devastated', 'heartbroken', 'टूट गया']):
            return "This person is really hurting. Be extra gentle and comforting. Lead with empathy."
        
        elif any(word in message_lower for word in ['excited', 'happy', 'khush', 'great news', 'amazing']):
            return "They're sharing good news! Be genuinely excited for them and celebrate with them."
        
        elif any(word in message_lower for word in ['confused', 'samajh nahi aa raha', "don't know", 'stuck']):
            return "They're feeling lost and need clarity. Help them think through it step by step, like a friend would."
        
        elif any(word in message_lower for word in ['angry', 'frustrated', 'gussa', 'annoying', 'hate']):
            return "They're venting. Let them feel heard first, then gently help them process the anger."
        
        elif any(word in message_lower for word in ['scared', 'nervous', 'डरा हुआ', 'anxious', 'worried']):
            return "They need reassurance. Be calming and help them feel less alone with their fears."
        
        elif any(word in message_lower for word in ['tired', 'exhausted', 'बहुत थक गया', 'burn out']):
            return "They're emotionally or physically drained. Acknowledge how hard they're working and validate their tiredness."
        
        else:
            return "Respond naturally to what they're sharing. Match their energy level and be a supportive friend."

class SaharaAI:
    def __init__(self):
        self.responses = responses_data
        self.conversation_memory = {}
        self.user_sessions = {}
        self.gemini_ai = GeminiAI()  # Initialize Gemini integration
        
        # Enhanced context understanding with more nuanced patterns
        self.context_patterns = {
            'academic_pressure': {
                'keywords': ['study', 'studies', 'exam', 'exams', 'test', 'marks', 'grade', 'college', 'school', 'jee', 'neet', 'boards', 'coaching', 'rank'],
                'emotional_indicators': ['stressed', 'pressure', 'overwhelmed', 'tired', 'anxious', 'worried', 'burnt out', 'exhausted', 'fed up'],
                'language_mix': ['padhai', 'exam', 'marks', 'college', 'school', 'coaching', 'rank', 'bahut padha', 'dimag kharab'],
                'casual_expressions': ['cant take it anymore', 'so done with this', 'pressure cooker ban gaya hun', 'head explode hone wala hai']
            },
            'family_expectations': {
                'keywords': ['family', 'parents', 'mummy', 'papa', 'dad', 'mom', 'expectations', 'disappoint', 'fight', 'argument'],
                'emotional_indicators': ['disappointed', 'pressure', 'fight', 'angry', 'sad', 'frustrated', 'misunderstood', 'trapped'],
                'language_mix': ['ghar mein', 'mummy papa', 'bolte hain', 'sunna padta', 'samjhate nahi', 'log kya kahenge', 'relatives'],
                'casual_expressions': ['they just dont get it', 'always on my case', 'never happy with anything', 'bas taunt karte rehte']
            },
            'social_anxiety': {
                'keywords': ['friends', 'social', 'people', 'talk', 'shy', 'awkward', 'lonely', 'party', 'group', 'hang out'],
                'emotional_indicators': ['nervous', 'scared', 'worried', 'uncomfortable', 'left out', 'weird', 'different'],
                'language_mix': ['dost', 'baat karna', 'sharma jana', 'log', 'group mein nahi fit hota', 'akela lagta'],
                'casual_expressions': ['i feel so awkward', 'dont know what to say', 'everyone seems so confident', 'main hi ajeeb hun kya']
            },
            'general_sadness': {
                'keywords': ['sad', 'down', 'low', 'empty', 'hopeless', 'cry', 'upset', 'depressed', 'crying', 'tears'],
                'emotional_indicators': ['depressed', 'lonely', 'tired', 'worthless', 'broken', 'numb', 'heavy heart'],
                'language_mix': ['udaas', 'rona', 'dukhi', 'pareshan', 'mann nahi kar raha', 'dil bhari', 'ro raha hun'],
                'casual_expressions': ['everything sucks', 'nothing makes me happy', 'just want to disappear', 'kuch acha nahi lagta']
            },
            'positive_sharing': {
                'keywords': ['good', 'happy', 'better', 'success', 'achievement', 'proud', 'excited', 'amazing', 'awesome', 'great'],
                'emotional_indicators': ['excited', 'grateful', 'confident', 'optimistic', 'thrilled', 'pumped', 'over the moon'],
                'language_mix': ['khush', 'accha laga', 'khushi', 'mazaak', 'bahut accha', 'kamaal', 'zabardast'],
                'casual_expressions': ['im so happy', 'this is amazing', 'cant believe it happened', 'feeling on top of world']
            },
            'relationship_issues': {
                'keywords': ['boyfriend', 'girlfriend', 'crush', 'love', 'breakup', 'relationship', 'dating', 'propose'],
                'emotional_indicators': ['heartbroken', 'confused', 'rejected', 'in love', 'nervous', 'excited', 'hurt'],
                'language_mix': ['pyar', 'dil toot gaya', 'propose karu', 'reject kar diya', 'confused hun'],
                'casual_expressions': ['they dont like me back', 'should i tell them', 'got friendzoned', 'kya karu samajh nahi aa raha']
            },
            'career_confusion': {
                'keywords': ['career', 'job', 'future', 'what to do', 'confused', 'stream', 'branch', 'course'],
                'emotional_indicators': ['confused', 'lost', 'scared', 'pressured', 'uncertain', 'worried'],
                'language_mix': ['kya karu', 'samajh nahi aa raha', 'future dark lagta', 'kuch pata nahi'],
                'casual_expressions': ['no idea what to do', 'everyone else seems sorted', 'feeling so lost', 'koi direction nahi hai']
            }
        }
    
    def understand_message_deeply(self, message, session_id=None):
        """Advanced message understanding with context awareness"""
        message_lower = message.lower()
        
        # Initialize analysis
        analysis = {
            'main_topic': None,
            'emotion': 'neutral',
            'intensity': 'moderate',
            'specific_concerns': [],
            'needs_follow_up': False,
            'context_clues': [],
            'sentiment_score': 0,
            'user_state': 'exploring'
        }
        
        # Detect primary context
        context_scores = {}
        for context_name, patterns in self.context_patterns.items():
            score = 0
            matched_elements = []
            
            # Check keywords
            for keyword in patterns['keywords']:
                if keyword in message_lower:
                    score += 2
                    matched_elements.append(keyword)
            
            # Check emotional indicators
            for emotion in patterns['emotional_indicators']:
                if emotion in message_lower:
                    score += 3  # Emotions get higher weight
                    analysis['emotion'] = emotion
            
            # Check Hindi/mixed language
            for hindi_phrase in patterns['language_mix']:
                if hindi_phrase in message_lower:
                    score += 2
                    matched_elements.append(hindi_phrase)
            
            if score > 0:
                context_scores[context_name] = {
                    'score': score,
                    'elements': matched_elements
                }
        
        # Determine main topic
        if context_scores:
            analysis['main_topic'] = max(context_scores.keys(), key=lambda x: context_scores[x]['score'])
            analysis['context_clues'] = context_scores[analysis['main_topic']]['elements']
            analysis['sentiment_score'] = context_scores[analysis['main_topic']]['score']
        
        # Determine user state and needs
        question_indicators = ['how', 'what', 'why', 'कैसे', 'क्या', 'कैसा', '?']
        if any(q in message_lower for q in question_indicators):
            analysis['user_state'] = 'seeking_guidance'
            analysis['needs_follow_up'] = True
        
        negative_indicators = ['not', 'no', 'nahi', 'नहीं', 'cant', 'unable', 'difficult']
        if any(neg in message_lower for neg in negative_indicators):
            analysis['user_state'] = 'struggling'
            analysis['needs_follow_up'] = True
        
        # Extract specific concerns
        concern_patterns = {
            'academic': ['marks kam', 'fail', 'competition', 'pressure', 'study'],
            'family': ['parents angry', 'expectations', 'disappointed', 'ghar mein'],
            'social': ['friends', 'lonely', 'talk nahi kar', 'awkward'],
            'emotional': ['sad', 'depressed', 'anxious', 'worried', 'upset']
        }
        
        for concern_type, indicators in concern_patterns.items():
            for indicator in indicators:
                if indicator in message_lower:
                    analysis['specific_concerns'].append(concern_type)
        
        return analysis

    def generate_intelligent_response(self, message, session_id=None, mood_context=None, user_context=None):
        """Generate contextually intelligent responses using Gemini AI with local fallback"""
        
        # Deep analysis of the message
        analysis = self.understand_message_deeply(message, session_id)
        
        # Enhance analysis with mood context if available
        if mood_context and mood_context.get('has_recent_data'):
            analysis['mood_context'] = mood_context
            analysis['user_emotional_state'] = mood_context['recent_emotion']
            analysis['user_wellness_trend'] = mood_context['wellness_trend']
        
        # Handle crisis immediately - always use local crisis response
        crisis_words = ['suicide', 'kill myself', 'end it all', 'want to die', 'मरना चाहता हूं', 'जिंदगी से परेशान']
        if any(word in message.lower() for word in crisis_words):
            return {
                'message': f"मैं समझ सकता हूं कि आप बहुत कठिन समय से गुजर रहे हैं। आपकी जिंदगी मायने रखती है। 🤗\n\n🚨 तुरंत मदद:\n• Aasra: 91-9820466726\n• Sneha: 91-44-24640050\n• आप अकेले नहीं हैं।",
                'context': 'crisis',
                'urgent': True,
                'source': 'local_crisis'
            }
        
        # Get conversation history for context
        conversation_history = []
        if session_id and session_id in self.user_sessions:
            conversation_history = [msg['user'] for msg in self.user_sessions[session_id]['messages'][-3:]]
        
        # Try Gemini AI first
        gemini_response = self.gemini_ai.get_gemini_response(message, analysis, conversation_history)
        
        if gemini_response:
            # Store conversation context
            self._store_conversation_context(message, analysis, session_id)
            return gemini_response
        
        # Fallback to local intelligent responses
        response = self._craft_contextual_response(message, analysis, session_id, user_context)
        response['source'] = 'local_intelligent'
        
        # Store conversation context
        self._store_conversation_context(message, analysis, session_id)
        
        return response
    
    def _store_conversation_context(self, message, analysis, session_id):
        """Store conversation context for continuity"""
        if session_id:
            if session_id not in self.user_sessions:
                self.user_sessions[session_id] = {
                    'messages': [],
                    'topics_discussed': set(),
                    'emotional_journey': [],
                    'rapport_level': 0
                }
            
            self.user_sessions[session_id]['messages'].append({
                'user': message,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            })
            
            if analysis['main_topic']:
                self.user_sessions[session_id]['topics_discussed'].add(analysis['main_topic'])
            
            self.user_sessions[session_id]['emotional_journey'].append(analysis['emotion'])
            self.user_sessions[session_id]['rapport_level'] += 1
    
    def _craft_contextual_response(self, message, analysis, session_id=None, user_context=None):
        """Craft intelligent, contextual responses based on deep analysis"""
        
        # Get session context if available
        session_context = self.user_sessions.get(session_id, {}) if session_id else {}
        is_continuing_conversation = len(session_context.get('messages', [])) > 0
        
        # Get mood context from analysis if available
        mood_context = analysis.get('mood_context', {})
        has_mood_data = mood_context.get('has_recent_data', False)
        
        # Add mood-aware greeting for first-time interactions
        greeting_response = self._add_mood_aware_greeting(message, analysis, has_mood_data, mood_context, is_continuing_conversation, user_context)
        
        # Response based on main topic and user state
        base_response = None
        if analysis['main_topic'] == 'academic_stress':
            base_response = self._handle_academic_stress(message, analysis, is_continuing_conversation, mood_context)
        elif analysis['main_topic'] == 'family_pressure':
            base_response = self._handle_family_pressure(message, analysis, is_continuing_conversation, mood_context)
        elif analysis['main_topic'] == 'social_anxiety':
            base_response = self._handle_social_anxiety(message, analysis, is_continuing_conversation, mood_context)
        elif analysis['main_topic'] == 'general_sadness':
            base_response = self._handle_general_sadness(message, analysis, is_continuing_conversation, mood_context)
        elif analysis['main_topic'] == 'positive_sharing':
            base_response = self._handle_positive_sharing(message, analysis, is_continuing_conversation, mood_context)
        else:
            base_response = self._handle_general_conversation(message, analysis, is_continuing_conversation, mood_context, user_context)
        
        # Combine greeting with base response if greeting exists
        if greeting_response:
            base_response['message'] = greeting_response + "\n\n" + base_response['message']
            
        return base_response
        
    def _add_mood_aware_greeting(self, message, analysis, has_mood_data, mood_context, is_continuing, user_context=None):
        """Add mood-aware greeting for enhanced personalization"""
        
        # Skip greeting if continuing conversation
        if is_continuing:
            return None
        
        # Get user journey context
        entry_point = user_context.get('entry_point', 'direct_chat_access') if user_context else 'direct_chat_access'
        user_state = user_context.get('user_state', 'seeking_support') if user_context else 'seeking_support'
        has_tracked_mood = user_context.get('has_tracked_mood', False) if user_context else False
        
        # Create contextual greeting based on entry point
        entry_greetings = {
            'mood_analytics_referral': "I see you came here from your mood analytics dashboard! 📊 That's great that you're tracking your mental wellness.",
            'mood_checkin_referral': "Welcome! I noticed you just tracked your mood - thanks for staying aware of your mental state. 🌸",
            'direct_chat_access': "Hello! I'm Sahara, your AI mental wellness buddy. 🤗",
            'external_referral': "Welcome to Sahara! I'm glad you found us. 🌟",
            'organic_discovery': "Hi there! Great to meet you. I'm Sahara, here to support your mental wellness journey. ✨"
        }
        
        base_greeting = entry_greetings.get(entry_point, entry_greetings['direct_chat_access'])
        
        # Skip mood-specific greeting if no mood data and user hasn't tracked mood
        if not has_mood_data and not has_tracked_mood:
            return base_greeting + " How are you feeling today?"
            
        # Generate mood-aware greeting
        recent_emotion = mood_context.get('recent_emotion', 'neutral').lower()
        recent_rating = mood_context.get('recent_rating', 5)
        trend = mood_context.get('wellness_trend', 'stable')
        
        greeting_variants = {
            'happy': [
                f"Hey! 😊 I can see you've been feeling {recent_emotion} lately - that's wonderful!",
                f"Hi there! 🌟 Your recent mood shows you're doing well. I'm glad to see that!"
            ],
            'excited': [
                f"Hello! 🎉 I noticed you've been feeling {recent_emotion} - love that energy!",
                f"Hey! ✨ Your positive vibes are showing through your recent mood tracking!"
            ],
            'sad': [
                f"Hi... 🤗 I see you've been going through some tough times lately. I'm here for you.",
                f"Hey there. 💙 I noticed you've been feeling {recent_emotion} recently. Want to talk about it?"
            ],
            'anxious': [
                f"Hello. 🌸 I can see you've been feeling a bit anxious lately. Let's talk through this together.",
                f"Hi there. 😌 I noticed some anxiety in your recent mood entries. You're not alone in this."
            ],
            'stressed': [
                f"Hey. 🫂 I see you've been dealing with some stress recently. I'm here to help you work through it.",
                f"Hi. 🌿 Your recent mood shows you've been under pressure. Let's find some ways to ease that."
            ],
            'angry': [
                f"Hi there. 😤 I can see you've been feeling frustrated lately. Sometimes we all need to vent.",
                f"Hello. 💭 I noticed some anger in your recent mood tracking. Want to talk about what's bothering you?"
            ]
        }
        
        # Add trend-based context
        trend_messages = {
            'improving': " Things seem to be looking up for you recently! 📈",
            'declining': " I noticed things have been a bit challenging lately. 💪",
            'stable': " You've been pretty consistent with your mood lately."
        }
        
        # Select appropriate greeting
        if recent_emotion in greeting_variants:
            import random
            base_greeting = random.choice(greeting_variants[recent_emotion])
            if trend != 'stable':
                base_greeting += trend_messages.get(trend, '')
            return base_greeting
            
        # Default mood-aware greeting for other emotions
        if recent_rating >= 7:
            return f"Hi! 😊 I can see you've been feeling pretty good lately ({recent_rating}/10). That's great!"
        elif recent_rating <= 4:
            return f"Hey there. 🤗 I see you've been having some rough days recently ({recent_rating}/10). I'm here to listen."
        else:
            return f"Hello! 😌 I noticed you've been tracking your mood - that's a great step for self-awareness."
    
    def _get_mood_enhancement(self, mood_context):
        """Generate mood-aware enhancement for responses"""
        if not mood_context or not mood_context.get('has_recent_data'):
            return ""
            
        recent_emotion = mood_context.get('recent_emotion', 'neutral').lower()
        recent_rating = mood_context.get('recent_rating', 5)
        trend = mood_context.get('wellness_trend', 'stable')
        
        # Generate contextual enhancement based on mood
        if recent_emotion in ['sad', 'depressed', 'anxious', 'overwhelmed', 'hopeless'] or recent_rating <= 4:
            return " Given that you've been going through some tough times lately, I want you to know that what you're feeling is completely valid."
        elif recent_emotion in ['stressed', 'overwhelmed', 'pressured', 'burnt out'] or recent_rating == 5:
            return " I can see you've been dealing with some stress recently, so let's focus on practical steps that won't add more pressure."
        elif recent_emotion in ['angry', 'frustrated', 'irritated']:
            return " I noticed you've been feeling frustrated lately - sometimes academic pressure can build up and make everything feel more intense."
        elif trend == 'improving':
            return " It's great to see your mood has been improving recently! Let's keep building on that positive momentum."
        elif trend == 'declining':
            return " I see things have been getting tougher for you lately. Remember, it's okay to ask for help and take things one step at a time."
        else:
            return ""
    
    def _handle_academic_stress(self, message, analysis, is_continuing, mood_context=None):
        """Handle academic stress with specific strategies"""
        message_lower = message.lower()
        
        # Add mood-aware context if available
        mood_enhancement = self._get_mood_enhancement(mood_context)
        has_mood_data = mood_context.get('has_recent_data', False) if mood_context else False
        
        if 'physics' in message_lower and ('hard' in message_lower or 'difficult' in message_lower or 'lagta hai' in message_lower):
            base_message = f"Physics tough subject है, मैं समझ सकता हूं! 🔬 बहुत सारे students को Physics challenging लगती है।{mood_enhancement}\n\nPhysics के लिए कुछ tips:\n• Concepts को visual करने की कोशिश करें\n• Formula derivation समझें, रटें नहीं\n• Practice problems daily करें\n• Physics में maths strong होना जरूरी है\n\nकौन सा Physics topic आपको सबसे मुश्किल लग रहा है? Mechanics, Thermodynamics, या कुछ और? 🤔"
            return {
                'message': base_message,
                'context': 'physics_help',
                'follow_up': 'subject_specific'
            }
        elif 'burn' in message_lower and ('feel' in message_lower or 'ho raha' in message_lower):
            base_message = f"Burnout feel करना बहुत common है studies में। आपका body और mind दोनों rest मांग रहे हैं।{mood_enhancement} 😔\n\nBurnout से बचने के लिए:\n• Regular breaks लें (Pomodoro technique try करें)\n• Proper sleep जरूरी है\n• Physical activity include करें\n• Friends/family के साथ time spend करें\n\nक्या आप बहुत लंबे hours continuously study कर रहे हैं? Schedule थोड़ा adjust करना पड़ सकता है। 💆‍♀️"
            return {
                'message': base_message,
                'context': 'burnout_support',
                'follow_up': 'study_schedule'
            }
        elif 'marks' in message_lower and ('kam' in message_lower or 'less' in message_lower):
            return {
                'message': f"मैं समझ सकता हूं कि marks कम आने से आप upset हो रहे हैं। यह feeling बिल्कुल natural है। 📚\n\nलेकिन याद रखिए:\n• एक exam आपकी पूरी worth define नहीं करती\n• Competitive exams में हजारों students participate करते हैं\n• आपमें बहुत potential है\n\nक्या आप बताना चाहेंगे कि कौन सा subject या topic आपको सबसे ज्यादा challenging लगता है? मैं कुछ effective study strategies suggest कर सकता हूं। �",
                'context': 'academic_support',
                'follow_up': 'study_strategies'
            }
        else:
            return {
                'message': f"Studies का pressure feel करना normal है। आप अकेले नहीं हैं जो इससे गुजर रहे हैं। 🤗\n\nआपकी academic journey के बारे में और बताइए। कौन से subjects में help चाहिए?",
                'context': 'academic_support'
            }
    
    def _handle_family_pressure(self, message, analysis, is_continuing, mood_context=None):
        """Handle family pressure situations"""
        return {
            'message': f"Family expectations का pressure बहुत heavy हो सकता है। Indian families में यह common है लेकिन इससे आपकी feelings कम valid नहीं हो जातीं। 👨‍👩‍👧‍👦\n\nकभी-कभी parents अपने sapne हमारे through पूरे करना चाहते हैं। उनका प्यार है लेकिन pressure overwhelming हो जाता है।\n\nक्या आप बताना चाहेंगे कि exactly क्या expectations हैं जो आपको burden लग रही हैं?",
            'context': 'family_understanding'
        }
    
    def _handle_social_anxiety(self, message, analysis, is_continuing, mood_context=None):
        """Handle social anxiety and relationship issues"""
        return {
            'message': f"Social situations में awkward feel करना बहुत common है। आप अकेले नहीं हैं जो यह experience करता है। 😊\n\nConnection बनाना time लेता है, और हर person का अपना pace होता है।\n\nक्या कोई specific social situation है जो आपको particularly challenging लगती है?",
            'context': 'social_support'
        }
    
    def _handle_general_sadness(self, message, analysis, is_continuing, mood_context=None):
        """Handle general sadness and low mood"""
        return {
            'message': f"आपकी feelings को acknowledge करना important है। Sadness भी एक valid emotion है। 🤗\n\nकभी-कभी हमें exactly पता नहीं होता कि क्यों upset feel कर रहे हैं, और यह भी okay है।\n\nक्या कोई specific बात है जो आपको disturb कर रही है, या फिर general low feeling है?",
            'context': 'emotional_support'
        }
    
    def _handle_positive_sharing(self, message, analysis, is_continuing, mood_context=None):
        """Handle positive news and achievements"""
        return {
            'message': f"यह तो बहुत अच्छी बात है! 🎉 आपकी positivity सुनकर मुझे भी खुशी हुई।\n\nअच्छे moments को celebrate करना जरूरी है। आप बताना चाहेंगे कि क्या खुशी की बात है?",
            'context': 'celebration'
        }
    
    def _handle_general_conversation(self, message, analysis, is_continuing, mood_context=None, user_context=None):
        """Handle general conversation with better context awareness"""
        
        # Get journey context for more personalized responses
        entry_point = user_context.get('entry_point', 'direct_chat_access') if user_context else 'direct_chat_access'
        has_tracked_mood = user_context.get('has_tracked_mood', False) if user_context else False
        
        # Check if it's a follow-up about academic topics
        if any(word in message.lower() for word in ['physics', 'maths', 'chemistry', 'study', 'exam', 'subject']):
            return self._handle_academic_stress(message, analysis, is_continuing, mood_context)
        
        # Check for emotional words
        if any(word in message.lower() for word in ['sad', 'upset', 'depressed', 'worried', 'anxious']):
            return self._handle_general_sadness(message, analysis, is_continuing, mood_context)
            
        if is_continuing:
            # More natural responses for continuing conversations
            if analysis['emotion'] != 'neutral':
                return {
                    'message': f"Hmm, I can totally sense that you're feeling {analysis['emotion']} about this 🤗 Aur you know what? It's completely okay to feel this way.\n\nI'm genuinely listening to everything you're saying. Want to tell me more about what's going on? I'm here for you yaar! 💙",
                    'context': 'empathetic_listening'
                }
            else:
                return {
                    'message': f"I'm really glad you're talking to me about this 😊 Seriously, it means a lot that you trust me enough to share.\n\nWhat's really on your mind today? Kuch bhi ho - studies, family, friends, या just random thoughts. I'm all ears! ✨",
                    'context': 'active_listening'
                }
        else:
            return {
                'message': f"नमस्ते! मैं Sahara हूं। 🌸 मैं यहां आपकी बात सुनने के लिए हूं।\n\nआप कैसा feel कर रहे हैं आज? कोई भी बात share कर सकते हैं - मैं judge नहीं करूंगा।",
                'context': 'greeting'
            }


    def get_response(self, message, user_context=None, mood_context=None):
        """Main function to get intelligent AI response with mood awareness"""
        
        # Extract session ID for context
        session_id = user_context.get('session_id', 'anonymous') if user_context else 'anonymous'
        
        # Generate intelligent response using new system with mood context
        response = self.generate_intelligent_response(message, session_id, mood_context, user_context)
        
        return response
    
    def get_relevant_resources(self, context):
        resource_mapping = {
            'academic_pressure': ['study_techniques', 'stress_management', 'breathing_exercises'],
            'family_expectations': ['communication_tips', 'career_guidance', 'self_advocacy'],
            'anxiety': ['breathing_exercises', 'mindfulness', 'anxiety_management'],
            'depression': ['professional_help', 'mood_boosters', 'support_groups'],
            'relationships': ['social_skills', 'communication_tips', 'peer_support'],
            'identity': ['self_discovery', 'goal_setting', 'personal_growth']
        }
        return resource_mapping.get(context, ['general_wellness'])

# Mood Context Functions
def get_mood_context(user=None):
    """Get recent mood context for AI chat enhancement"""
    mood_context = {
        'has_recent_data': False,
        'recent_rating': None,
        'recent_emotion': None,
        'dominant_emotions': [],
        'wellness_trend': 'stable',
        'context_summary': ''
    }
    
    try:
        if user and user.is_authenticated:
            # Get user's recent mood entries from database
            recent_entries = MoodEntry.query.filter_by(user_id=user.id)\
                           .order_by(MoodEntry.timestamp.desc())\
                           .limit(5).all()
                           
            if recent_entries:
                mood_context['has_recent_data'] = True
                latest = recent_entries[0]
                mood_context['recent_rating'] = latest.rating
                mood_context['recent_emotion'] = latest.emotion
                
                # Analyze dominant emotions
                emotions = [entry.emotion for entry in recent_entries]
                emotion_counts = {}
                for emotion in emotions:
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                mood_context['dominant_emotions'] = sorted(emotion_counts.keys(), 
                                                         key=emotion_counts.get, reverse=True)[:3]
                
                # Determine wellness trend
                ratings = [entry.rating for entry in recent_entries]
                if len(ratings) >= 2:
                    if ratings[0] > ratings[-1]:
                        mood_context['wellness_trend'] = 'improving'
                    elif ratings[0] < ratings[-1]:
                        mood_context['wellness_trend'] = 'declining' 
                
        else:
            # For anonymous users, check localStorage equivalent
            # This will be handled on frontend and passed to chat endpoint
            pass
            
        # Generate context summary
        if mood_context['has_recent_data']:
            emotion = mood_context['recent_emotion']
            rating = mood_context['recent_rating']
            trend = mood_context['wellness_trend']
            
            mood_context['context_summary'] = f"Recent mood: {emotion} ({rating}/10), trend: {trend}"
            
    except Exception as e:
        print(f"Error getting mood context: {e}")
        
    return mood_context

# Initialize AI
sahara_ai = SaharaAI()

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        next_page = data.get('next', '/')
        
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return jsonify({'success': True, 'message': 'Account created successfully', 'redirect': next_page})
    
    next_page = request.args.get('next', '/')
    return render_template('login_simple.html', next_page=next_page)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        next_page = data.get('next', '/')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return jsonify({'success': True, 'message': 'Login successful', 'redirect': next_page})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'})
    
    next_page = request.args.get('next', '/')
    return render_template('login_simple.html', next_page=next_page)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    
    # Handle AJAX requests (POST from Alpine.js)
    if request.method == 'POST':
        return jsonify({'success': True, 'message': 'Logout successful'})
    
    # Handle regular GET requests with redirects
    from_url = request.args.get('from')
    if from_url and '/mood-analytics' in from_url:
        return redirect(url_for('mood_analytics_dashboard'))
    elif from_url:
        # For other authenticated pages, redirect to landing
        return redirect(url_for('landing'))
    else:
        # Default redirect based on referrer
        referrer = request.referrer
        if referrer and 'mood-analytics' in referrer:
            return redirect(url_for('mood_analytics_dashboard'))
        else:
            return redirect(url_for('landing'))

@app.route('/profile')
@login_required
def profile():
    user_chats = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).all()
    
    # Generate insights
    total_chats = len(user_chats)
    recent_moods = [chat.mood for chat in user_chats[:10] if chat.mood]
    common_topics = ['stress', 'anxiety', 'studies', 'family', 'relationships']
    
    # Basic mood analysis
    mood_distribution = {}
    for mood in recent_moods:
        mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
    
    insights = {
        'total_conversations': total_chats,
        'active_days': len(set(chat.timestamp.date() for chat in user_chats)),
        'most_common_mood': max(mood_distribution, key=mood_distribution.get) if mood_distribution else None,
        'improvement_trend': 'positive' if len([m for m in recent_moods[-5:] if m in ['happy', 'excited', 'calm']]) > 2 else 'stable'
    }
    
    return jsonify({
        'user': {
            'username': current_user.username,
            'email': current_user.email,
            'joined': current_user.created_at.strftime('%B %Y')
        },
        'chats': [{
            'message': chat.message,
            'response': chat.response,
            'timestamp': chat.timestamp.strftime('%Y-%m-%d %H:%M'),
            'mood': chat.mood
        } for chat in user_chats],
        'insights': insights
    })

@app.route('/user-insights')
@login_required 
def user_insights():
    """Get personalized insights for the user"""
    user_chats = ChatHistory.query.filter_by(user_id=current_user.id).all()
    
    if not user_chats:
        return jsonify({
            'message': 'Start chatting to see your personalized insights!',
            'tips': [
                'Share your daily experiences with Sahara',
                'Track your mood regularly', 
                'Use Sahara when you need support'
            ]
        })
    
    # Analyze conversation patterns
    total_conversations = len(user_chats)
    dates_active = set(chat.timestamp.date() for chat in user_chats)
    consistency_score = len(dates_active) / max(1, (datetime.now().date() - min(dates_active)).days) * 100
    
    # Generate personalized message
    insights_message = f"""
    🌟 आपकी Sahara journey: 
    
    📊 आपने {total_conversations} बातचीत की हैं
    📅 {len(dates_active)} दिनों में active रहे हैं  
    💪 Consistency: {consistency_score:.1f}%
    
    Keep growing with Sahara! आप बहुत अच्छा कर रहे हैं। 💚
    """
    
    return jsonify({
        'message': insights_message,
        'stats': {
            'total_chats': total_conversations,
            'active_days': len(dates_active),
            'consistency': round(consistency_score, 1)
        }
    })

@app.route('/')
def landing():
    return render_template('landing.html', current_user=current_user)

@app.route('/chat')
def chat_interface():
    # Get user mood data for context-aware chat
    recent_mood_data = None
    user_context = None
    
    if current_user.is_authenticated:
        # Get user's most recent mood entries for context
        recent_moods = MoodEntry.query.filter_by(user_id=current_user.id)\
                                    .order_by(MoodEntry.timestamp.desc())\
                                    .limit(5).all()
        
        if recent_moods:
            latest_mood = recent_moods[0]
            recent_mood_data = {
                'latest_mood': latest_mood.mood_label,  # Use mood_label instead of mood
                'intensity': latest_mood.mood_intensity,  # Use mood_intensity instead of intensity
                'notes': getattr(latest_mood, 'notes', ''),  # Safe access to notes
                'timestamp': latest_mood.timestamp.isoformat(),
                'recent_entries_count': len(recent_moods),
                'mood_trend': [{'mood': m.mood_label, 'intensity': m.mood_intensity, 'timestamp': m.timestamp.isoformat()} for m in recent_moods]
            }
        
        user_context = {
            'is_authenticated': True,
            'username': current_user.username,
            'email': current_user.email,
            'id': current_user.id,
            'created_at': current_user.created_at.isoformat() if hasattr(current_user, 'created_at') else None,
            'has_tracked_mood': recent_mood_data is not None,  # Add flag for mood tracking status
            'mood_entries_count': len(recent_moods) if recent_moods else 0
        }
    else:
        # Check for anonymous session mood data
        session_id = session.get('session_id')
        if session_id:
            # Get anonymous mood data from localStorage or session
            user_context = {
                'is_authenticated': False,
                'session_id': session_id,
                'is_anonymous': True
            }
    
    return render_template('index_chatgpt.html', 
                         current_user=current_user,
                         user_context=user_context,
                         recent_mood_data=recent_mood_data)

@app.route('/chat-secure')
@login_required
def secure_chat():
    return render_template('index_chatgpt.html')

@app.route('/modern')
def modern():
    return render_template('index_modern.html')

@app.route('/classic')
def classic():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    user_context = data.get('context', {})
    anonymous_mood_data = data.get('mood_data', {})  # For anonymous users
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Add session management for conversation continuity
    if 'session_id' not in user_context:
        import uuid
        user_context['session_id'] = str(uuid.uuid4())
    
    # Get mood context for AI enhancement
    mood_context = get_mood_context(current_user if current_user.is_authenticated else None)
    
    # For anonymous users, use frontend-provided mood data
    if not current_user.is_authenticated and anonymous_mood_data:
        mood_context.update({
            'has_recent_data': True,
            'recent_rating': anonymous_mood_data.get('recent_rating'),
            'recent_emotion': anonymous_mood_data.get('recent_emotion'),
            'dominant_emotions': anonymous_mood_data.get('dominant_emotions', []),
            'wellness_trend': anonymous_mood_data.get('wellness_trend', 'stable'),
            'context_summary': f"Recent mood: {anonymous_mood_data.get('recent_emotion', 'neutral')} ({anonymous_mood_data.get('recent_rating', 5)}/10)"
        })
    
    # Extract user journey context for enhanced responses
    user_journey = user_context.get('user_journey', {})
    entry_point = user_journey.get('entry_point', 'direct_chat_access')
    user_state = user_journey.get('user_state', 'seeking_support')
    
    # Add journey context to user_context for AI processing
    user_context['entry_point'] = entry_point
    user_context['user_state'] = user_state
    user_context['has_tracked_mood'] = user_journey.get('has_tracked_mood', False)
    user_context['session_duration'] = user_journey.get('session_duration', 0)
    
    response = sahara_ai.get_response(message, user_context, mood_context)
    response['session_id'] = user_context['session_id']  # Return session ID for frontend
    
    # Save chat history for logged-in users
    if current_user.is_authenticated:
        chat_history = ChatHistory(
            user_id=current_user.id,
            message=message,
            response=response.get('response', ''),
            mood=user_context.get('mood'),
            session_id=user_context['session_id']
        )
        db.session.add(chat_history)
        db.session.commit()
    
    return jsonify(response)

@app.route('/mood', methods=['POST'])
def track_mood():
    data = request.get_json()
    mood_emoji = data.get('mood_emoji')
    mood_label = data.get('mood_label')
    mood_intensity = data.get('mood_intensity', 3)
    notes = data.get('notes', '')
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    try:
        # Only save to database if user is authenticated
        if current_user.is_authenticated:
            mood_entry = MoodEntry(
                user_id=current_user.id,
                mood_emoji=mood_emoji,
                mood_label=mood_label,
                mood_intensity=int(mood_intensity),
                notes=notes,
                session_id=session_id
            )
            
            db.session.add(mood_entry)
            db.session.commit()
            
            response_data = mood_entry.to_dict()
        else:
            # For anonymous users, return data without saving to database
            response_data = {
                'id': str(uuid.uuid4()),
                'mood_emoji': mood_emoji,
                'mood_label': mood_label,
                'mood_intensity': int(mood_intensity),
                'notes': notes,
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': None,
                'anonymous': True
            }
        
        # Generate personalized insight
        insight_message = generate_mood_insight(mood_label, mood_intensity, current_user.is_authenticated)
        
        return jsonify({
            'success': True,
            'message': 'Mood tracked successfully',
            'insight': insight_message,
            'mood_entry': response_data,
            'is_authenticated': current_user.is_authenticated
        })
    
    except Exception as e:
        if current_user.is_authenticated:
            db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to track mood',
            'error': str(e)
        }), 500

def generate_mood_insight(mood_label, intensity, is_authenticated):
    """Generate personalized insight based on mood"""
    intensity_words = {1: "बहुत कम", 2: "कम", 3: "ठीक-ठाक", 4: "अच्छा", 5: "बहुत अच्छा"}
    
    if mood_label in ['happy', 'excited', 'grateful']:
        return f"खुशी देखकर अच्छा लगा! आपका मूड {intensity_words.get(intensity, 'ठीक-ठाक')} है। इस positive energy को बनाए रखें! 😊"
    elif mood_label in ['sad', 'stressed', 'anxious']:
        return f"समझ सकते हैं कि आप {mood_label} feel कर रहे हैं। ये normal है। थोड़ी deep breathing try करें या मुझसे बात करें। 💙"
    elif mood_label in ['angry', 'frustrated']:
        return f"गुस्सा आना बिल्कुल normal है। थोड़ा time लें, कुछ देर walk करें या music सुनें। मैं यहाँ हूँ अगर बात करनी हो। 🌱"
    else:
        return f"आपका आज का मूड: {mood_label}। धन्यवाद कि आपने अपनी भावनाओं को साझा किया। हर दिन अलग होता है! 🌟"

@app.route('/mood-history')
def get_mood_history():
    """Get mood history - only for authenticated users"""
    try:
        if current_user.is_authenticated:
            mood_entries = MoodEntry.query.filter_by(user_id=current_user.id)\
                                        .order_by(MoodEntry.timestamp.desc())\
                                        .limit(30).all()
            
            return jsonify({
                'success': True,
                'mood_entries': [entry.to_dict() for entry in mood_entries],
                'analytics': generate_mood_analytics(mood_entries),
                'is_authenticated': True
            })
        else:
            # For anonymous users, return empty data (frontend will use localStorage)
            return jsonify({
                'success': True,
                'mood_entries': [],
                'analytics': {
                    'total_entries': 0,
                    'mood_distribution': {},
                    'average_intensity': 0,
                    'recent_trend': 'No data available'
                },
                'is_authenticated': False,
                'message': 'Anonymous users data is stored locally only'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/mood-checkin')
def mood_checkin_page():
    """Render mood check-in page"""
    return render_template('mood_checkin.html')

@app.route('/mood-test')
def mood_test():
    """Test the fixed mood check-in page"""
    return render_template('mood_checkin_fixed.html')

@app.route('/mood-analytics')
def mood_analytics_dashboard():
    """Render the modern mood analytics dashboard with user context"""
    user_data = {
        'is_authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False,
        'username': current_user.username if current_user.is_authenticated else None,
        'user_id': current_user.id if current_user.is_authenticated else None
    }
    return render_template('mood_analytics_dashboard.html', user=user_data)

def generate_mood_analytics(mood_entries):
    """Generate comprehensive analytics from mood entries"""
    from datetime import datetime, timedelta
    
    if not mood_entries:
        return {
            'total_entries': 0,
            'average_intensity': 0.0,
            'current_streak': 0,
            'wellness_score': 0.0,
            'mood_distribution': {},
            'trend': 'No data available',
            'streak_message': 'Start tracking to build your streak!',
            'wellness_message': 'Begin your wellness journey'
        }
    
    total_entries = len(mood_entries)
    
    # Calculate emotion-aware average mood score (considering emotion type + intensity)
    def calculate_mood_score(entry):
        """Calculate actual mood score considering emotion valence and intensity"""
        emotion_valence = {
            'happy': 1.0, 'excited': 1.0, 'content': 0.8, 'calm': 0.7,
            'hopeful': 0.9, 'grateful': 0.9, 'neutral': 0.5, 'tired': 0.3,
            'bored': 0.4, 'confused': 0.3, 'worried': 0.2, 'stressed': 0.2,
            'anxious': 0.1, 'sad': 0.1, 'angry': 0.0, 'frustrated': 0.1,
            'depressed': 0.0, 'overwhelmed': 0.1
        }
        
        valence = emotion_valence.get(entry.mood_label.lower(), 0.5)
        
        if valence >= 0.5:  # Positive emotion
            return valence * entry.mood_intensity
        else:  # Negative emotion - higher intensity = worse mood
            return valence * (11 - entry.mood_intensity)
    
    # Calculate proper average mood considering emotion types
    mood_scores = [calculate_mood_score(entry) for entry in mood_entries]
    avg_intensity = sum(mood_scores) / len(mood_scores)
    
    # Count mood distribution
    mood_counts = {}
    for entry in mood_entries:
        mood_counts[entry.mood_label] = mood_counts.get(entry.mood_label, 0) + 1
    
    # Calculate current streak (consecutive days with entries)
    current_streak = calculate_mood_streak(mood_entries)
    
    # Calculate wellness score (based on intensity, consistency, and positive trends)
    wellness_score = calculate_wellness_score(mood_entries)
    
    # Determine trend
    trend = calculate_mood_trend(mood_entries)
    
    # Generate motivational messages
    streak_message = get_streak_message(current_streak)
    wellness_message = get_wellness_message(wellness_score)
    
    return {
        'total_entries': total_entries,
        'average_intensity': round(avg_intensity, 1),
        'current_streak': current_streak,
        'wellness_score': round(wellness_score, 1),
        'mood_distribution': mood_counts,
        'trend': trend,
        'streak_message': streak_message,
        'wellness_message': wellness_message
    }

def calculate_mood_streak(mood_entries):
    """Calculate current consecutive day streak"""
    if not mood_entries:
        return 0
    
    from datetime import datetime, timedelta
    
    # Sort entries by date (newest first)
    sorted_entries = sorted(mood_entries, key=lambda x: x.timestamp, reverse=True)
    
    # Get unique dates (in case multiple entries per day)
    unique_dates = []
    seen_dates = set()
    
    for entry in sorted_entries:
        date_only = entry.timestamp.date()
        if date_only not in seen_dates:
            unique_dates.append(date_only)
            seen_dates.add(date_only)
    
    if not unique_dates:
        return 0
    
    # Calculate streak starting from most recent date
    today = datetime.now().date()
    streak = 0
    
    # Check if there's an entry today or yesterday
    most_recent = unique_dates[0]
    if most_recent == today:
        streak = 1
        check_date = today - timedelta(days=1)
    elif most_recent == today - timedelta(days=1):
        streak = 1
        check_date = most_recent - timedelta(days=1)
    else:
        return 0  # No recent activity
    
    # Count consecutive days backwards
    for date in unique_dates[1:]:
        if date == check_date:
            streak += 1
            check_date = check_date - timedelta(days=1)
        else:
            break
    
    return streak

def calculate_wellness_score(mood_entries):
    """Calculate wellness score based on current mental state considering both emotion type and intensity (0-10 scale)"""
    if not mood_entries:
        return 0.0
    
    from datetime import datetime, timedelta
    
    # Define emotion valence (how positive/negative each emotion is)
    emotion_valence = {
        'happy': 1.0,    # Very positive
        'excited': 1.0,  # Very positive  
        'content': 0.8,  # Positive
        'calm': 0.7,     # Positive
        'hopeful': 0.9,  # Very positive
        'grateful': 0.9, # Very positive
        'neutral': 0.5,  # Neutral
        'tired': 0.3,    # Slightly negative
        'bored': 0.4,    # Slightly negative
        'confused': 0.3, # Slightly negative
        'worried': 0.2,  # Negative
        'stressed': 0.2, # Negative
        'anxious': 0.1,  # Very negative
        'sad': 0.1,      # Very negative
        'angry': 0.0,    # Very negative
        'frustrated': 0.1, # Very negative
        'depressed': 0.0,  # Very negative
        'overwhelmed': 0.1 # Very negative
    }
    
    def calculate_entry_wellness(entry):
        """Calculate wellness score for a single entry (0-10)"""
        # Get emotion valence (default to neutral if unknown emotion)
        valence = emotion_valence.get(entry.mood_label.lower(), 0.5)
        
        # Convert intensity (1-10) to wellness impact
        # For positive emotions: higher intensity = better wellness
        # For negative emotions: higher intensity = worse wellness  
        if valence >= 0.5:  # Positive or neutral emotion
            wellness = valence * entry.mood_intensity
        else:  # Negative emotion
            # For negative emotions, higher intensity means worse wellness
            # angry with intensity 10 = extremely angry = very bad wellness (near 0)
            # angry with intensity 1 = slightly angry = somewhat bad wellness 
            wellness = valence * (11 - entry.mood_intensity)
        
        return min(max(wellness, 0), 10)  # Ensure 0-10 range
    
    # Prioritize recent entries (last 7 days) - 70% weight
    recent_cutoff = datetime.now() - timedelta(days=7)
    recent_entries = [e for e in mood_entries if e.timestamp >= recent_cutoff]
    
    if recent_entries:
        # Calculate wellness for recent entries
        recent_wellness_scores = [calculate_entry_wellness(entry) for entry in recent_entries]
        recent_avg = sum(recent_wellness_scores) / len(recent_wellness_scores)
        
        # Today's mood (if exists) gets extra weight
        today = datetime.now().date()
        today_entries = [e for e in recent_entries if e.timestamp.date() == today]
        if today_entries:
            today_wellness_scores = [calculate_entry_wellness(entry) for entry in today_entries]
            today_avg = sum(today_wellness_scores) / len(today_wellness_scores)
            recent_score = (recent_avg * 0.3) + (today_avg * 0.7)  # Heavily weight today's mood
        else:
            recent_score = recent_avg
        
        recent_weighted = recent_score * 0.7
    else:
        # No recent data, use overall average with penalty
        all_wellness_scores = [calculate_entry_wellness(entry) for entry in mood_entries]
        recent_weighted = (sum(all_wellness_scores) / len(all_wellness_scores)) * 0.5
    
    # Overall trend factor - 20% weight
    trend_score = 0
    if len(mood_entries) >= 4:
        # Compare last 2 entries with previous 2 entries
        recent_two = mood_entries[:2]
        previous_two = mood_entries[2:4]
        
        recent_wellness = sum(calculate_entry_wellness(e) for e in recent_two) / len(recent_two)
        previous_wellness = sum(calculate_entry_wellness(e) for e in previous_two) / len(previous_two)
        
        if recent_wellness > previous_wellness + 1:
            trend_score = 2.0  # Significant improvement
        elif recent_wellness > previous_wellness:
            trend_score = 1.0  # Improving
        elif recent_wellness == previous_wellness:
            trend_score = 0.5  # Stable
        else:
            trend_score = 0  # Declining (concerning)
    else:
        # Not enough data, give neutral score
        trend_score = 0.5
    
    trend_weighted = trend_score * 0.2
    
    # Consistency factor - 10% weight (minimal impact)
    consistency_score = min(len(recent_entries if recent_entries else mood_entries) / 7.0, 1.0) * 1.0
    consistency_weighted = consistency_score * 0.1
    
    # Calculate final score
    final_score = recent_weighted + trend_weighted + consistency_weighted
    
    return min(round(final_score, 1), 10.0)

def calculate_mood_trend(mood_entries):
    """Calculate mood trend description using emotion-aware scoring"""
    if len(mood_entries) < 3:
        return "Building data"
    
    # Define emotion valence for proper mood scoring
    emotion_valence = {
        'happy': 1.0, 'excited': 1.0, 'content': 0.8, 'calm': 0.7,
        'hopeful': 0.9, 'grateful': 0.9, 'neutral': 0.5, 'tired': 0.3,
        'bored': 0.4, 'confused': 0.3, 'worried': 0.2, 'stressed': 0.2,
        'anxious': 0.1, 'sad': 0.1, 'angry': 0.0, 'frustrated': 0.1,
        'depressed': 0.0, 'overwhelmed': 0.1
    }
    
    def calculate_mood_score(entry):
        valence = emotion_valence.get(entry.mood_label.lower(), 0.5)
        if valence >= 0.5:
            return valence * entry.mood_intensity
        else:
            return valence * (11 - entry.mood_intensity)
    
    # Compare recent entries with older ones using proper mood scores
    recent_scores = [calculate_mood_score(e) for e in mood_entries[:3]]
    recent_avg = sum(recent_scores) / len(recent_scores)
    
    if len(mood_entries) >= 6:
        older_scores = [calculate_mood_score(e) for e in mood_entries[3:6]]
        older_avg = sum(older_scores) / len(older_scores)
        diff = recent_avg - older_avg
        
        if diff > 1:
            return "Significantly improving"
        elif diff > 0.5:
            return "Improving"
        elif diff < -1:
            return "Needs attention"
        elif diff < -0.5:
            return "Declining"
        else:
            return "Stable"
    else:
        # Not enough data for comparison
        if recent_avg >= 7:
            return "Doing well"
        elif recent_avg >= 5:
            return "Moderate"
        else:
            return "Needs support"

def get_streak_message(streak):
    """Get motivational streak message"""
    if streak == 0:
        return "Start your wellness streak today!"
    elif streak == 1:
        return "Great start! Keep it going!"
    elif streak < 7:
        return f"Amazing! {streak} days strong!"
    elif streak < 30:
        return f"Incredible consistency! {streak} days!"
    else:
        return f"Wellness champion! {streak} days!"

def get_wellness_message(score):
    """Get wellness score message based on current mental state"""
    if score >= 8:
        return "You're doing great mentally!"
    elif score >= 6:
        return "Good mental health balance"
    elif score >= 4:
        return "Room for improvement"
    elif score >= 2:
        return "Focus on self-care"
    else:
        return "Consider seeking support"

@app.route('/resources')
def get_resources():
    """Render resources page with wellness content"""
    return render_template('resources.html')

@app.route('/resources-data')
def get_resources_data():
    """API endpoint for resources JSON data"""
    return jsonify(resources_data)

@app.route('/crisis-support')
def crisis_support():
    """Crisis support page with immediate help resources"""
    crisis_data = resources_data.get('crisis_support', {})
    return render_template('crisis_support.html', crisis_data=crisis_data)

@app.route('/dashboard')
def dashboard():
    """User dashboard with mood analytics and insights"""
    user_data = {
        'is_authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False,
        'username': current_user.username if current_user.is_authenticated else None,
    }
    return render_template('dashboard.html', user_data=user_data)

@app.route('/achievements', methods=['POST'])
def achievements():
    data = request.get_json()
    session_id = data.get('session_id', 'anonymous')
    
    # Simple achievement logic
    achievements = ['first_chat']  # Default achievement
    
    return jsonify({
        'achievements': achievements,
        'message': 'Achievements retrieved successfully'
    })

@app.route('/analytics', methods=['POST'])
def analytics():
    """Collect analytics data for improving user experience"""
    data = request.get_json()
    
    # In production, you would store this in a database
    # For demo purposes, we'll just log it
    print(f"Analytics: {data.get('event')} - Session: {data.get('session_id')}")
    
    return jsonify({'status': 'recorded'})

@app.route('/manifest.json')
def manifest():
    """Serve PWA manifest"""
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    """Serve service worker"""
    return send_from_directory('static', 'sw.js')

# Initialize database tables
try:
    with app.app_context():
        db.create_all()
except Exception as e:
    print(f"Database initialization error: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='127.0.0.1')
