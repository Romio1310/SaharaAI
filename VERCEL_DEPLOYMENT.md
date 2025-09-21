# Sahara Wellness - Vercel Deployment Guide

## ✅ Current Status
Your Sahara wellness project is now **Vercel-ready** with the following configurations:

### Files Added/Modified:
- ✅ `vercel.json` - Vercel deployment configuration
- ✅ `api/index.py` - Serverless function entry point  
- ✅ `app.py` - Updated for serverless database handling
- ✅ `requirements.txt` - Optimized dependencies

## 🚀 Deployment Steps

### 1. Database Setup (IMPORTANT!)
**⚠️ SQLite won't work on Vercel.** Choose one option:

#### Option A: PostgreSQL (Recommended for Production)
1. Sign up for a free PostgreSQL database:
   - [Supabase](https://supabase.com/) (Free tier: 500MB)
   - [Aiven](https://aiven.io/) (Free tier: 1 month)  
   - [Railway](https://railway.app/) (Free tier with usage limits)
   - [Neon](https://neon.tech/) (Free tier: 10GB)

2. Get your database URL (format: `postgresql://user:password@host:port/dbname`)

#### Option B: In-Memory SQLite (Demo Only)
Your app will work but **data won't persist** between requests.

### 2. Environment Variables Setup
In your Vercel dashboard, add these environment variables:

```
GEMINI_API_KEY=AIzaSyCUF3OWkKrOjZN6ni-WqDIq-vP_vGHi56Q
USE_GEMINI_API=true
FALLBACK_TO_LOCAL=true
DATABASE_URL=your_postgresql_url_here  # If using PostgreSQL
SECRET_KEY=your-secret-key-here
```

### 3. Deploy to Vercel

#### Method 1: Vercel CLI (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from your project directory
cd /Users/codname_gd/sahara-wellness-genai
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? Your username
# - Link to existing project? No  
# - Project name: sahara-wellness
# - Directory: ./
# - Override settings? No
```

#### Method 2: GitHub + Vercel Dashboard
1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import your GitHub repository
4. Add environment variables
5. Deploy!

### 4. Post-Deployment Checklist
- [ ] Test the mood tracking functionality
- [ ] Verify AI chat responses work
- [ ] Check database persistence (if using PostgreSQL)
- [ ] Test user registration/login
- [ ] Verify static files (CSS/JS) load correctly

## 🔧 Current App Features Ready for Demo:
- ✅ AI Mental Wellness Chatbot (Gemini AI + Local fallback)
- ✅ Mood Tracking & Analytics  
- ✅ User Authentication
- ✅ Resource Library
- ✅ Crisis Support
- ✅ PWA Support (Service Worker)
- ✅ Mobile Responsive Design

## 📊 Expected Vercel URLs:
- **Main App**: `https://sahara-wellness.vercel.app`
- **API Routes**: `https://sahara-wellness.vercel.app/api/`
- **Static Assets**: Auto-served by Vercel CDN

## 🚨 Known Limitations on Vercel:
1. **Cold Starts**: First request may be slower (~1-2 seconds)
2. **Function Timeout**: 60 seconds max per request  
3. **File Storage**: No persistent file system
4. **Database**: Requires external database service

## 💡 Demo Tips:
1. **Test AI Chat**: Shows Gemini AI integration
2. **Mood Analytics**: Demonstrates data visualization
3. **Responsive Design**: Works great on mobile
4. **PWA Features**: Can be installed as an app

## 🔗 Useful Links:
- [Vercel Deployment Docs](https://vercel.com/docs/deployments/overview)
- [Flask on Vercel](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Environment Variables](https://vercel.com/docs/projects/environment-variables)

---

Your Sahara wellness app is ready to demonstrate AI mental health support for Indian youth! 🌟