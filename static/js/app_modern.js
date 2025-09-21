// Modern Sahara App - Enhanced JavaScript

class SaharaAppModern {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.messages = [];
        this.currentMood = null;
        this.achievements = new Set();
        this.resources = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadResources();
        this.loadAchievements();
        this.setupMoodCalendar();
        this.loadFromStorage();
        this.initializeAnimations();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    setupEventListeners() {
        // Enhanced message input
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Real-time typing animation
            messageInput.addEventListener('input', this.showTypingIndicator.bind(this));
        }

        // Voice input (if supported)
        this.setupVoiceInput();
        
        // Service Worker for PWA
        this.registerServiceWorker();
    }

    async sendMessage() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Clear input and show typing
        input.value = '';
        this.addMessage(message, 'user');
        this.showAITyping(true);

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    context: { session_id: this.sessionId }
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Simulate realistic AI thinking time
                await this.delay(1500);
                
                this.showAITyping(false);
                this.addMessage(data.message, 'ai');
                
                // Check for achievements
                this.checkAchievements(message, data);
                
                // Save to storage
                this.saveToStorage();
                
                // Analytics
                this.trackInteraction('chat_message', {
                    user_message: message,
                    ai_response_source: data.source || 'unknown'
                });
            }
        } catch (error) {
            this.showAITyping(false);
            this.addMessage('Sorry, I encountered an error. Please try again! 😊', 'ai');
            console.error('Chat error:', error);
        }
    }

    addMessage(text, sender) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex items-start space-x-3 ${sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`;
        
        const timestamp = new Date().toLocaleTimeString('en-IN', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-user text-white text-sm"></i>
                </div>
                <div class="chat-bubble chat-bubble-user max-w-md">
                    <p class="text-white">${this.formatMessage(text)}</p>
                    <div class="text-xs text-blue-100 mt-1">${timestamp}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-robot text-white text-sm"></i>
                </div>
                <div class="chat-bubble chat-bubble-ai max-w-md">
                    <div class="text-gray-800">${this.formatMessage(text)}</div>
                    <div class="text-xs text-gray-500 mt-2 flex items-center justify-between">
                        <span>${timestamp}</span>
                        <div class="flex space-x-1">
                            <button onclick="this.copyMessage('${text}')" class="text-gray-400 hover:text-primary text-xs">
                                <i class="fas fa-copy"></i>
                            </button>
                            <button onclick="this.likeMessage()" class="text-gray-400 hover:text-green-500 text-xs">
                                <i class="fas fa-thumbs-up"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        // Add with animation
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        messagesContainer.appendChild(messageDiv);

        // Animate in
        setTimeout(() => {
            messageDiv.style.transition = 'all 0.3s ease-out';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 10);

        this.scrollToBottom();
        
        // Store message
        this.messages.push({
            text,
            sender,
            timestamp: Date.now()
        });
    }

    formatMessage(text) {
        // Enhanced text formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" class="text-blue-500 hover:underline">$1</a>');
    }

    showAITyping(show) {
        const messagesContainer = document.getElementById('chat-messages');
        const existingTyping = messagesContainer.querySelector('.typing-indicator');
        
        if (existingTyping) {
            existingTyping.remove();
        }
        
        if (show) {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing-indicator flex items-start space-x-3';
            typingDiv.innerHTML = `
                <div class="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-robot text-white text-sm"></i>
                </div>
                <div class="bg-white rounded-2xl rounded-tl-md p-4 shadow-sm border">
                    <div class="flex space-x-1">
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style="animation-delay: 0.4s"></div>
                    </div>
                </div>
            `;
            messagesContainer.appendChild(typingDiv);
            this.scrollToBottom();
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Mood Tracking with Enhanced UI
    async recordMood(mood) {
        const moodButtons = document.querySelectorAll('.mood-btn');
        moodButtons.forEach(btn => btn.classList.remove('selected'));
        
        event.target.closest('.mood-btn').classList.add('selected');
        
        this.currentMood = mood;
        const today = new Date().toISOString().split('T')[0];
        
        try {
            const response = await fetch('/mood', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mood: mood,
                    date: today,
                    session_id: this.sessionId
                })
            });

            if (response.ok) {
                this.showNotification('Mood recorded! 💙', 'success');
                this.updateMoodCalendar();
                this.checkMoodAchievements();
                
                // Analytics
                this.trackInteraction('mood_record', { mood, date: today });
            }
        } catch (error) {
            this.showNotification('Failed to record mood. Please try again.', 'error');
            console.error('Mood recording error:', error);
        }
    }

    setupMoodCalendar() {
        const calendar = document.getElementById('mood-calendar');
        if (!calendar) return;

        const today = new Date();
        const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        
        let calendarHTML = '<div class="grid grid-cols-7 gap-2 text-center">';
        
        // Days of week header
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        days.forEach(day => {
            calendarHTML += `<div class="text-sm font-semibold text-gray-600 p-2">${day}</div>`;
        });
        
        // Empty cells for start of month
        for (let i = 0; i < startOfMonth.getDay(); i++) {
            calendarHTML += '<div class="p-2"></div>';
        }
        
        // Days of month
        for (let day = 1; day <= endOfMonth.getDate(); day++) {
            const date = new Date(today.getFullYear(), today.getMonth(), day);
            const dateStr = date.toISOString().split('T')[0];
            const isToday = day === today.getDate();
            const mood = this.getMoodForDate(dateStr);
            
            calendarHTML += `
                <div class="p-2 rounded-lg hover:bg-gray-100 transition-colors ${isToday ? 'ring-2 ring-primary' : ''}" 
                     title="${dateStr}">
                    <div class="text-sm font-medium">${day}</div>
                    <div class="text-lg">${this.getMoodEmoji(mood)}</div>
                </div>
            `;
        }
        
        calendarHTML += '</div>';
        calendar.innerHTML = calendarHTML;
    }

    getMoodEmoji(mood) {
        const moodEmojis = {
            'very-happy': '😄',
            'happy': '😊',
            'neutral': '😐',
            'sad': '😢',
            'very-sad': '😭'
        };
        return moodEmojis[mood] || '⭕';
    }

    getMoodForDate(date) {
        const stored = localStorage.getItem('sahara_moods');
        if (stored) {
            const moods = JSON.parse(stored);
            return moods[date] || null;
        }
        return null;
    }

    // Enhanced Resources Loading
    async loadResources() {
        try {
            const response = await fetch('/resources');
            const resources = await response.json();
            
            const container = document.getElementById('resources-grid');
            if (!container) return;
            
            container.innerHTML = resources.map(resource => `
                <div class="modern-card resource-card interactive-hover" onclick="this.openResource('${resource.id}')">
                    <div class="flex items-start space-x-4">
                        <div class="w-12 h-12 bg-gradient-to-br ${this.getResourceColor(resource.category)} rounded-xl flex items-center justify-center flex-shrink-0">
                            <i class="${this.getResourceIcon(resource.category)} text-white text-lg"></i>
                        </div>
                        <div class="flex-1">
                            <h3 class="text-lg font-semibold text-gray-900 mb-2">${resource.title}</h3>
                            <p class="text-gray-600 text-sm mb-3">${resource.description}</p>
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-medium px-2 py-1 bg-gray-100 text-gray-700 rounded-full">
                                    ${resource.category}
                                </span>
                                <span class="text-xs text-gray-500">${resource.readTime || '5 min read'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
            
        } catch (error) {
            console.error('Failed to load resources:', error);
        }
    }

    getResourceColor(category) {
        const colors = {
            'breathing': 'from-blue-500 to-blue-600',
            'meditation': 'from-purple-500 to-purple-600',
            'exercise': 'from-green-500 to-green-600',
            'sleep': 'from-indigo-500 to-indigo-600',
            'nutrition': 'from-orange-500 to-orange-600',
            'social': 'from-pink-500 to-pink-600',
            'default': 'from-gray-500 to-gray-600'
        };
        return colors[category] || colors.default;
    }

    getResourceIcon(category) {
        const icons = {
            'breathing': 'fas fa-wind',
            'meditation': 'fas fa-om',
            'exercise': 'fas fa-running',
            'sleep': 'fas fa-moon',
            'nutrition': 'fas fa-apple-alt',
            'social': 'fas fa-users',
            'default': 'fas fa-book'
        };
        return icons[category] || icons.default;
    }

    // Achievement System
    async loadAchievements() {
        try {
            const response = await fetch('/achievements', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ session_id: this.sessionId })
            });
            
            const data = await response.json();
            this.displayAchievements(data.achievements || []);
            
        } catch (error) {
            console.error('Failed to load achievements:', error);
        }
    }

    displayAchievements(achievements) {
        const container = document.getElementById('achievements-grid');
        if (!container) return;
        
        const allAchievements = [
            { id: 'first_chat', name: 'First Chat', icon: 'fa-comments', description: 'Started your first conversation' },
            { id: 'mood_tracker', name: 'Mood Tracker', icon: 'fa-heart', description: 'Recorded your mood' },
            { id: 'week_streak', name: 'Weekly Warrior', icon: 'fa-fire', description: '7 days of check-ins' },
            { id: 'resource_explorer', name: 'Explorer', icon: 'fa-compass', description: 'Explored resources' },
            { id: 'share_feelings', name: 'Open Heart', icon: 'fa-heart-broken', description: 'Shared deep feelings' },
            { id: 'positive_mood', name: 'Sunshine', icon: 'fa-sun', description: 'Maintained positive mood' },
            { id: 'help_seeker', name: 'Brave Soul', icon: 'fa-shield-alt', description: 'Sought help when needed' },
            { id: 'month_user', name: 'Committed', icon: 'fa-calendar', description: '30 days with Sahara' }
        ];
        
        container.innerHTML = allAchievements.map(achievement => {
            const isUnlocked = achievements.includes(achievement.id);
            return `
                <div class="achievement-badge ${isUnlocked ? '' : 'locked'} interactive-hover">
                    <div class="text-2xl mb-2">
                        <i class="fas ${achievement.icon} ${isUnlocked ? 'text-yellow-800' : 'text-gray-400'}"></i>
                    </div>
                    <h4 class="font-semibold text-sm ${isUnlocked ? 'text-yellow-800' : 'text-gray-400'}">${achievement.name}</h4>
                    <p class="text-xs mt-1 ${isUnlocked ? 'text-yellow-700' : 'text-gray-400'}">${achievement.description}</p>
                    ${isUnlocked ? '<div class="text-xs text-yellow-600 mt-2">✓ Unlocked</div>' : '<div class="text-xs text-gray-400 mt-2">🔒 Locked</div>'}
                </div>
            `;
        }).join('');
    }

    // Notification System
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-20 right-4 z-50 max-w-sm p-4 rounded-lg shadow-lg transition-all duration-300 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button onclick="this.remove()" class="ml-4 text-white hover:text-gray-200">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    // Voice Input (Progressive Enhancement)
    setupVoiceInput() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            return; // Speech recognition not supported
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'hi-IN'; // Hindi support
        
        const micButton = document.querySelector('.fa-microphone')?.parentElement;
        if (micButton) {
            micButton.addEventListener('click', () => {
                recognition.start();
                micButton.innerHTML = '<i class="fas fa-microphone-slash text-red-500"></i>';
            });
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('message-input').value = transcript;
                micButton.innerHTML = '<i class="fas fa-microphone"></i>';
            };
            
            recognition.onerror = () => {
                micButton.innerHTML = '<i class="fas fa-microphone"></i>';
                this.showNotification('Voice recognition failed', 'error');
            };
        }
    }

    // PWA Service Worker
    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js')
                .then(registration => console.log('SW registered:', registration))
                .catch(error => console.log('SW registration failed:', error));
        }
    }

    // Analytics & Tracking
    trackInteraction(event, data = {}) {
        // Send to analytics endpoint
        fetch('/analytics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                event,
                data,
                timestamp: Date.now(),
                session_id: this.sessionId,
                user_agent: navigator.userAgent
            })
        }).catch(() => {}); // Fail silently
    }

    // Utility functions
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    saveToStorage() {
        localStorage.setItem('sahara_session', JSON.stringify({
            sessionId: this.sessionId,
            messages: this.messages.slice(-50), // Keep last 50 messages
            lastActivity: Date.now()
        }));
    }

    loadFromStorage() {
        const stored = localStorage.getItem('sahara_session');
        if (stored) {
            const data = JSON.parse(stored);
            // Restore session if less than 24 hours old
            if (Date.now() - data.lastActivity < 24 * 60 * 60 * 1000) {
                this.sessionId = data.sessionId;
                this.messages = data.messages || [];
                // Restore chat messages
                this.messages.forEach(msg => this.addMessage(msg.text, msg.sender));
            }
        }
    }

    initializeAnimations() {
        // Initialize AOS (Animate On Scroll) if not already done
        if (typeof AOS !== 'undefined') {
            AOS.refresh();
        }
    }
}

// Quick message functions (global scope for onclick handlers)
function sendQuickMessage(message) {
    document.getElementById('message-input').value = message;
    app.sendMessage();
}

function recordMood(mood) {
    app.recordMood(mood);
}

function sendMessage() {
    app.sendMessage();
}

// Initialize the modern app
const app = new SaharaAppModern();

// Global functions for HTML onclick handlers
window.sendMessage = () => app.sendMessage();
window.recordMood = (mood) => app.recordMood(mood);
window.sendQuickMessage = (message) => sendQuickMessage(message);