// Sahara Mental Wellness - Main JavaScript Application
class SaharaApp {
    constructor() {
        this.currentMood = null;
        this.chatHistory = [];
        this.sessionId = null;
        this.moodHistory = this.loadMoodHistory();
        this.achievements = this.loadAchievements();
        this.stats = this.loadStats();
        this.userJourney = this.initializeUserJourney();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadResources();
        this.updateStats();
        this.updateMoodCalendar();
        this.checkAchievements();
    }

    loadMoodHistory() {
        return JSON.parse(localStorage.getItem('sahara_mood_history') || '[]');
    }

    getRecentMoodContext() {
        // Get recent mood context for AI chat enhancement - anonymous users
        const moodHistory = this.loadMoodHistory();
        
        if (moodHistory.length === 0) {
            return null;
        }

        // Get last 5 mood entries
        const recentEntries = moodHistory.slice(-5);
        const latest = recentEntries[0];
        
        // Calculate dominant emotions
        const emotionCounts = {};
        recentEntries.forEach(entry => {
            const emotion = entry.emotion || 'neutral';
            emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
        });
        
        const dominantEmotions = Object.keys(emotionCounts)
            .sort((a, b) => emotionCounts[b] - emotionCounts[a])
            .slice(0, 3);
        
        // Determine wellness trend
        let wellnessTrend = 'stable';
        if (recentEntries.length >= 2) {
            const firstRating = recentEntries[0].rating || 5;
            const lastRating = recentEntries[recentEntries.length - 1].rating || 5;
            
            if (firstRating > lastRating) {
                wellnessTrend = 'improving';
            } else if (firstRating < lastRating) {
                wellnessTrend = 'declining';
            }
        }
        
        return {
            recent_rating: latest.rating || 5,
            recent_emotion: latest.emotion || 'neutral', 
            dominant_emotions: dominantEmotions,
            wellness_trend: wellnessTrend
        };
    }

    initializeUserJourney() {
        // Initialize user journey tracking
        const journey = {
            entry_point: this.detectEntryPoint(),
            session_start: new Date().toISOString(),
            pages_visited: [],
            chat_initiated_from: null,
            mood_context_available: this.moodHistory.length > 0,
            user_state: 'exploring'
        };
        
        // Track page visits
        this.trackPageVisit(window.location.pathname);
        
        return journey;
    }

    detectEntryPoint() {
        // Detect how user accessed the chat system
        const referrer = document.referrer;
        const currentPath = window.location.pathname;
        const urlParams = new URLSearchParams(window.location.search);
        
        // Check if came from mood analytics dashboard
        if (referrer.includes('/mood-analytics') || urlParams.has('from_analytics')) {
            return 'mood_analytics_referral';
        }
        
        // Check if came from mood check-in
        if (referrer.includes('/mood-checkin') || urlParams.has('from_checkin')) {
            return 'mood_checkin_referral';
        }
        
        // Check if direct access to chat
        if (currentPath === '/' || currentPath.includes('chat')) {
            return 'direct_chat_access';
        }
        
        // Check if from external source
        if (referrer && !referrer.includes(window.location.hostname)) {
            return 'external_referral';
        }
        
        return 'organic_discovery';
    }

    trackPageVisit(path) {
        // Track user navigation for context
        if (!this.userJourney.pages_visited.includes(path)) {
            this.userJourney.pages_visited.push(path);
        }
        
        // Update user state based on page
        if (path.includes('mood-analytics')) {
            this.userJourney.user_state = 'analyzing_mood_data';
        } else if (path.includes('mood-checkin')) {
            this.userJourney.user_state = 'tracking_mood';
        } else if (path === '/' || path.includes('chat')) {
            this.userJourney.user_state = 'seeking_support';
        }
    }

    getChatContext() {
        // Get contextual information for chat enhancement
        return {
            entry_point: this.userJourney.entry_point,
            user_state: this.userJourney.user_state,
            has_tracked_mood: this.userJourney.mood_context_available,
            session_duration: this.getSessionDuration(),
            pages_visited: this.userJourney.pages_visited
        };
    }

