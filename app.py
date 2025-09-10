from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# Mock data structure for learning projects and conversations
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

# AI Models configuration
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
def dashboard():
    """Main learning dashboard showing all projects"""
    return render_template('dashboard.html', projects=mock_projects)

@app.route('/outline')
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
def project_dashboard(project_id):
    """Project dashboard showing conversations and new conversation button"""
    project = next((p for p in mock_projects if p["id"] == project_id), None)
    if not project:
        return redirect(url_for('dashboard'))
    return render_template('project_dashboard.html', project=project)

@app.route('/project/<int:project_id>/new-conversation')
def new_conversation(project_id):
    """Prompting page where users configure their conversation"""
    project = next((p for p in mock_projects if p["id"] == project_id), None)
    if not project:
        return redirect(url_for('dashboard'))
    
    return render_template('new_conversation.html', 
                         project=project,
                         conversation_styles=conversation_styles,
                         ai_models=ai_models,
                         learning_preferences=learning_preferences)

@app.route('/project/<int:project_id>/conversation/<int:conversation_id>')
def chat_interface(project_id, conversation_id):
    """Chat interface for having conversations"""
    project = next((p for p in mock_projects if p["id"] == project_id), None)
    if not project:
        return redirect(url_for('dashboard'))
    
    conversation = None
    for conv in project["conversations"]:
        if conv["id"] == conversation_id:
            conversation = conv
            break
    
    if not conversation:
        return redirect(url_for('project_dashboard', project_id=project_id))
    
    return render_template('chat_interface.html', 
                         project=project, 
                         conversation=conversation,
                         outline_mode=False)

@app.route('/api/send-message', methods=['POST'])
def send_message():
    """API endpoint to handle chat messages (placeholder)"""
    data = request.json
    message = data.get('message', '')
    outline_mode = data.get('outline_mode', False)
    
    # Placeholder response - in real implementation, this would call AI APIs
    if outline_mode:
        response = (
            "Great—let's shape your learning project. "
            "Briefly describe what you want to learn, any specific resources you'd like to include, "
            "whether you prefer surveying existing knowledge or starting from scratch, and if you want deep mastery or a broad overview.\n\n"
            f"You said: '{message}'."
        )
    else:
        response = (
            f"This is a placeholder response to: '{message}'. In the real implementation, this would be processed by the selected AI model with the configured prompt context."
        )
    
    return jsonify({
        'response': response,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/create-project-from-outline', methods=['POST'])
def create_project_from_outline():
    """Create an in-memory project after the outline is complete (no persistence)."""
    data = request.json or {}
    topic = (data.get('topic') or '').strip()
    description = (data.get('description') or '').strip()

    # Auto-generate a title if not provided
    if not topic:
        topic = 'New Learning Project'
    title = topic

    # Compute next IDs
    next_project_id = (max((p["id"] for p in mock_projects), default=0) + 1) if mock_projects else 1
    next_conversation_id = (max((c["id"] for p in mock_projects for c in p.get("conversations", [])), default=0) + 1)

    new_project = {
        "id": next_project_id,
        "title": title,
        "description": description or f"Learning project about {topic}",
        "created_date": datetime.now().strftime('%Y-%m-%d'),
        "conversations": [
            {"id": next_conversation_id, "title": "Outline Summary", "date": datetime.now().strftime('%Y-%m-%d'), "message_count": 0}
        ]
    }

    mock_projects.append(new_project)

    return jsonify({
        'project_id': new_project["id"],
        'redirect_url': url_for('project_dashboard', project_id=new_project["id"]) 
    })

@app.route('/style')
def style():
    return render_template('style_options.html')

if __name__ == '__main__':
    app.run(debug=True)
