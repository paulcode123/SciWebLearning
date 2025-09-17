from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import json
import os
from datetime import datetime
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
from models import db, User, Project, Conversation, Message, KnowledgeNode, KnowledgeEdge
from chat_providers import get_default_provider
from kg import extract_knowledge_graph

load_dotenv()
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
    """Main learning dashboard showing all projects"""
    projects = (
        Project.query.filter_by(owner_id=current_user.id)
        .order_by(Project.id.desc())
        .all()
    )
    return render_template('dashboard.html', projects=projects)


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
    return render_template('chat_interface.html', project=temp_project, conversation=temp_conversation, outline_mode=True)

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
    data = request.json or {}
    message = (data.get('message') or '').strip()
    outline_mode = bool(data.get('outline_mode', False))
    project_id = data.get('project_id')
    conversation_id = data.get('conversation_id')

    if outline_mode:
        response = (
            "Great—let's shape your learning project. "
            "Briefly describe what you want to learn, any specific resources you'd like to include, "
            "whether you prefer surveying existing knowledge or starting from scratch, and if you want deep mastery or a broad overview.\n\n"
            f"You said: '{message}'."
        )
        return jsonify({'response': response, 'timestamp': datetime.now().isoformat()})

    # Normal chat flow with persistence and provider call
    conversation = Conversation.query.join(Project).filter(
        Conversation.id == conversation_id,
        Project.id == project_id,
        Project.owner_id == current_user.id,
    ).first()
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404

    # Persist user message
    user_msg = Message(conversation_id=conversation.id, role='user', content=message)
    db.session.add(user_msg)
    db.session.commit()

    # Build provider messages from history (trimmed)
    history = (
        Message.query.filter_by(conversation_id=conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    provider_messages = [{"role": m.role, "content": m.content} for m in history][-24:]

    try:
        provider = get_default_provider()
        ai_text = provider.chat(provider_messages, model=conversation.ai_model)
    except Exception as e:
        ai_text = "Sorry, there was an issue contacting the AI provider."

    # Persist assistant message
    ai_msg = Message(conversation_id=conversation.id, role='assistant', content=ai_text)
    db.session.add(ai_msg)
    db.session.commit()

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
            src = label_to_node.get(e['source'])
            tgt = label_to_node.get(e['target'])
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

    return jsonify({'response': ai_text, 'timestamp': datetime.now().isoformat()})

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
    db.session.commit()

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

@app.route('/style')
@login_required
def style():
    return render_template('style_options.html')


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

if __name__ == '__main__':
    # Dev convenience: create tables if not present
    with app.app_context():
        db.create_all()
    app.run(debug=app.config.get('DEBUG', False))
