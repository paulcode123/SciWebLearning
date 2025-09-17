# SciWeb 4.0 - Interactive AI Learning Platform

SciWeb is a personalized AI-powered learning platform that creates dynamic conversations with AI models to enhance your learning experience.

## Features

- **Learning Dashboard**: View all your learning projects in one place
- **Project Management**: Organize conversations by learning topics
- **AI Model Selection**: Choose from 10+ AI models (OpenAI, Anthropic, Google)
- **Conversation Styles**: 25+ interaction styles across 5 categories
- **Personalized Prompts**: Dynamic prompt construction with learning context
- **Interactive Chat**: Real-time conversations with AI assistants

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - Create a `.env` file (optional) or set environment variables:
     - `FLASK_ENV=development`
     - `SECRET_KEY=change-me`
     - `DATABASE_URL=sqlite:///sciweb.db` (or your Postgres URL)
     - `OPENAI_API_KEY=sk-...`

3. **Run Database Migrations**
   ```bash
   flask db init && flask db migrate -m "init" && flask db upgrade
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

3. **Open Your Browser**
   Navigate to `http://localhost:5000`

## Project Structure

```
SciWeb4.0/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── templates/
    ├── base.html         # Base template with styling
    ├── dashboard.html    # Learning projects dashboard
    ├── project_dashboard.html  # Individual project view
    ├── new_conversation.html   # Conversation configuration
    └── chat_interface.html     # Chat interface
```

## How It Works

### 1. Learning Dashboard
- View all your learning projects
- See conversation counts and creation dates
- Click to enter any project

### 2. Project Dashboard
- View conversation history for a specific project
- Start new conversations
- Track project progress

### 3. Conversation Configuration
- Set specific learning objectives
- Choose learning preferences (pace, difficulty, style)
- Select interaction style from 25+ options:
  - **Teaching & Explanation**: Socratic questioning, tutorials, analogies
  - **Problem Solving**: Guided problem solving, challenges, debugging
  - **Interactive & Experiential**: Role-play, historical conversations, simulations
  - **Practice & Assessment**: Quizzes, flashcards, mock interviews
  - **Creative & Exploratory**: Brainstorming, research assistance, debates
- Pick AI model from OpenAI, Anthropic, or Google

### 4. Chat Interface
- Real-time conversation with configured AI
- Quick action buttons for common requests
- Message history with smooth animations
- Responsive design for all devices

## Current Status

This is a **skeleton implementation** with:
- ✅ Complete UI/UX flow
- ✅ All pages and navigation
- ✅ Conversation style selection
- ✅ AI model options
- ✅ Mock data and placeholder responses
- ✅ DB models, auth, persistence
- ✅ OpenAI provider abstraction (env-based)
- ✅ Knowledge graph extraction and visualization
- 🔄 **Next Steps**: Group learning rooms, achievements, AR/VR hooks

## Conversation Styles Available

### Teaching & Explanation
- Socratic Questioning
- Step-by-Step Tutorial
- Analogies & Metaphors
- Visual Learning Support
- Concept Mapping

### Problem Solving
- Guided Problem Solving
- Challenge-Based Learning
- Case Study Analysis
- Debugging Partner
- Critical Thinking Exercises

### Interactive & Experiential
- Role-Play Scenarios
- Historical Figure Conversations
- Simulation Exercises
- Game-Based Learning
- Interactive Storytelling

### Practice & Assessment
- Quiz & Test Prep
- Flashcard Review
- Practice Problems
- Mock Interviews
- Peer Review Simulation

### Creative & Exploratory
- Brainstorming Sessions
- Creative Writing Partner
- Research Assistant
- Debate Partner
- Idea Development

## AI Models Supported

### OpenAI
- GPT-4
- GPT-3.5 Turbo
- GPT-4 Turbo

### Anthropic
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku

### Google
- Gemini Pro
- Gemini Ultra
- Gemini Nano

## Design Philosophy

- **No Navigation Bar**: Clean, focused experience with back arrows
- **Fun & Interactive**: Gradient backgrounds, smooth animations, engaging UI
- **Mobile-First**: Responsive design that works on all devices
- **Context-Aware**: AI conversations include full learning context and history

## Future Enhancements

- Real AI API integrations
- User authentication and profiles
- Database persistence
- Progress tracking and analytics
- Advanced conversation management
- Export conversation transcripts
- Learning path recommendations