    getSessionDuration() {
        // Calculate how long user has been in session
        const start = new Date(this.userJourney.session_start);
        const now = new Date();
        return Math.round((now - start) / 1000 / 60); // minutes
    }

    setupEventListeners() {
        // Mood quick select buttons
        document.querySelectorAll('.mood-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectQuickMood(e.target.dataset.mood);
            });
        });

        // Mood selector buttons
        document.querySelectorAll('.mood-select').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectMood(e.target.dataset.mood);
            });
        });

        // Smooth scrolling for navigation
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    selectQuickMood(mood) {
        this.currentMood = mood;
        document.querySelectorAll('.mood-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
        
        // Auto scroll to chat
        setTimeout(() => {
            document.getElementById('chat-section').scrollIntoView({ behavior: 'smooth' });
        }, 500);
    }

    selectMood(mood) {
        this.currentMood = mood;
        document.querySelectorAll('.mood-select').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
    }

    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message) return;

        // Add user message to chat
        this.addMessageToChat(message, 'user');
        messageInput.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Get or create session ID
            if (!this.sessionId) {
                this.sessionId = localStorage.getItem('sahara_session_id') || null;
            }

            // Get recent mood context for AI enhancement
            const moodData = this.getRecentMoodContext();

            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    context: {
                        session_id: this.sessionId,
                        mood: this.currentMood,
                        history: this.chatHistory.slice(-5), // Last 5 messages for context
                        timestamp: new Date().toISOString(),
                        user_journey: this.getChatContext() // Include user journey context
                    },
                    mood_data: moodData // Include mood context for AI enhancement
                })
            });

            const data = await response.json();
            
            // Store session ID
            if (data.session_id) {
                this.sessionId = data.session_id;
                localStorage.setItem('sahara_session_id', this.sessionId);
            }
            
            // Remove typing indicator
            this.removeTypingIndicator();
            
            // Add bot response with better formatting
            this.addMessageToChat(data.message, 'bot', data.urgent);
            
            // Update stats
            this.stats.chatCount++;
            this.updateStats();
            this.saveStats();
            
            // Check for achievements
            this.checkAchievements();
            
        } catch (error) {
            this.removeTypingIndicator();
            this.addMessageToChat('माफ करें, कुछ तकनीकी समस्या है। कृपया पुनः प्रयास करें। Please try again.', 'bot');
            console.error('Chat error:', error);
        }
    }

    addMessageToChat(message, sender, isUrgent = false) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        
        const messageClass = sender === 'user' ? 'user-message' : 'bot-message';
        const urgentClass = isUrgent ? 'crisis-message' : '';
        
        messageDiv.className = `message ${messageClass} ${urgentClass}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                ${sender === 'bot' ? '<strong>Sahara:</strong> ' : ''}${message}
            </div>
            <small class="text-muted">${new Date().toLocaleTimeString()}</small>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Store in history
        this.chatHistory.push({ message, sender, timestamp: new Date() });
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing-indicator-message';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
                <strong style="margin-left: 10px;">Sahara is typing...</strong>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    removeTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator-message');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async trackMood() {
        if (!this.currentMood) {
            alert('कृपया पहले अपना mood select करें।');
            return;
        }

        const notes = document.getElementById('mood-notes').value;
        const today = new Date().toISOString().split('T')[0];
        
        try {
            const response = await fetch('/mood', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mood: this.currentMood,
                    date: today,
                    notes: notes
                })
            });

            const data = await response.json();
            
            // Save mood locally
            this.moodHistory[today] = {
                mood: this.currentMood,
                notes: notes,
                timestamp: new Date()
            };
            
            this.saveMoodHistory();
            this.updateMoodCalendar();
            this.updateMoodInsights();
            
            // Update stats
            this.stats.moodCount++;
            this.updateStats();
            this.saveStats();
            
            // Clear form
            document.getElementById('mood-notes').value = '';
            document.querySelectorAll('.mood-select').forEach(btn => btn.classList.remove('active'));
            this.currentMood = null;
            
            // Show success message
            this.showNotification('Mood tracked successfully! 🌟', 'success');
            
            // Check achievements
            this.checkAchievements();
            
        } catch (error) {
            this.showNotification('कुछ तकनीकी समस्या है। कृपया पुनः प्रयास करें।', 'error');
        }
    }

    async loadResources() {
        try {
            const response = await fetch('/resources');
            const resources = await response.json();
            this.displayResources(resources);
        } catch (error) {
            console.error('Error loading resources:', error);
        }
    }

    displayResources(resources) {
        const container = document.getElementById('resources-container');
        container.innerHTML = '';

        Object.entries(resources).forEach(([key, resource]) => {
            const resourceCard = document.createElement('div');
            resourceCard.className = 'col-md-6 col-lg-4 mb-4';
            
            let itemsHtml = '';
            if (resource.items) {
                resource.items.forEach(item => {
                    if (item.name) {
                        itemsHtml += `<li><strong>${item.name}:</strong> ${item.description || item.contact || ''}</li>`;
                    } else if (item.tip) {
                        itemsHtml += `<li>${item.tip}</li>`;
                    } else if (item.steps) {
                        itemsHtml += `<li><strong>${item.name}:</strong><ul>`;
                        item.steps.forEach(step => {
                            itemsHtml += `<li>${step}</li>`;
                        });
                        itemsHtml += `</ul></li>`;
                    }
                });
            }

            resourceCard.innerHTML = `
                <div class="card resource-card h-100">
                    <div class="card-header">
                        <h5 class="card-title mb-0">${resource.title}</h5>
                    </div>
                    <div class="card-body">
                        <p class="card-text text-muted">${resource.description}</p>
                        <ul class="list-unstyled">
                            ${itemsHtml}
                        </ul>
                        <button class="btn btn-outline-primary btn-sm" onclick="saharaApp.readResource('${key}')">
                            <i class="fas fa-book-open me-1"></i>Read More
                        </button>
                    </div>
                </div>
            `;
            
            container.appendChild(resourceCard);
        });
    }

    readResource(resourceKey) {
        this.stats.resourceCount++;
        this.updateStats();
        this.saveStats();
        this.showNotification('Resource accessed! Keep learning 📚', 'info');
        this.checkAchievements();
    }

    updateMoodCalendar() {
        const weekMood = document.getElementById('week-mood');
        weekMood.innerHTML = '';
        
        const today = new Date();
        const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(today.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            
            const dayDiv = document.createElement('div');
            dayDiv.className = 'text-center';
            
            const moodData = this.moodHistory[dateStr];
            let moodEmoji = '';
            let moodClass = '';
            
            if (moodData) {
                switch (moodData.mood) {
                    case 'very-happy': moodEmoji = '😄'; moodClass = 'happy'; break;
                    case 'happy': moodEmoji = '😊'; moodClass = 'happy'; break;
                    case 'okay': moodEmoji = '😐'; moodClass = 'okay'; break;
                    case 'sad': moodEmoji = '��'; moodClass = 'sad'; break;
                    case 'anxious': moodEmoji = '😰'; moodClass = 'anxious'; break;
                }
            }
            
            dayDiv.innerHTML = `
                <div class="mood-day ${moodClass}" title="${moodData ? moodData.notes : 'No mood recorded'}">
                    ${moodEmoji || '?'}
                </div>
                <small>${weekDays[date.getDay()]}</small>
            `;
            
            weekMood.appendChild(dayDiv);
        }
    }

    updateMoodInsights() {
        const insights = document.getElementById('mood-insights');
        const moodCounts = {};
        const recent = Object.entries(this.moodHistory).slice(-7);
        
        recent.forEach(([date, data]) => {
            moodCounts[data.mood] = (moodCounts[data.mood] || 0) + 1;
        });
        
        let insightText = '';
        const dominantMood = Object.keys(moodCounts).reduce((a, b) => 
            moodCounts[a] > moodCounts[b] ? a : b
        );
        
        switch (dominantMood) {
            case 'happy':
            case 'very-happy':
                insightText = '🌟 आप इस सप्ताह अच्छा महसूस कर रहे हैं! Keep up the positive energy!';
                break;
            case 'sad':
                insightText = '💙 यह समय कठिन लग सकता है, लेकिन आप अकेले नहीं हैं। Consider talking to someone.';
                break;
            case 'anxious':
                insightText = '🧘‍♀️ Anxiety के signs दिख रहे हैं। Try some breathing exercises or meditation.';
                break;
            default:
                insightText = '📊 Continue tracking to see patterns in your mood.';
        }
        
        insights.innerHTML = `<p class="text-info">${insightText}</p>`;
    }

    checkAchievements() {
        const newAchievements = [];
        
        // First chat achievement
        if (this.stats.chatCount >= 1 && !this.achievements.includes('first_chat')) {
            newAchievements.push('first_chat');
        }
        
        // Mood tracker achievement
        if (this.stats.moodCount >= 1 && !this.achievements.includes('mood_tracker')) {
            newAchievements.push('mood_tracker');
        }
        
        // Resource reader achievement
        if (this.stats.resourceCount >= 1 && !this.achievements.includes('resource_reader')) {
            newAchievements.push('resource_reader');
        }
        
        // Week streak achievement
        if (this.stats.moodCount >= 7 && !this.achievements.includes('week_streak')) {
            newAchievements.push('week_streak');
        }
        
        // Award new achievements
        newAchievements.forEach(achievement => {
            this.awardAchievement(achievement);
        });
    }

    async awardAchievement(achievementType) {
        try {
            const response = await fetch('/achievements', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ type: achievementType })
            });
            
            const data = await response.json();
            
            this.achievements.push(achievementType);
            this.stats.points += data.points;
            
            this.saveAchievements();
            this.updateStats();
            this.updateAchievementsDisplay();
            
            this.showNotification(`🏆 Achievement Unlocked: ${data.achievement}`, 'success');
            
        } catch (error) {
            console.error('Error awarding achievement:', error);
        }
    }

    updateAchievementsDisplay() {
        const achievementsList = document.getElementById('achievements-list');
        achievementsList.innerHTML = '';
        
        const achievementTitles = {
            'first_chat': '🌱 First Conversation',
            'mood_tracker': '📊 Mood Tracking Started',
            'resource_reader': '📚 Knowledge Seeker',
            'week_streak': '🔥 7-Day Streak'
        };
        
        if (this.achievements.length === 0) {
            achievementsList.innerHTML = '<p class="text-muted">Start your wellness journey to unlock achievements!</p>';
        } else {
            this.achievements.forEach(achievement => {
                const badge = document.createElement('div');
                badge.className = 'achievement-badge';
                badge.textContent = achievementTitles[achievement] || 'Achievement';
                achievementsList.appendChild(badge);
            });
        }
    }

    updateStats() {
        document.getElementById('chat-count').textContent = this.stats.chatCount;
        document.getElementById('mood-count').textContent = this.stats.moodCount;
        document.getElementById('resource-count').textContent = this.stats.resourceCount;
        document.getElementById('points-count').textContent = this.stats.points;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} notification`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            animation: slideInRight 0.3s ease;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    // Local Storage Methods
    loadMoodHistory() {
        return JSON.parse(localStorage.getItem('sahara_mood_history') || '{}');
    }

    saveMoodHistory() {
        localStorage.setItem('sahara_mood_history', JSON.stringify(this.moodHistory));
    }

    loadAchievements() {
        return JSON.parse(localStorage.getItem('sahara_achievements') || '[]');
    }

    saveAchievements() {
        localStorage.setItem('sahara_achievements', JSON.stringify(this.achievements));
    }

    loadStats() {
        return JSON.parse(localStorage.getItem('sahara_stats') || 
            '{"chatCount": 0, "moodCount": 0, "resourceCount": 0, "points": 0}');
    }

    saveStats() {
        localStorage.setItem('sahara_stats', JSON.stringify(this.stats));
    }
}

// Global Functions
function startChat() {
    document.getElementById('chat-section').scrollIntoView({ behavior: 'smooth' });
    document.getElementById('message-input').focus();
}

function sendMessage() {
    saharaApp.sendMessage();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function trackMood() {
    saharaApp.trackMood();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.saharaApp = new SaharaApp();
});

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
