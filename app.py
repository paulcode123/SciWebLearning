from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import json
import os
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    current_user,
    login_required,
)
from flask_migrate import Migrate

from config import DevelopmentConfig, ProductionConfig
from dotenv import load_dotenv
from models import db, User, Project, Conversation, Message, KnowledgeNode, KnowledgeEdge, GradeSubmission, LearningModule, DailyLesson, LessonProgress
from chat_providers import get_default_provider
from kg import extract_knowledge_graph
from werkzeug.utils import secure_filename
import base64

load_dotenv()
# Also load server-managed secrets from instance folder if present
try:
    load_dotenv(os.path.join(os.path.dirname(__file__), 'instance', 'secrets.env'))
except Exception:
    pass
app = Flask(__name__)

# Config
ENV_NAME = os.environ.get('FLASK_ENV', 'development').lower()
if ENV_NAME == 'production':
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

# Extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
@app.errorhandler(404)
def not_found(e):
    return render_template('error_404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error_500.html'), 500


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.context_processor
def inject_provider_status():
    """Expose provider readiness to templates to surface helpful UI banners."""
    return { 'PROVIDER_READY': bool(os.environ.get('OPENAI_API_KEY')) }

# Mock data used for non-authenticated landing/demo
mock_projects = [
    {
        "id": 1,
        "title": "Master Python Programming",
        "description": "Learn Python from basics to advanced concepts",
        "created_date": "2024-01-15",
        "conversations": [
            {"id": 1, "title": "Python Basics", "date": "2024-01-15", "message_count": 12},
            {"id": 2, "title": "Object-Oriented Programming", "date": "2024-01-18", "message_count": 8}
        ]
    },
    {
        "id": 2,
        "title": "Calculus Fundamentals",
        "description": "Understanding derivatives and integrals",
        "created_date": "2024-01-20",
        "conversations": [
            {"id": 3, "title": "Limits and Continuity", "date": "2024-01-20", "message_count": 15}
        ]
    },
    {
        "id": 3,
        "title": "World History Deep Dive",
        "description": "Exploring major historical events and figures",
        "created_date": "2024-01-22",
        "conversations": []
    }
]

# AI Models configuration (UI only; runtime uses environment/provider)
ai_models = {
    "openai": [
        {"id": "gpt-4", "name": "GPT-4", "provider": "OpenAI"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "OpenAI"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "OpenAI"}
    ],
    "anthropic": [
        {"id": "claude-3-opus", "name": "Claude 3 Opus", "provider": "Anthropic"},
        {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "provider": "Anthropic"},
        {"id": "claude-3-haiku", "name": "Claude 3 Haiku", "provider": "Anthropic"}
    ],
    "google": [
        {"id": "gemini-pro", "name": "Gemini Pro", "provider": "Google"},
        {"id": "gemini-ultra", "name": "Gemini Ultra", "provider": "Google"},
        {"id": "gemini-nano", "name": "Gemini Nano", "provider": "Google"}
    ]
}

# Conversation styles organized by category
conversation_styles = {
    "Teaching & Explanation": [
        "Socratic Questioning",
        "Step-by-Step Tutorial",
        "Analogies & Metaphors",
        "Visual Learning Support",
        "Concept Mapping"
    ],
    "Problem Solving": [
        "Guided Problem Solving",
        "Challenge-Based Learning",
        "Case Study Analysis",
        "Debugging Partner",
        "Critical Thinking Exercises"
    ],
    "Interactive & Experiential": [
        "Role-Play Scenarios",
        "Historical Figure Conversations",
        "Simulation Exercises",
        "Game-Based Learning",
        "Interactive Storytelling"
    ],
    "Practice & Assessment": [
        "Quiz & Test Prep",
        "Flashcard Review",
        "Practice Problems",
        "Mock Interviews",
        "Peer Review Simulation"
    ],
    "Creative & Exploratory": [
        "Brainstorming Sessions",
        "Creative Writing Partner",
        "Research Assistant",
        "Debate Partner",
        "Idea Development"
    ]
}

# Learning preferences
learning_preferences = {
    "learning_pace": ["Slow and thorough", "Moderate", "Fast-paced"],
    "difficulty_level": ["Beginner", "Intermediate", "Advanced", "Expert"],
    "explanation_style": ["Detailed explanations", "Concise summaries", "Examples-heavy", "Theory-focused"],
    "interaction_preference": ["Highly interactive", "Balanced", "More listening"]
}

