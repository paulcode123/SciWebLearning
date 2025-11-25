from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Gamification fields
    xp = db.Column(db.Integer, default=0, nullable=False)
    level = db.Column(db.Integer, default=1, nullable=False)
    streak_days = db.Column(db.Integer, default=0, nullable=False)
    last_activity_date = db.Column(db.Date, nullable=True)
    achievements = db.Column(db.JSON, default=list, nullable=True)  # List of achievement IDs

    projects = db.relationship('Project', backref='owner', lazy=True)
    
    def add_xp(self, amount):
        """Add XP and check for level up"""
        self.xp += amount
        new_level = self.calculate_level()
        if new_level > self.level:
            self.level = new_level
            return True  # Leveled up!
        return False
    
    def calculate_level(self):
        """Calculate level based on XP (exponential growth)"""
        # Level formula: level = floor(sqrt(xp / 100)) + 1
        import math
        return int(math.sqrt(self.xp / 100)) + 1
    
    def update_streak(self):
        """Update daily streak"""
        today = date.today()
        if self.last_activity_date:
            days_diff = (today - self.last_activity_date).days
            if days_diff == 1:
                self.streak_days += 1
            elif days_diff > 1:
                self.streak_days = 1
        else:
            self.streak_days = 1
        self.last_activity_date = today


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_date = db.Column(db.Date, default=date.today, nullable=False)

    conversations = db.relationship('Conversation', backref='project', lazy=True, cascade='all, delete-orphan')


class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ai_model = db.Column(db.String(120), nullable=True)
    interaction_style = db.Column(db.String(120), nullable=True)
    learning_pace = db.Column(db.String(50), nullable=True)
    difficulty_level = db.Column(db.String(50), nullable=True)
    explanation_style = db.Column(db.String(50), nullable=True)
    interaction_preference = db.Column(db.String(50), nullable=True)

    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')
    graph_nodes = db.relationship('KnowledgeNode', backref='conversation', lazy=True, cascade='all, delete-orphan')
    graph_edges = db.relationship('KnowledgeEdge', backref='conversation', lazy=True, cascade='all, delete-orphan')


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class KnowledgeNode(db.Model):
    __tablename__ = 'knowledge_nodes'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(100), nullable=True)  # concept, theorem, person, event, etc.
    extra = db.Column(db.JSON, nullable=True)


class KnowledgeEdge(db.Model):
    __tablename__ = 'knowledge_edges'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    source_node_id = db.Column(db.Integer, db.ForeignKey('knowledge_nodes.id'), nullable=False)
    target_node_id = db.Column(db.Integer, db.ForeignKey('knowledge_nodes.id'), nullable=False)
    relation = db.Column(db.String(120), nullable=False)  # derives, causes, references, etc.
    extra = db.Column(db.JSON, nullable=True)


class GradeSubmission(db.Model):
    __tablename__ = 'grade_submissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(120), nullable=True)
    image_filename = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(512), nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)  # pending, graded, error
    overall_score = db.Column(db.Float, nullable=True)  # 0-100
    total_points = db.Column(db.Float, nullable=True)
    earned_points = db.Column(db.Float, nullable=True)
    ai_feedback = db.Column(db.Text, nullable=True)
    grading_rubric = db.Column(db.JSON, nullable=True)
    annotations = db.Column(db.JSON, nullable=True)  # Store marked-up positions
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    graded_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='grade_submissions', lazy=True)
    project = db.relationship('Project', backref='grade_submissions', lazy=True)


class LearningModule(db.Model):
    """Duolingo-style learning modules organized by topic"""
    __tablename__ = 'learning_modules'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    subject = db.Column(db.String(120), nullable=False)  # e.g., "Physics", "Calculus", "Python"
    difficulty = db.Column(db.String(50), default='Beginner', nullable=False)
    icon = db.Column(db.String(50), default='book', nullable=False)  # FontAwesome icon name
    color = db.Column(db.String(20), default='#6366f1', nullable=False)  # Module color
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    order_index = db.Column(db.Integer, default=0, nullable=False)  # For ordering modules
    
    lessons = db.relationship('DailyLesson', backref='module', lazy=True, cascade='all, delete-orphan', order_by='DailyLesson.order_index')
    user = db.relationship('User', backref='learning_modules', lazy=True)


class DailyLesson(db.Model):
    """Individual lessons within a module (like Duolingo's daily lessons)"""
    __tablename__ = 'daily_lessons'

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)  # Lesson content/instructions
    lesson_type = db.Column(db.String(50), default='interactive', nullable=False)  # interactive, quiz, practice, review
    order_index = db.Column(db.Integer, default=0, nullable=False)
    xp_reward = db.Column(db.Integer, default=20, nullable=False)  # XP gained on completion
    estimated_minutes = db.Column(db.Integer, default=10, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_unlocked = db.Column(db.Boolean, default=False, nullable=False)
    
    progress = db.relationship('LessonProgress', backref='lesson', lazy=True, uselist=False)


class LessonProgress(db.Model):
    """Track user progress on individual lessons"""
    __tablename__ = 'lesson_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('daily_lessons.id'), nullable=False, unique=True)
    completion_percentage = db.Column(db.Float, default=0.0, nullable=False)  # 0-100
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    best_score = db.Column(db.Float, nullable=True)  # Best score achieved (0-100)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    user = db.relationship('User', backref='lesson_progress', lazy=True)

