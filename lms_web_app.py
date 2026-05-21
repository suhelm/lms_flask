"""
FLASK WEB INTERFACE FOR LMS SYSTEM
REST API endpoints and HTML templates for web access
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime, timedelta
import json
import os
import sys

# Import LMS modules
from lms_system import (
    DatabaseManager, 
    AuthenticationManager, 
    TeacherManager, 
    StudentManager
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Initialize database
db = DatabaseManager("lms_web.db")

# Fix database lock issue
import sqlite3
sqlite3.connect("lms_web.db", timeout=10.0).close()
auth = AuthenticationManager(db)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    """Decorator to check if user is a teacher"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'teacher':
            return jsonify({"error": "Access denied"}), 403
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """Decorator to check if user is a student"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'student':
            return jsonify({"error": "Access denied"}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        if session['role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        data = request.form
        
        success, msg = auth.register_user(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role=data.get('role', 'student')
        )
        
        if success:
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=msg)
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, user_data = auth.login(username, password)
        
        if success:
            session['user_id'] = user_data['id']
            session['username'] = user_data['username']
            session['role'] = user_data['role']
            session['name'] = f"{user_data['first_name']} {user_data['last_name']}"
            
            if user_data['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('login'))

# ============================================================================
# TEACHER ROUTES
# ============================================================================

@app.route('/teacher/dashboard')
@login_required
@teacher_required
def teacher_dashboard():
    """Teacher dashboard"""
    teacher = TeacherManager(db, session['user_id'])
    courses = teacher.get_my_courses()
    
    return render_template('teacher/dashboard.html', 
                         name=session['name'],
                         courses=courses)

@app.route('/teacher/course/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_course():
    """Create new course"""
    if request.method == 'POST':
        teacher = TeacherManager(db, session['user_id'])
        
        success, msg = teacher.create_course(
            course_code=request.form.get('course_code'),
            course_name=request.form.get('course_name'),
            description=request.form.get('description'),
            semester=request.form.get('semester'),
            credits=int(request.form.get('credits', 3))
        )
        
        if success:
            return redirect(url_for('teacher_dashboard'))
        else:
            return render_template('teacher/create_course.html', error=msg)
    
    return render_template('teacher/create_course.html')

@app.route('/teacher/course/<int:course_id>')
@login_required
@teacher_required
def view_course(course_id):
    """View course details"""
    teacher = TeacherManager(db, session['user_id'])
    course = teacher.get_course_details(course_id)
    
    if not course:
        return "Course not found", 404
    
    modules = teacher.get_course_modules(course_id)
    enrollments = teacher.get_course_enrollments(course_id)
    announcements = teacher.get_course_announcements(course_id)
    
    return render_template('teacher/view_course.html',
                         course=course,
                         modules=modules,
                         enrollments=enrollments,
                         announcements=announcements)

@app.route('/teacher/module/<int:module_id>/lessons')
@login_required
@teacher_required
def view_module_lessons(module_id):
    """View module lessons"""
    teacher = TeacherManager(db, session['user_id'])
    lessons = teacher.get_module_lessons(module_id)
    
    return render_template('teacher/view_lessons.html', lessons=lessons)

@app.route('/teacher/lesson/<int:lesson_id>/assignments')
@login_required
@teacher_required
def view_lesson_assignments(lesson_id):
    """View assignments for a lesson"""
    teacher = TeacherManager(db, session['user_id'])
    # Get assignments - would need course_id for full context
    
    return render_template('teacher/view_assignments.html')

@app.route('/teacher/assignment/<int:assignment_id>/submissions')
@login_required
@teacher_required
def view_submissions(assignment_id):
    """View assignment submissions"""
    teacher = TeacherManager(db, session['user_id'])
    submissions = teacher.get_assignment_submissions(assignment_id)
    
    return render_template('teacher/view_submissions.html', 
                         submissions=submissions,
                         assignment_id=assignment_id)

@app.route('/teacher/submission/<int:submission_id>/grade', methods=['POST'])
@login_required
@teacher_required
def grade_submission(submission_id):
    """Grade a submission"""
    teacher = TeacherManager(db, session['user_id'])
    
    success, msg = teacher.grade_submission(
        submission_id=submission_id,
        points_earned=float(request.form.get('points_earned')),
        feedback=request.form.get('feedback')
    )
    
    return jsonify({"success": success, "message": msg})

# ============================================================================
# STUDENT ROUTES
# ============================================================================

@app.route('/student/dashboard')
@login_required
@student_required
def student_dashboard():
    """Student dashboard"""
    student = StudentManager(db, session['user_id'])
    courses = student.get_enrolled_courses()
    pending_assignments = student.get_pending_assignments()
    
    return render_template('student/dashboard.html',
                         name=session['name'],
                         courses=courses,
                         assignments=pending_assignments)

@app.route('/student/enroll')
@login_required
@student_required
def enroll_course():
    """Enroll in a new course"""
    if request.method == 'POST':
        student = StudentManager(db, session['user_id'])
        
        success, msg = student.enroll_course(
            course_id=int(request.form.get('course_id'))
        )
        
        if success:
            return redirect(url_for('student_dashboard'))
        else:
            return render_template('student/enroll.html', error=msg)
    
    return render_template('student/enroll.html')

@app.route('/student/course/<int:course_id>')
@login_required
@student_required
def view_student_course(course_id):
    """View course as student"""
    student = StudentManager(db, session['user_id'])
    courses = student.get_enrolled_courses()
    
    # Find the course
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        return "Course not found", 404
    
    return render_template('student/view_course.html', course=course)

@app.route('/student/assignments')
@login_required
@student_required
def student_assignments():
    """View pending assignments"""
    student = StudentManager(db, session['user_id'])
    assignments = student.get_pending_assignments()
    
    return render_template('student/assignments.html', assignments=assignments)

@app.route('/student/assignment/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
@student_required
def submit_assignment(assignment_id):
    """Submit an assignment"""
    if request.method == 'POST':
        student = StudentManager(db, session['user_id'])
        
        success, msg = student.submit_assignment(
            assignment_id=assignment_id,
            submission_text=request.form.get('submission_text')
        )
        
        if success:
            return redirect(url_for('student_assignments'))
        else:
            return render_template('student/submit_assignment.html', 
                                 error=msg,
                                 assignment_id=assignment_id)
    
    return render_template('student/submit_assignment.html', assignment_id=assignment_id)

@app.route('/student/grades')
@login_required
@student_required
def student_grades():
    """View student grades"""
    student = StudentManager(db, session['user_id'])
    grades = student.get_grades()
    
    # Calculate statistics
    total_points = sum([g['total_points'] for g in grades if g['points_earned']])
    earned_points = sum([g['points_earned'] for g in grades if g['points_earned']])
    overall_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
    
    return render_template('student/grades.html',
                         grades=grades,
                         overall_percentage=overall_percentage)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/api/teacher/courses')
@login_required
@teacher_required
def api_get_courses():
    """Get all courses for teacher (API)"""
    teacher = TeacherManager(db, session['user_id'])
    courses = teacher.get_my_courses()
    
    return jsonify(courses), 200

@app.route('/api/teacher/course/<int:course_id>/modules')
@login_required
@teacher_required
def api_get_modules(course_id):
    """Get modules for a course (API)"""
    teacher = TeacherManager(db, session['user_id'])
    modules = teacher.get_course_modules(course_id)
    
    return jsonify(modules), 200

@app.route('/api/student/pending-assignments')
@login_required
@student_required
def api_get_pending_assignments():
    """Get pending assignments for student (API)"""
    student = StudentManager(db, session['user_id'])
    assignments = student.get_pending_assignments()
    
    return jsonify(assignments), 200

@app.route('/api/student/grades')
@login_required
@student_required
def api_get_grades():
    """Get student grades (API)"""
    student = StudentManager(db, session['user_id'])
    grades = student.get_grades()
    
    return jsonify(grades), 200

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('500.html'), 500

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    print("Starting LMS Web Application...")
    print("Access at: http://localhost:5000")
    print("\nDefault test users:")
    print("  Teacher: prof_smith / password123")
    print("  Student: student1 / password123")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