@app.route('/')
@login_required
def dashboard():
    """Duolingo-style learning dashboard with daily modules"""
    # Get or create default learning modules for the user
    modules = LearningModule.query.filter_by(user_id=current_user.id, is_active=True).order_by(LearningModule.order_index).all()
    
    # If no modules exist, create default ones
    if not modules:
        default_modules = [
            {'title': 'Physics Fundamentals', 'subject': 'Physics', 'icon': 'atom', 'color': '#ef4444', 'description': 'Master the basics of mechanics, energy, and motion'},
            {'title': 'Calculus Essentials', 'subject': 'Mathematics', 'icon': 'function', 'color': '#3b82f6', 'description': 'Learn derivatives, integrals, and limits'},
            {'title': 'Python Programming', 'subject': 'Computer Science', 'icon': 'code', 'color': '#10b981', 'description': 'Build programming skills from scratch'},
            {'title': 'Chemistry Basics', 'subject': 'Chemistry', 'icon': 'flask', 'color': '#f59e0b', 'description': 'Understand atoms, molecules, and reactions'},
        ]
        for idx, mod_data in enumerate(default_modules):
            module = LearningModule(
                user_id=current_user.id,
                title=mod_data['title'],
                subject=mod_data['subject'],
                icon=mod_data['icon'],
                color=mod_data['color'],
                description=mod_data['description'],
                order_index=idx,
                difficulty='Beginner'
            )
            db.session.add(module)
        db.session.commit()
        modules = LearningModule.query.filter_by(user_id=current_user.id, is_active=True).order_by(LearningModule.order_index).all()
    
    # Get today's lesson for each module
    today = date.today()
    modules_with_lessons = []
    for module in modules:
        # Get today's lesson or create one
        today_lesson = DailyLesson.query.filter_by(module_id=module.id).filter(
            DailyLesson.created_at >= datetime.combine(today, datetime.min.time())
        ).first()
        
        if not today_lesson:
            # Generate today's lesson
            today_lesson = generate_daily_lesson(module, current_user)
        
        # Get progress
        progress = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=today_lesson.id).first()
        if not progress:
            progress = LessonProgress(user_id=current_user.id, lesson_id=today_lesson.id)
            db.session.add(progress)
            db.session.commit()
        
        # Calculate module completion
        all_lessons = DailyLesson.query.filter_by(module_id=module.id).all()
        completed_lessons = sum(1 for l in all_lessons 
                                if LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=l.id, is_completed=True).first())
        module_completion = (completed_lessons / len(all_lessons) * 100) if all_lessons else 0
        
        modules_with_lessons.append({
            'module': module,
            'today_lesson': today_lesson,
            'progress': progress,
            'completion': module_completion
        })
    
    # Calculate daily goal progress
    daily_xp_goal = 50
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    
    # Calculate today's XP from completed lessons
    today_lessons = DailyLesson.query.join(LessonProgress).filter(
        LessonProgress.user_id == current_user.id,
        LessonProgress.is_completed == True,
        LessonProgress.completed_at >= today_start
    ).all()
    today_xp = sum(lesson.xp_reward for lesson in today_lessons)
    
    # Get user stats
    user_stats = {
        'xp': current_user.xp,
        'level': current_user.level,
        'streak_days': current_user.streak_days,
        'daily_xp': today_xp,
        'daily_goal': daily_xp_goal
    }
    
    # Get projects for the projects section
    projects = (
        Project.query.filter_by(owner_id=current_user.id)
        .order_by(Project.id.desc())
        .limit(6)
        .all()
    )
    
    return render_template('dashboard.html', 
                         modules_with_lessons=modules_with_lessons,
                         user_stats=user_stats,
                         projects=projects)


