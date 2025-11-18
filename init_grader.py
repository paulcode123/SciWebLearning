#!/usr/bin/env python3
"""
Initialize Grade Scanner tables
Run this script once to add the grade_submissions table to your existing database.
"""

from app import app, db

def init_grader_tables():
    """Create grade scanner tables"""
    with app.app_context():
        # Import models to ensure they're registered
        from models import GradeSubmission

        print("Creating grade scanner tables...")
        db.create_all()
        print("[OK] Grade scanner tables created successfully!")
        print("\nYou can now use the grade scanner at /grader")

if __name__ == '__main__':
    init_grader_tables()