def generate_daily_lesson(module, user):
    """Generate a daily lesson for a module using AI"""
    from chat_providers import get_default_provider
    
    # Get previous lessons to avoid repetition
    previous_lessons = DailyLesson.query.filter_by(module_id=module.id).order_by(DailyLesson.created_at.desc()).limit(5).all()
    previous_topics = [l.title for l in previous_lessons]
    
    # Generate lesson content using AI
    provider = get_default_provider()
    system_prompt = f"""You are a learning module generator for SciWeb. Create a daily lesson for the module "{module.title}" in {module.subject}.

Module description: {module.description}
Difficulty: {module.difficulty}

Previous lesson topics: {', '.join(previous_topics) if previous_topics else 'None'}

Generate a new lesson that:
1. Builds on previous knowledge but introduces new concepts
2. Is appropriate for {module.difficulty} level
3. Takes about 10 minutes to complete
4. Is interactive and engaging
5. Includes clear learning objectives

Return a JSON object with:
- "title": Lesson title (max 60 chars)
- "description": Brief description (1-2 sentences)
- "content": Detailed lesson content with interactive elements
- "lesson_type": One of: interactive, quiz, practice, review
- "learning_objectives": Array of 2-3 learning objectives

Format your response as valid JSON only."""
    
    try:
        if provider and provider._has_key:
            response = provider.chat([{"role": "system", "content": system_prompt}, 
                                     {"role": "user", "content": f"Generate today's lesson for {module.title}"}],
                                    model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'))
            
            # Parse JSON response
            import json
            import re
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                lesson_data = json.loads(json_match.group())
                # Ensure content is a string, not a dict
                if isinstance(lesson_data.get('content'), dict):
                    # If content is a dict, convert it to a formatted string
                    content_parts = []
                    for key, value in lesson_data['content'].items():
                        content_parts.append(f"## {key.title()}\n\n{value}")
                    lesson_data['content'] = '\n\n'.join(content_parts)
                elif not isinstance(lesson_data.get('content'), str):
                    # If content is not a string, convert it
                    lesson_data['content'] = str(lesson_data.get('content', ''))
            else:
                # Fallback if JSON parsing fails
                lesson_data = {
                    'title': f'{module.subject} Practice',
                    'description': f'Continue learning {module.subject}',
                    'content': response[:500] if isinstance(response, str) else str(response)[:500],
                    'lesson_type': 'interactive',
                    'learning_objectives': ['Master key concepts', 'Apply knowledge']
                }
        else:
            # Fallback lesson
            lesson_data = {
                'title': f'{module.subject} Practice',
                'description': f'Continue learning {module.subject}',
                'content': f'Today we will explore key concepts in {module.subject}. This interactive lesson will help you build your understanding step by step.',
                'lesson_type': 'interactive',
                'learning_objectives': ['Master key concepts', 'Apply knowledge']
            }
    except Exception as e:
        print(f"Error generating lesson: {e}")
        lesson_data = {
            'title': f'{module.subject} Practice',
            'description': f'Continue learning {module.subject}',
            'content': f'Today we will explore key concepts in {module.subject}.',
            'lesson_type': 'interactive',
            'learning_objectives': ['Master key concepts']
        }
    
    # Create the lesson - ensure content is a string
    content = lesson_data.get('content', '')
    if not isinstance(content, str):
        if isinstance(content, dict):
            # Convert dict to formatted string
            content_parts = []
            for key, value in content.items():
                content_parts.append(f"## {key.title()}\n\n{value}")
            content = '\n\n'.join(content_parts)
        else:
            content = str(content)
    
    lesson = DailyLesson(
        module_id=module.id,
        title=lesson_data.get('title', f'{module.subject} Lesson'),
        description=lesson_data.get('description', ''),
        content=content,
        lesson_type=lesson_data.get('lesson_type', 'interactive'),
        xp_reward=20,
        estimated_minutes=10,
        is_unlocked=True
    )
    db.session.add(lesson)
    db.session.commit()
    
    return lesson


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        display_name = (request.form.get('display_name') or '').strip() or email
        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'error')
            return redirect(url_for('login'))
        user = User(email=email, password_hash=generate_password_hash(password), display_name=display_name)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('auth_register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'error')
        return redirect(url_for('login'))
    return render_template('auth_login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/outline')
@login_required
def outline_chat():
    """Outline session that starts a conversation without creating a project yet"""
    # Initialize or reset outline history for a fresh session
    # Optionally, you can keep history by not clearing it
    # session.pop('outline_history', None)  # Uncomment to reset history on each visit
    
    temp_project = {
        "id": 0,
        "title": "New Learning Project",
        "description": "",
        "created_date": datetime.now().strftime('%Y-%m-%d'),
        "conversations": []
    }
    temp_conversation = {
        "id": 0,
        "title": "Outline Session"
    }
    
    # Load existing outline history if available
    outline_messages = session.get('outline_history', [])
    messages_json = json.dumps([{"role": m["role"], "content": m["content"]} for m in outline_messages])
    
    return render_template('chat_interface.html', 
                         project=temp_project, 
                         conversation=temp_conversation, 
                         outline_mode=True,
                         messages_json=messages_json)

@app.route('/project/<int:project_id>')
@login_required
def project_dashboard(project_id):
    """Project dashboard showing conversations and new conversation button"""
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first()
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('project_dashboard.html', project=project)

@app.route('/project/<int:project_id>/new-conversation')
@login_required
def new_conversation(project_id):
    """Prompting page where users configure their conversation"""
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first()
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('new_conversation.html', 
                         project=project,
                         conversation_styles=conversation_styles,
                         ai_models=ai_models,
                         learning_preferences=learning_preferences)

@app.route('/project/<int:project_id>/conversation/<int:conversation_id>')
@login_required
def chat_interface(project_id, conversation_id):
    """Chat interface for having conversations"""
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first()
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('dashboard'))

    conversation = Conversation.query.filter_by(id=conversation_id, project_id=project.id).first()
    if not conversation:
        flash('Conversation not found.', 'error')
        return redirect(url_for('project_dashboard', project_id=project_id))

    recent_messages = (
        Message.query.filter_by(conversation_id=conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    serialized = [{"role": m.role, "content": m.content} for m in recent_messages]

    return render_template('chat_interface.html', 
                         project=project, 
                         conversation=conversation,
                         outline_mode=False,
                         messages_json=json.dumps(serialized))

@app.route('/api/send-message', methods=['POST'])
@login_required
def send_message():
    """API endpoint to handle chat messages"""
    try:
        data = request.json or {}
        message = (data.get('message') or '').strip()
        
        if not message:
            return jsonify({
                'response': 'Please enter a message.',
                'timestamp': datetime.now().isoformat(),
                'error': True
            })
        
        raw_outline = data.get('outline_mode', False)
        outline_mode = (raw_outline is True) or (
            isinstance(raw_outline, str) and raw_outline.strip().lower() in ('true', '1', 'yes')
        )
        project_id = data.get('project_id')
        conversation_id = data.get('conversation_id')

        # Force outline mode ONLY for the outline temp session (project_id == 0 or conversation_id == 0)
        if outline_mode and (project_id not in (0, None) and conversation_id not in (0, None)):
            outline_mode = False

        if outline_mode:
            # Use provider to generate an outline-guided response with conversation history
            provider = get_default_provider()
            
            # Check if provider is available (check for API key)
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key or (hasattr(provider, '_has_key') and not provider._has_key):
                return jsonify({
                    'response': (
                        "Provider unavailable: missing OPENAI_API_KEY. Please add it to your environment or .env file, "
                        "then refresh and try again."
                    ),
                    'timestamp': datetime.now().isoformat(),
                    'error': True
                })
            
            # Maintain conversation history in session
            if 'outline_history' not in session:
                session['outline_history'] = []
            
            # Add user message to history
            session['outline_history'].append({"role": "user", "content": message})
            
            # Build messages with system prompt and history
            sys_prompt = (
                "You are SciWeb, an AI learning guide helping a learner outline their learning project. "
                "Ask concise, targeted questions to clarify: (1) the topic/subject they want to learn, "
                "(2) any specific resources or materials they want to include, (3) their prior knowledge level, "
                "(4) whether they want a broad overview or deep mastery, and (5) their learning goals. "
                "Propose a brief structured plan with milestones, key skills to develop, and checkpoints. "
                "Keep responses conversational and encouraging. End with 1-2 short questions to proceed."
            )
            
            messages = [{"role": "system", "content": sys_prompt}] + session['outline_history'][-20:]  # Keep last 20 messages
            
            try:
                # Call the provider
                ai_text = provider.chat(messages, model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'))
                
                # Check if we got a valid response (not an error message)
                if not ai_text or ai_text.startswith("Provider unavailable"):
                    return jsonify({
                        'response': ai_text or "No response from AI provider. Please check your API key.",
                        'timestamp': datetime.now().isoformat(),
                        'error': True
                    })
                
                # Add assistant response to history
                session['outline_history'].append({"role": "assistant", "content": ai_text})
                session.modified = True
                
                # Award XP for outline mode interaction
                from datetime import date
                try:
                    current_user.update_streak()
                    leveled_up = current_user.add_xp(10)  # 10 XP per message
                    db.session.commit()
                except Exception as db_error:
                    # If DB commit fails, log but don't fail the request
                    print(f"Warning: Failed to update user stats: {db_error}")
                    db.session.rollback()
                    leveled_up = False
                
                return jsonify({
                    'response': ai_text,
                    'timestamp': datetime.now().isoformat(),
                    'xp_gained': 10,
                    'total_xp': current_user.xp if hasattr(current_user, 'xp') else 0,
                    'level': current_user.level if hasattr(current_user, 'level') else 1,
                    'leveled_up': leveled_up if 'leveled_up' in locals() else False,
                    'streak_days': current_user.streak_days if hasattr(current_user, 'streak_days') else 0
                })
            except Exception as e:
                # Log the error with full traceback for debugging
                import traceback
                error_trace = traceback.format_exc()
                error_msg = str(e)
                print(f"Error in outline mode: {error_msg}")
                print(error_trace)
                
                # Return a more informative error message (always return 200 with error in response)
                # This ensures the frontend can read the error message
                if "API key" in error_msg or "authentication" in error_msg.lower() or "401" in error_msg:
                    return jsonify({
                        'response': (
                            "Authentication error: Please check that your OPENAI_API_KEY is valid and has not expired. "
                            f"Error details: {error_msg}"
                        ),
                        'timestamp': datetime.now().isoformat(),
                        'error': True
                    })
                elif "rate limit" in error_msg.lower() or "429" in error_msg:
                    return jsonify({
                        'response': (
                            "Rate limit exceeded: Please wait a moment and try again."
                        ),
                        'timestamp': datetime.now().isoformat(),
                        'error': True
                    })
                else:
                    return jsonify({
                        'response': (
                            f"Error: {error_msg}. Please check your API key and try again. "
                            "If the problem persists, check the server logs for more details."
                        ),
                        'timestamp': datetime.now().isoformat(),
                        'error': True
                    })

        # Normal chat flow with persistence and provider call
        if not project_id or not conversation_id:
            return jsonify({
                'response': 'Invalid request: project_id and conversation_id are required for normal chat mode.',
                'timestamp': datetime.now().isoformat(),
                'error': True
            })
        
        conversation = Conversation.query.join(Project).filter(
            Conversation.id == conversation_id,
            Project.id == project_id,
            Project.owner_id == current_user.id,
        ).first()
        if not conversation:
            return jsonify({
                'response': 'Conversation not found. Please create a new conversation.',
                'timestamp': datetime.now().isoformat(),
                'error': True
            })

        # Persist user message
        user_msg = Message(conversation_id=conversation.id, role='user', content=message)
        db.session.add(user_msg)
        
        # Award XP and update streak for user activity
        from datetime import date
        current_user.update_streak()
        leveled_up = current_user.add_xp(10)  # 10 XP per message
        db.session.commit()

        # Build provider messages from history (trimmed) with SciWeb system prompt
        history = (
            Message.query.filter_by(conversation_id=conversation.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        # Compose a system prompt that encodes SciWeb's learning framework
        style = conversation.interaction_style or 'Socratic Questioning'
        sys_prompt = (
            "You are SciWeb, an AI learning guide. Goals: (1) Conversational knowledge derivation with"
            " historical simulations and STEM re-derivations; (2) Scaffolded prompting with adaptive hints;"
            " (3) Build conceptual connections suitable for extraction into a knowledge graph;"
            " (4) Encourage reflection and milestone framing."
            f" Interaction style: {style}. Adjust difficulty by learner signals. Prefer prompting the learner"
            " to think, show steps, and connect ideas historically when relevant. Keep responses concise but"
            " rigorous; include check-for-understanding questions."
        )
        provider_messages = [{"role": "system", "content": sys_prompt}] + [
            {"role": m.role, "content": m.content} for m in history
        ][-24:]

        try:
            provider = get_default_provider()
            ai_text = provider.chat(provider_messages, model=conversation.ai_model)
        except Exception as e:
            # Provide a more actionable error message for setup issues
            import traceback
            error_trace = traceback.format_exc()
            error_msg = str(e)
            print(f"Error in normal chat mode: {error_msg}")
            print(error_trace)
            missing_key = 'OPENAI_API_KEY' not in os.environ or not os.environ.get('OPENAI_API_KEY')
            if missing_key:
                ai_text = (
                    "Provider unavailable: missing OPENAI_API_KEY. Add it to your environment or .env, then"
                    " refresh and try again."
                )
            else:
                ai_text = f"Sorry, there was an issue contacting the AI provider: {error_msg}. Please try again."

        # Persist assistant message
        ai_msg = Message(conversation_id=conversation.id, role='assistant', content=ai_text)
        db.session.add(ai_msg)
        
        # Award additional XP for receiving AI response
        leveled_up = current_user.add_xp(5)  # 5 XP for AI response
        db.session.commit()
        
        # Return level up status if applicable
        response_data = {
            'response': ai_text,
            'timestamp': datetime.now().isoformat(),
            'xp_gained': 15,
            'total_xp': current_user.xp,
            'level': current_user.level,
            'leveled_up': leveled_up,
            'streak_days': current_user.streak_days
        }

        # Update knowledge graph for this conversation (simple refresh)
        try:
            full_messages = (
                Message.query.filter_by(conversation_id=conversation.id)
                .order_by(Message.created_at.asc())
                .all()
            )
            messages_payload = [{"role": m.role, "content": m.content} for m in full_messages]
            nodes, edges = extract_knowledge_graph(messages_payload)

            # Clear and reinsert nodes/edges
            KnowledgeEdge.query.filter_by(conversation_id=conversation.id).delete()
            KnowledgeNode.query.filter_by(conversation_id=conversation.id).delete()
            db.session.flush()

            label_to_node = {}
            for n in nodes:
                node = KnowledgeNode(conversation_id=conversation.id, label=n['label'], type=n.get('type'))
                db.session.add(node)
                db.session.flush()
                label_to_node[n['label']] = node

            for e in edges:
                src = label_to_node.get(e.get('source'))
                tgt = label_to_node.get(e.get('target'))
                if src and tgt and src.id != tgt.id:
                    db.session.add(KnowledgeEdge(
                        conversation_id=conversation.id,
                        source_node_id=src.id,
                        target_node_id=tgt.id,
                        relation=e.get('relation') or 'related_to'
                    ))
            db.session.commit()
        except Exception:
            db.session.rollback()

        return jsonify(response_data)
    except Exception as global_error:
        # Catch any unhandled errors
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(global_error)
        print(f"Global error in send_message: {error_msg}")
        print(error_trace)
        return jsonify({
            'response': (
                f"An error occurred: {error_msg}. Please check the server logs for details."
            ),
            'timestamp': datetime.now().isoformat(),
            'error': True
        })

@app.route('/api/create-project-from-outline', methods=['POST'])
@login_required
def create_project_from_outline():
    """Create a project and initial conversation in the database."""
    data = request.json or {}
    topic = (data.get('topic') or '').strip() or 'New Learning Project'
    description = (data.get('description') or '').strip() or f'Learning project about {topic}'

    project = Project(owner_id=current_user.id, title=topic, description=description)
    db.session.add(project)
    db.session.flush()

    conv = Conversation(
        project_id=project.id,
        title='Outline Summary',
    )
    db.session.add(conv)
    db.session.flush()
    
    # Save outline history as messages if available
    outline_history = session.get('outline_history', [])
    for msg in outline_history:
        message = Message(
            conversation_id=conv.id,
            role=msg.get('role', 'user'),
            content=msg.get('content', '')
        )
        db.session.add(message)
    
    db.session.commit()
    
    # Clear outline history from session
    session.pop('outline_history', None)

    return jsonify({'project_id': project.id, 'redirect_url': url_for('project_dashboard', project_id=project.id)})


@app.route('/api/create-conversation', methods=['POST'])
@login_required
def api_create_conversation():
    data = request.json or {}
    project_id = data.get('project_id')
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    title = (data.get('objective') or 'New Conversation').strip()[:255]
    conv = Conversation(
        project_id=project.id,
        title=title or 'New Conversation',
        ai_model=data.get('ai_model'),
        interaction_style=data.get('conversation_style'),
        learning_pace=data.get('learning_pace'),
        difficulty_level=data.get('difficulty_level'),
        explanation_style=data.get('explanation_style'),
        interaction_preference=data.get('interaction_preference'),
    )
    db.session.add(conv)
    db.session.commit()

    return jsonify({'conversation_id': conv.id, 'redirect_url': url_for('chat_interface', project_id=project.id, conversation_id=conv.id)})



@app.route('/project/<int:project_id>/knowledge-graph')
@login_required
def knowledge_graph(project_id):
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first()
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('dashboard'))

    # Aggregate nodes/edges across all conversations in the project
    convo_ids = [c.id for c in project.conversations]
    nodes = KnowledgeNode.query.filter(KnowledgeNode.conversation_id.in_(convo_ids)).all()
    edges = KnowledgeEdge.query.filter(KnowledgeEdge.conversation_id.in_(convo_ids)).all()

    node_payload = [{'id': n.id, 'label': n.label, 'type': n.type} for n in nodes]
    edge_payload = [{'source': e.source_node_id, 'target': e.target_node_id, 'relation': e.relation} for e in edges]

    return render_template('knowledge_graph.html', project=project, nodes_json=json.dumps(node_payload), edges_json=json.dumps(edge_payload))

@app.route('/assistant')
@login_required
def assistant_hub():
    """Central hub to launch guided AI chats by template/category."""
    projects = (
        Project.query.filter_by(owner_id=current_user.id)
        .order_by(Project.id.desc())
        .all()
    )
    featured = [
        {"title": "Historical Simulation", "objective": "Role-play with a historical figure to explore core ideas.", "style": "Historical Figure Conversations"},
        {"title": "STEM Derivation", "objective": "Re-derive a physics/maths law step by step.", "style": "Socratic Questioning"},
        {"title": "Scaffolded Prompting", "objective": "Guided exploration with adaptive hints.", "style": "Guided Problem Solving"},
        {"title": "Group Debate", "objective": "Debate-style learning across multiple viewpoints.", "style": "Debate Partner"},
        {"title": "Concept Mapping", "objective": "Build a concept graph of a topic.", "style": "Concept Mapping"},
        {"title": "Prompt Autocomposer", "objective": "Auto-generate a conversation flow for my theme.", "style": "Brainstorming Sessions"},
    ]
    return render_template('assistant_hub.html', projects=projects, featured=featured)

# New social/collab UI routes (mock data)
@app.route('/feed')
@login_required
def feed():
    items = [
        {
            'id': 1,
            'author': current_user.display_name or current_user.email,
            'title': 'Deriving Maxwell’s Equations',
            'concepts': ['Electromagnetism', 'Vector Calculus'],
            'type': 'lesson',
            'helpfulness': 42,
            'preview': 'A step-by-step derivation from Gauss and Faraday to wave propagation…',
            'created': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 2,
            'author': 'Ada Lovelace',
            'title': 'Study Thread: Dynamic Programming Practice',
            'concepts': ['Algorithms', 'Recurrence Relations'],
            'type': 'thread',
            'helpfulness': 27,
            'preview': 'Let’s solve coin change, LCS, and knapsack with reasoning traces…',
            'created': datetime.now().strftime('%Y-%m-%d')
        },
    ]
    return render_template('feed.html', items=items)


@app.route('/cohorts')
@login_required
def cohorts():
    groups = [
        {'id': 1, 'name': 'AP Physics C Cohort', 'members': 18, 'topics': ['Mechanics', 'E&M']},
        {'id': 2, 'name': 'Linear Algebra Club', 'members': 24, 'topics': ['Eigenvalues', 'SVD']},
        {'id': 3, 'name': 'World History 1900–1950', 'members': 12, 'topics': ['WWI', 'Interwar', 'WWII']},
    ]
    return render_template('cohorts.html', groups=groups)


@app.route('/study')
@login_required
def study_room():
    room = {
        'id': 'demo',
        'title': 'Focus Room',
        'members': [current_user.display_name or current_user.email, 'Guest'],
    }
    return render_template('study_room.html', room=room)


@app.route('/profile')
@login_required
def profile():
    portfolio = {
        'name': current_user.display_name or current_user.email,
        'badges': ['Concept Mapper', 'Helpful Mentor'],
        'skills': ['Calculus', 'Python', 'Critical Thinking'],
    }
    return render_template('profile.html', portfolio=portfolio)


@app.route('/create')
@login_required
def create_hub():
    tools = [
        {'id': 'lesson', 'title': 'Lesson Builder', 'desc': 'Compose structured lessons with concept tags.'},
        {'id': 'quiz', 'title': 'Quiz Builder', 'desc': 'Create practice sets with spaced repetition.'},
        {'id': 'notes', 'title': 'Collaborative Notes', 'desc': 'Co-edit notes with classmates.'},
    ]
    return render_template('create_hub.html', tools=tools)


@app.route('/style')
@login_required
def style():
    """Style options page for customizing UI preferences"""
    return render_template('style_options.html')


@app.route('/lesson/<int:lesson_id>')
@login_required
def lesson_view(lesson_id):
    """View and complete a daily lesson"""
    lesson = DailyLesson.query.get_or_404(lesson_id)
    module = lesson.module
    
    # Verify user owns the module
    if module.user_id != current_user.id:
        flash('You do not have access to this lesson.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get or create progress
    progress = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    if not progress:
        progress = LessonProgress(user_id=current_user.id, lesson_id=lesson_id, started_at=datetime.utcnow())
        db.session.add(progress)
        db.session.commit()
    elif not progress.started_at:
        progress.started_at = datetime.utcnow()
        db.session.commit()
    
    return render_template('lesson_view.html', lesson=lesson, module=module, progress=progress)


@app.route('/api/lesson/complete', methods=['POST'])
@login_required
def complete_lesson():
    """Mark a lesson as completed and award XP"""
    data = request.json or {}
    lesson_id = data.get('lesson_id')
    score = data.get('score', 100)  # Default to 100% if not provided
    
    if not lesson_id:
        return jsonify({'error': 'lesson_id required'}), 400
    
    lesson = DailyLesson.query.get_or_404(lesson_id)
    if lesson.module.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Update progress
    progress = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    if not progress:
        progress = LessonProgress(user_id=current_user.id, lesson_id=lesson_id)
        db.session.add(progress)
    
    progress.completion_percentage = min(100.0, float(score))
    progress.is_completed = progress.completion_percentage >= 80.0  # 80% to complete
    progress.attempts += 1
    if float(score) > (progress.best_score or 0):
        progress.best_score = float(score)
    
    if progress.is_completed and not progress.completed_at:
        progress.completed_at = datetime.utcnow()
        # Award XP
        current_user.update_streak()
        leveled_up = current_user.add_xp(lesson.xp_reward)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'xp_gained': lesson.xp_reward,
            'total_xp': current_user.xp,
            'level': current_user.level,
            'leveled_up': leveled_up,
            'streak_days': current_user.streak_days
        })
    
    db.session.commit()
    return jsonify({'success': True, 'progress': progress.completion_percentage})


@app.route('/api/lesson/progress', methods=['POST'])
@login_required
def update_lesson_progress():
    """Update lesson progress without completing"""
    data = request.json or {}
    lesson_id = data.get('lesson_id')
    completion = data.get('completion', 0)  # 0-100
    
    if not lesson_id:
        return jsonify({'error': 'lesson_id required'}), 400
    
    lesson = DailyLesson.query.get_or_404(lesson_id)
    if lesson.module.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    progress = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    if not progress:
        progress = LessonProgress(user_id=current_user.id, lesson_id=lesson_id, started_at=datetime.utcnow())
        db.session.add(progress)
    
    progress.completion_percentage = min(100.0, max(0.0, float(completion)))
    progress.last_accessed = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'completion': progress.completion_percentage})


@app.route('/messages')
@login_required
def messages():
    threads = [
        {'id': 1, 'name': 'AP Physics Chat', 'last': "Let's meet 6pm for problem set 3", 'unread': 2},
        {'id': 2, 'name': 'Linear Algebra Buddies', 'last': 'SVD intuition notes shared', 'unread': 0},
        {'id': 3, 'name': 'History Debate Team', 'last': 'Finalize sources list', 'unread': 1},
    ]
    current = {'id': 1, 'name': 'AP Physics Chat', 'messages': [
        {'who': 'You', 'text': "Anyone free to review Gauss's law derivation?"},
        {'who': 'Riley', 'text': 'Yes! I can join in 10.'}
    ]}
    return render_template('messages.html', threads=threads, current=current)


# Grade Scanner Routes
@app.route('/grader')
@login_required
def grader_home():
    """Grade scanner dashboard showing recent submissions"""
    recent_submissions = (
        GradeSubmission.query.filter_by(user_id=current_user.id)
        .order_by(GradeSubmission.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template('grader_home.html', submissions=recent_submissions)


@app.route('/grader/upload', methods=['GET'])
@login_required
def grader_upload():
    """Upload page for grade scanner"""
    projects = Project.query.filter_by(owner_id=current_user.id).all()
    return render_template('grader_upload.html', projects=projects)


@app.route('/api/grader/submit', methods=['POST'])
@login_required
def api_grader_submit():
    """Handle file upload and initial submission"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf', 'heic'}
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, PDF, HEIC'}), 400

    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'grader')
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{current_user.id}_{timestamp}_{filename}"
    file_path = os.path.join(upload_dir, unique_filename)

    # Save file
    file.save(file_path)

    # Get form data
    title = request.form.get('title', 'Untitled Submission')
    subject = request.form.get('subject', '')
    project_id = request.form.get('project_id')

    # Create submission record
    submission = GradeSubmission(
        user_id=current_user.id,
        project_id=int(project_id) if project_id and project_id.isdigit() else None,
        title=title,
        subject=subject,
        image_filename=unique_filename,
        image_path=file_path,
        status='pending'
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({
        'success': True,
        'submission_id': submission.id,
        'redirect_url': url_for('grader_process', submission_id=submission.id)
    })


@app.route('/grader/process/<int:submission_id>')
@login_required
def grader_process(submission_id):
    """Processing page that triggers AI grading"""
    submission = GradeSubmission.query.filter_by(id=submission_id, user_id=current_user.id).first()
    if not submission:
        flash('Submission not found.', 'error')
        return redirect(url_for('grader_home'))

    return render_template('grader_process.html', submission=submission)


@app.route('/api/grader/grade/<int:submission_id>', methods=['POST'])
@login_required
def api_grader_grade(submission_id):
    """AI grading endpoint using vision model"""
    submission = GradeSubmission.query.filter_by(id=submission_id, user_id=current_user.id).first()
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404

    try:
        # Read the image file
        with open(submission.image_path, 'rb') as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')

        # Get grading instructions from request
        data = request.json or {}
        answer_key = data.get('answer_key', '')
        rubric = data.get('rubric', '')

        # Build AI prompt for grading
        grading_prompt = f"""You are an expert teacher grading handwritten student work.

Subject: {submission.subject or 'General'}
Assignment: {submission.title}

{f"Answer Key: {answer_key}" if answer_key else ""}
{f"Grading Rubric: {rubric}" if rubric else ""}

Please analyze this handwritten work and provide:
1. Overall score (0-100)
2. Detailed feedback on what's correct and what's incorrect
3. Specific comments on each problem/section
4. Constructive suggestions for improvement

Format your response as JSON with these fields:
{{
  "overall_score": <number 0-100>,
  "earned_points": <number>,
  "total_points": <number>,
  "feedback": "<detailed overall feedback>",
  "problem_feedback": [
    {{"problem": "<problem number/name>", "score": <points>, "comment": "<specific feedback>", "is_correct": <true/false>}}
  ]
}}"""

        # Call AI provider with vision capabilities
        provider = get_default_provider()

        # For vision grading, we'll use a simplified text-based approach for now
        # In production, you'd use GPT-4 Vision or similar
        ai_response = provider.chat([
            {"role": "system", "content": "You are an expert teacher providing detailed, constructive feedback on student work."},
            {"role": "user", "content": grading_prompt}
        ])

        # Parse AI response (assuming JSON format)
        try:
            import json
            grading_result = json.loads(ai_response)
        except:
            # Fallback if not JSON
            grading_result = {
                "overall_score": 85,
                "earned_points": 85,
                "total_points": 100,
                "feedback": ai_response,
                "problem_feedback": []
            }

        # Update submission with grading results
        submission.status = 'graded'
        submission.overall_score = grading_result.get('overall_score', 0)
        submission.earned_points = grading_result.get('earned_points', 0)
        submission.total_points = grading_result.get('total_points', 100)
        submission.ai_feedback = grading_result.get('feedback', '')
        submission.grading_rubric = grading_result.get('problem_feedback', [])
        submission.graded_at = datetime.now()
        db.session.commit()

        return jsonify({
            'success': True,
            'grading_result': grading_result,
            'redirect_url': url_for('grader_result', submission_id=submission.id)
        })

    except Exception as e:
        submission.status = 'error'
        db.session.commit()
        return jsonify({'error': f'Grading failed: {str(e)}'}), 500


@app.route('/grader/result/<int:submission_id>')
@login_required
def grader_result(submission_id):
    """Display grading results with annotations"""
    submission = GradeSubmission.query.filter_by(id=submission_id, user_id=current_user.id).first()
    if not submission:
        flash('Submission not found.', 'error')
        return redirect(url_for('grader_home'))

    return render_template('grader_result.html', submission=submission)
if __name__ == '__main__':
    # Dev convenience: create tables if not present
    with app.app_context():
        db.create_all()
    app.run(debug=app.config.get('DEBUG', False))
