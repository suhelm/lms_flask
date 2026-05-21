"""
CANVAS-LIKE LMS SYSTEM
Learning Management System with SQLite Database
Features: Authentication, Teacher Portal, Course Management, Assignments, Grades
"""

import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import os

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

class DatabaseManager:
    """Manages all database operations for the LMS"""
    
    def __init__(self, db_path: str = "lms_system.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn
    
    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table (Teachers and Students)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('teacher', 'student', 'admin')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                course_code TEXT UNIQUE NOT NULL,
                course_name TEXT NOT NULL,
                description TEXT,
                semester TEXT,
                credits INTEGER DEFAULT 3,
                max_students INTEGER DEFAULT 50,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Course enrollments (Student enrollment in courses)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'dropped', 'completed')),
                UNIQUE(student_id, course_id),
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            )
        ''')
        
        # Modules/Lessons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                module_name TEXT NOT NULL,
                description TEXT,
                order_index INTEGER,
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            )
        ''')
        
        # Lessons/Content within modules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER NOT NULL,
                lesson_name TEXT NOT NULL,
                content TEXT,
                lesson_type TEXT CHECK(lesson_type IN ('text', 'video', 'assignment', 'quiz')),
                order_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
            )
        ''')
        
        # Assignments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                assignment_name TEXT NOT NULL,
                description TEXT,
                instructions TEXT,
                total_points INTEGER DEFAULT 100,
                due_date DATETIME NOT NULL,
                allow_late_submission BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
            )
        ''')
        
        # Student submissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                submission_text TEXT,
                file_path TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'submitted' CHECK(status IN ('submitted', 'graded', 'late')),
                UNIQUE(assignment_id, student_id),
                FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Grades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL UNIQUE,
                points_earned FLOAT,
                feedback TEXT,
                graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                graded_by INTEGER NOT NULL,
                FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
                FOREIGN KEY (graded_by) REFERENCES users(id)
            )
        ''')
        
        # Announcements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                teacher_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✓ Database initialized: {self.db_path}")


# ============================================================================
# AUTHENTICATION MODULE
# ============================================================================

class AuthenticationManager:
    """Handles user authentication and password management"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, email: str, password: str, 
                     first_name: str, last_name: str, role: str) -> Tuple[bool, str]:
        """Register a new user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Validate role
            if role not in ['teacher', 'student', 'admin']:
                return False, "Invalid role. Must be 'teacher', 'student', or 'admin'"
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Insert user
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, first_name, last_name, role)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, first_name, last_name, role))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            return True, f"User registered successfully (ID: {user_id})"
        
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return False, "Username already exists"
            elif "email" in str(e):
                return False, "Email already registered"
            else:
                return False, str(e)
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """Authenticate user login"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                SELECT id, username, email, first_name, last_name, role, created_at
                FROM users
                WHERE username = ? AND password_hash = ?
            ''', (username, password_hash))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return True, dict(user)
            else:
                return False, None
        
        except Exception as e:
            return False, None


# ============================================================================
# TEACHER MODULE
# ============================================================================

class TeacherManager:
    """Manages teacher operations: courses, modules, assignments"""
    
    def __init__(self, db: DatabaseManager, teacher_id: int):
        self.db = db
        self.teacher_id = teacher_id
    
    # ===== COURSE MANAGEMENT =====
    
    def create_course(self, course_code: str, course_name: str, 
                     description: str, semester: str, credits: int = 3) -> Tuple[bool, str]:
        """Create a new course"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO courses (teacher_id, course_code, course_name, description, semester, credits)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.teacher_id, course_code, course_name, description, semester, credits))
            
            conn.commit()
            course_id = cursor.lastrowid
            conn.close()
            
            return True, f"Course created successfully (ID: {course_id})"
        
        except sqlite3.IntegrityError:
            return False, "Course code already exists"
        except Exception as e:
            return False, str(e)
    
    def get_my_courses(self) -> List[Dict]:
        """Get all courses taught by this teacher"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, course_code, course_name, description, semester, credits, created_at
            FROM courses
            WHERE teacher_id = ?
            ORDER BY created_at DESC
        ''', (self.teacher_id,))
        
        courses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return courses
    
    def get_course_details(self, course_id: int) -> Optional[Dict]:
        """Get detailed information about a course"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, course_code, course_name, description, semester, credits, created_at, updated_at
            FROM courses
            WHERE id = ? AND teacher_id = ?
        ''', (course_id, self.teacher_id))
        
        course = cursor.fetchone()
        conn.close()
        
        return dict(course) if course else None
    
    def update_course(self, course_id: int, course_name: str = None, 
                     description: str = None, semester: str = None) -> Tuple[bool, str]:
        """Update course information"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if course_name:
                updates.append("course_name = ?")
                params.append(course_name)
            if description:
                updates.append("description = ?")
                params.append(description)
            if semester:
                updates.append("semester = ?")
                params.append(semester)
            
            if not updates:
                return False, "No updates provided"
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.extend([course_id, self.teacher_id])
            
            query = f"UPDATE courses SET {', '.join(updates)} WHERE id = ? AND teacher_id = ?"
            cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            
            return True, "Course updated successfully"
        
        except Exception as e:
            return False, str(e)
    
    def delete_course(self, course_id: int) -> Tuple[bool, str]:
        """Delete a course and all associated data"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM courses WHERE id = ? AND teacher_id = ?', 
                         (course_id, self.teacher_id))
            
            conn.commit()
            conn.close()
            
            return True, "Course deleted successfully"
        
        except Exception as e:
            return False, str(e)
    
    # ===== MODULE MANAGEMENT =====
    
    def create_module(self, course_id: int, module_name: str, 
                     description: str, due_date: str = None) -> Tuple[bool, str]:
        """Create a module within a course"""
        try:
            # Verify course ownership
            if not self.get_course_details(course_id):
                return False, "Course not found or unauthorized"
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get next order index
            cursor.execute('SELECT MAX(order_index) FROM modules WHERE course_id = ?', 
                         (course_id,))
            max_order = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                INSERT INTO modules (course_id, module_name, description, order_index, due_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (course_id, module_name, description, max_order + 1, due_date))
            
            conn.commit()
            module_id = cursor.lastrowid
            conn.close()
            
            return True, f"Module created successfully (ID: {module_id})"
        
        except Exception as e:
            return False, str(e)
    
    def get_course_modules(self, course_id: int) -> List[Dict]:
        """Get all modules in a course"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, module_name, description, order_index, due_date, created_at
            FROM modules
            WHERE course_id = ?
            ORDER BY order_index ASC
        ''', (course_id,))
        
        modules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return modules
    
    def update_module(self, module_id: int, module_name: str = None, 
                     description: str = None, due_date: str = None) -> Tuple[bool, str]:
        """Update module information"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if module_name:
                updates.append("module_name = ?")
                params.append(module_name)
            if description:
                updates.append("description = ?")
                params.append(description)
            if due_date:
                updates.append("due_date = ?")
                params.append(due_date)
            
            if not updates:
                return False, "No updates provided"
            
            params.append(module_id)
            
            query = f"UPDATE modules SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            
            return True, "Module updated successfully"
        
        except Exception as e:
            return False, str(e)
    
    def delete_module(self, module_id: int) -> Tuple[bool, str]:
        """Delete a module"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM modules WHERE id = ?', (module_id,))
            
            conn.commit()
            conn.close()
            
            return True, "Module deleted successfully"
        
        except Exception as e:
            return False, str(e)
    
    # ===== LESSON MANAGEMENT =====
    
    def create_lesson(self, module_id: int, lesson_name: str, 
                     content: str, lesson_type: str) -> Tuple[bool, str]:
        """Create a lesson within a module"""
        try:
            if lesson_type not in ['text', 'video', 'assignment', 'quiz']:
                return False, "Invalid lesson type"
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get next order index
            cursor.execute('SELECT MAX(order_index) FROM lessons WHERE module_id = ?', 
                         (module_id,))
            max_order = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                INSERT INTO lessons (module_id, lesson_name, content, lesson_type, order_index)
                VALUES (?, ?, ?, ?, ?)
            ''', (module_id, lesson_name, content, lesson_type, max_order + 1))
            
            conn.commit()
            lesson_id = cursor.lastrowid
            conn.close()
            
            return True, f"Lesson created successfully (ID: {lesson_id})"
        
        except Exception as e:
            return False, str(e)
    
    def get_module_lessons(self, module_id: int) -> List[Dict]:
        """Get all lessons in a module"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, lesson_name, content, lesson_type, order_index, created_at
            FROM lessons
            WHERE module_id = ?
            ORDER BY order_index ASC
        ''', (module_id,))
        
        lessons = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return lessons
    
    def update_lesson(self, lesson_id: int, lesson_name: str = None, 
                     content: str = None) -> Tuple[bool, str]:
        """Update lesson content"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if lesson_name:
                updates.append("lesson_name = ?")
                params.append(lesson_name)
            if content:
                updates.append("content = ?")
                params.append(content)
            
            if not updates:
                return False, "No updates provided"
            
            params.append(lesson_id)
            
            query = f"UPDATE lessons SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            
            return True, "Lesson updated successfully"
        
        except Exception as e:
            return False, str(e)
    
    def delete_lesson(self, lesson_id: int) -> Tuple[bool, str]:
        """Delete a lesson"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM lessons WHERE id = ?', (lesson_id,))
            
            conn.commit()
            conn.close()
            
            return True, "Lesson deleted successfully"
        
        except Exception as e:
            return False, str(e)
    
    # ===== ASSIGNMENT MANAGEMENT =====
    
    def create_assignment(self, lesson_id: int, assignment_name: str, 
                         description: str, instructions: str, 
                         total_points: int, due_date: str) -> Tuple[bool, str]:
        """Create an assignment within a lesson"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO assignments 
                (lesson_id, assignment_name, description, instructions, total_points, due_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (lesson_id, assignment_name, description, instructions, total_points, due_date))
            
            conn.commit()
            assignment_id = cursor.lastrowid
            conn.close()
            
            return True, f"Assignment created successfully (ID: {assignment_id})"
        
        except Exception as e:
            return False, str(e)
    
    def get_lesson_assignments(self, lesson_id: int) -> List[Dict]:
        """Get all assignments in a lesson"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, assignment_name, description, instructions, total_points, due_date, created_at
            FROM assignments
            WHERE lesson_id = ?
        ''', (lesson_id,))
        
        assignments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return assignments
    
    def get_assignment_submissions(self, assignment_id: int) -> List[Dict]:
        """Get all submissions for an assignment"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                s.id, s.assignment_id, s.student_id, 
                u.username, u.first_name, u.last_name,
                s.submission_text, s.submitted_at, s.status,
                g.points_earned, g.feedback, g.graded_at
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            LEFT JOIN grades g ON s.id = g.submission_id
            WHERE s.assignment_id = ?
            ORDER BY s.submitted_at DESC
        ''', (assignment_id,))
        
        submissions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return submissions
    
    def grade_submission(self, submission_id: int, points_earned: float, 
                        feedback: str) -> Tuple[bool, str]:
        """Grade a student submission"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if grade already exists
            cursor.execute('SELECT id FROM grades WHERE submission_id = ?', (submission_id,))
            
            if cursor.fetchone():
                # Update existing grade
                cursor.execute('''
                    UPDATE grades
                    SET points_earned = ?, feedback = ?, graded_at = CURRENT_TIMESTAMP, graded_by = ?
                    WHERE submission_id = ?
                ''', (points_earned, feedback, self.teacher_id, submission_id))
            else:
                # Insert new grade
                cursor.execute('''
                    INSERT INTO grades (submission_id, points_earned, feedback, graded_by)
                    VALUES (?, ?, ?, ?)
                ''', (submission_id, points_earned, feedback, self.teacher_id))
            
            # Update submission status
            cursor.execute('UPDATE submissions SET status = ? WHERE id = ?', 
                         ('graded', submission_id))
            
            conn.commit()
            conn.close()
            
            return True, "Submission graded successfully"
        
        except Exception as e:
            return False, str(e)
    
    def update_assignment(self, assignment_id: int, assignment_name: str = None,
                         description: str = None, due_date: str = None,
                         total_points: int = None) -> Tuple[bool, str]:
        """Update assignment details"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if assignment_name:
                updates.append("assignment_name = ?")
                params.append(assignment_name)
            if description:
                updates.append("description = ?")
                params.append(description)
            if due_date:
                updates.append("due_date = ?")
                params.append(due_date)
            if total_points:
                updates.append("total_points = ?")
                params.append(total_points)
            
            if not updates:
                return False, "No updates provided"
            
            params.append(assignment_id)
            
            query = f"UPDATE assignments SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            
            return True, "Assignment updated successfully"
        
        except Exception as e:
            return False, str(e)
    
    def delete_assignment(self, assignment_id: int) -> Tuple[bool, str]:
        """Delete an assignment"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM assignments WHERE id = ?', (assignment_id,))
            
            conn.commit()
            conn.close()
            
            return True, "Assignment deleted successfully"
        
        except Exception as e:
            return False, str(e)
    
    # ===== ENROLLMENT MANAGEMENT =====
    
    def get_course_enrollments(self, course_id: int) -> List[Dict]:
        """Get all students enrolled in a course"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                e.id, e.student_id, e.enrollment_date, e.status,
                u.username, u.first_name, u.last_name, u.email
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            WHERE e.course_id = ? AND e.status = 'active'
            ORDER BY u.last_name, u.first_name
        ''', (course_id,))
        
        enrollments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return enrollments
    
    def enroll_student(self, course_id: int, identifier: str) -> Tuple[bool, str]:
        """Enroll a student in a course by username or email"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, first_name, last_name FROM users
                WHERE (username = ? OR email = ?) AND role = 'student'
            ''', (identifier, identifier))
            student = cursor.fetchone()

            if not student:
                conn.close()
                return False, f"No student found with username/email '{identifier}'"

            cursor.execute('''
                INSERT INTO enrollments (student_id, course_id, status)
                VALUES (?, ?, 'active')
            ''', (student['id'], course_id))

            conn.commit()
            conn.close()
            return True, f"Enrolled {student['first_name']} {student['last_name']}"

        except sqlite3.IntegrityError:
            return False, "Student is already enrolled in this course"
        except Exception as e:
            return False, str(e)

    # ===== ANNOUNCEMENTS =====

    def create_announcement(self, course_id: int, title: str, 
                           content: str) -> Tuple[bool, str]:
        """Create a course announcement"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO announcements (course_id, teacher_id, title, content)
                VALUES (?, ?, ?, ?)
            ''', (course_id, self.teacher_id, title, content))
            
            conn.commit()
            announcement_id = cursor.lastrowid
            conn.close()
            
            return True, f"Announcement created successfully (ID: {announcement_id})"
        
        except Exception as e:
            return False, str(e)
    
    def get_course_announcements(self, course_id: int) -> List[Dict]:
        """Get all announcements for a course"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                a.id, a.title, a.content, a.created_at,
                u.first_name, u.last_name
            FROM announcements a
            JOIN users u ON a.teacher_id = u.id
            WHERE a.course_id = ?
            ORDER BY a.created_at DESC
        ''', (course_id,))
        
        announcements = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return announcements


# ============================================================================
# STUDENT MODULE
# ============================================================================

class StudentManager:
    """Manages student operations"""
    
    def __init__(self, db: DatabaseManager, student_id: int):
        self.db = db
        self.student_id = student_id
    
    def get_enrolled_courses(self) -> List[Dict]:
        """Get all courses student is enrolled in"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                c.id, c.course_code, c.course_name, c.description, c.semester,
                u.first_name, u.last_name,
                e.enrollment_date, e.status
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            JOIN users u ON c.teacher_id = u.id
            WHERE e.student_id = ? AND e.status = 'active'
            ORDER BY c.course_name
        ''', (self.student_id,))
        
        courses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return courses
    
    def enroll_course(self, course_id: int) -> Tuple[bool, str]:
        """Enroll in a course"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if course exists and has capacity
            cursor.execute('''
                SELECT c.max_students, COUNT(e.id) as enrolled
                FROM courses c
                LEFT JOIN enrollments e ON c.id = e.course_id AND e.status = 'active'
                WHERE c.id = ?
                GROUP BY c.id
            ''', (course_id,))
            
            result = cursor.fetchone()
            if not result:
                return False, "Course not found"
            
            max_students, enrolled = result
            if enrolled >= max_students:
                return False, "Course is full"
            
            # Enroll student
            cursor.execute('''
                INSERT INTO enrollments (student_id, course_id, status)
                VALUES (?, ?, 'active')
            ''', (self.student_id, course_id))
            
            conn.commit()
            conn.close()
            
            return True, "Successfully enrolled in course"
        
        except sqlite3.IntegrityError:
            return False, "Already enrolled in this course"
        except Exception as e:
            return False, str(e)
    
    def get_pending_assignments(self) -> List[Dict]:
        """Get all pending assignments for enrolled courses"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                a.id, a.assignment_name, a.description, a.total_points, a.due_date,
                l.lesson_name, m.module_name, c.course_code, c.course_name,
                CASE WHEN s.id IS NOT NULL THEN 'submitted' ELSE 'pending' END as status
            FROM assignments a
            JOIN lessons l ON a.lesson_id = l.id
            JOIN modules m ON l.module_id = m.id
            JOIN courses c ON m.course_id = c.id
            JOIN enrollments e ON c.id = e.course_id
            LEFT JOIN submissions s ON a.id = s.assignment_id AND s.student_id = ?
            WHERE e.student_id = ? AND e.status = 'active'
                AND a.due_date > datetime('now')
            ORDER BY a.due_date ASC
        ''', (self.student_id, self.student_id))
        
        assignments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return assignments
    
    def submit_assignment(self, assignment_id: int, submission_text: str) -> Tuple[bool, str]:
        """Submit an assignment"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO submissions (assignment_id, student_id, submission_text, status)
                VALUES (?, ?, ?, 'submitted')
            ''', (assignment_id, self.student_id, submission_text))
            
            conn.commit()
            submission_id = cursor.lastrowid
            conn.close()
            
            return True, f"Assignment submitted successfully (ID: {submission_id})"
        
        except sqlite3.IntegrityError:
            return False, "Assignment already submitted"
        except Exception as e:
            return False, str(e)
    
    def get_grades(self) -> List[Dict]:
        """Get all grades for student"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                c.course_code, c.course_name,
                a.assignment_name, a.total_points,
                g.points_earned, g.feedback, g.graded_at
            FROM grades g
            JOIN submissions s ON g.submission_id = s.id
            JOIN assignments a ON s.assignment_id = a.id
            JOIN lessons l ON a.lesson_id = l.id
            JOIN modules m ON l.module_id = m.id
            JOIN courses c ON m.course_id = c.id
            WHERE s.student_id = ?
            ORDER BY c.course_name, a.assignment_name
        ''', (self.student_id,))
        
        grades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return grades


# ============================================================================
# DEMO / TESTING
# ============================================================================

def demo_lms_system():
    """Demonstrate LMS system functionality"""
    
    print("\n" + "="*70)
    print("CANVAS-LIKE LMS SYSTEM DEMO")
    print("="*70)
    
    # Initialize database
    db = DatabaseManager("lms_demo.db")
    auth = AuthenticationManager(db)
    
    # ===== USER REGISTRATION =====
    print("\n1. REGISTERING USERS")
    print("-" * 70)
    
    # Register teacher
    success, msg = auth.register_user(
        username="prof_smith",
        email="smith@university.edu",
        password="password123",
        first_name="John",
        last_name="Smith",
        role="teacher"
    )
    print(f"Teacher registration: {msg}")
    
    # Register students
    for i, (fname, lname) in enumerate([("Alice", "Johnson"), ("Bob", "Williams"), 
                                        ("Carol", "Davis"), ("David", "Brown")], 1):
        success, msg = auth.register_user(
            username=f"student{i}",
            email=f"student{i}@university.edu",
            password="password123",
            first_name=fname,
            last_name=lname,
            role="student"
        )
        print(f"Student registration ({fname}): {msg}")
    
    # ===== USER LOGIN =====
    print("\n2. USER LOGIN")
    print("-" * 70)
    
    success, teacher_data = auth.login("prof_smith", "password123")
    if success:
        print(f"✓ Teacher login successful: {teacher_data['first_name']} {teacher_data['last_name']}")
        teacher_id = teacher_data['id']
    
    success, student_data = auth.login("student1", "password123")
    if success:
        print(f"✓ Student login successful: {student_data['first_name']} {student_data['last_name']}")
        student_id = student_data['id']
    
    # ===== TEACHER: CREATE COURSE =====
    print("\n3. TEACHER: CREATE COURSE")
    print("-" * 70)
    
    teacher = TeacherManager(db, teacher_id)
    
    success, msg = teacher.create_course(
        course_code="CS101",
        course_name="Introduction to Computer Science",
        description="Fundamentals of programming and computer science",
        semester="Fall 2024",
        credits=3
    )
    print(f"{msg}")
    course_id = 1  # First course created
    
    # ===== TEACHER: CREATE MODULES =====
    print("\n4. TEACHER: CREATE MODULES")
    print("-" * 70)
    
    success, msg = teacher.create_module(
        course_id=course_id,
        module_name="Module 1: Programming Basics",
        description="Learn fundamental programming concepts",
        due_date="2024-09-15"
    )
    print(f"{msg}")
    module_id = 1
    
    # ===== TEACHER: CREATE LESSONS =====
    print("\n5. TEACHER: CREATE LESSONS")
    print("-" * 70)
    
    success, msg = teacher.create_lesson(
        module_id=module_id,
        lesson_name="Lesson 1: Variables and Data Types",
        content="Variables are containers for storing data values...",
        lesson_type="text"
    )
    print(f"{msg}")
    lesson_id = 1
    
    # ===== TEACHER: CREATE ASSIGNMENT =====
    print("\n6. TEACHER: CREATE ASSIGNMENT")
    print("-" * 70)
    
    success, msg = teacher.create_assignment(
        lesson_id=lesson_id,
        assignment_name="Assignment 1: Write a Simple Program",
        description="Write a program that calculates the sum of two numbers",
        instructions="Create a Python script that takes two numbers as input and displays their sum.",
        total_points=100,
        due_date="2024-09-20 23:59:00"
    )
    print(f"{msg}")
    assignment_id = 1
    
    # ===== TEACHER: VIEW COURSE DETAILS =====
    print("\n7. TEACHER: VIEW COURSE DETAILS")
    print("-" * 70)
    
    course = teacher.get_course_details(course_id)
    print(f"Course: {course['course_code']} - {course['course_name']}")
    print(f"Description: {course['description']}")
    print(f"Semester: {course['semester']}")
    
    # ===== TEACHER: VIEW MODULES =====
    print("\n8. TEACHER: VIEW MODULES")
    print("-" * 70)
    
    modules = teacher.get_course_modules(course_id)
    for module in modules:
        print(f"- {module['module_name']} (Due: {module['due_date']})")
    
    # ===== TEACHER: VIEW LESSONS =====
    print("\n9. TEACHER: VIEW LESSONS")
    print("-" * 70)
    
    lessons = teacher.get_module_lessons(module_id)
    for lesson in lessons:
        print(f"- {lesson['lesson_name']} ({lesson['lesson_type']})")
    
    # ===== STUDENT: ENROLL IN COURSE =====
    print("\n10. STUDENT: ENROLL IN COURSE")
    print("-" * 70)
    
    student = StudentManager(db, student_id)
    success, msg = student.enroll_course(course_id)
    print(f"{msg}")
    
    # ===== STUDENT: VIEW ENROLLED COURSES =====
    print("\n11. STUDENT: VIEW ENROLLED COURSES")
    print("-" * 70)
    
    courses = student.get_enrolled_courses()
    for course in courses:
        print(f"- {course['course_code']}: {course['course_name']}")
        print(f"  Taught by: {course['first_name']} {course['last_name']}")
    
    # ===== STUDENT: VIEW PENDING ASSIGNMENTS =====
    print("\n12. STUDENT: VIEW PENDING ASSIGNMENTS")
    print("-" * 70)
    
    assignments = student.get_pending_assignments()
    for assign in assignments:
        print(f"- {assign['assignment_name']}")
        print(f"  Course: {assign['course_code']} - {assign['course_name']}")
        print(f"  Due: {assign['due_date']} | Points: {assign['total_points']}")
    
    # ===== STUDENT: SUBMIT ASSIGNMENT =====
    print("\n13. STUDENT: SUBMIT ASSIGNMENT")
    print("-" * 70)
    
    success, msg = student.submit_assignment(
        assignment_id=assignment_id,
        submission_text="def add_numbers(a, b):\n    return a + b\n\nnum1 = int(input())\nnum2 = int(input())\nprint(add_numbers(num1, num2))"
    )
    print(f"{msg}")
    
    # ===== TEACHER: VIEW SUBMISSIONS =====
    print("\n14. TEACHER: VIEW SUBMISSIONS")
    print("-" * 70)
    
    submissions = teacher.get_assignment_submissions(assignment_id)
    for submission in submissions:
        print(f"- {submission['first_name']} {submission['last_name']}")
        print(f"  Submitted: {submission['submitted_at']}")
        print(f"  Status: {submission['status']}")
    
    # ===== TEACHER: GRADE SUBMISSION =====
    print("\n15. TEACHER: GRADE SUBMISSION")
    print("-" * 70)
    
    success, msg = teacher.grade_submission(
        submission_id=1,
        points_earned=95,
        feedback="Excellent work! The solution is clean and efficient."
    )
    print(f"{msg}")
    
    # ===== STUDENT: VIEW GRADES =====
    print("\n16. STUDENT: VIEW GRADES")
    print("-" * 70)
    
    grades = student.get_grades()
    for grade in grades:
        percentage = (grade['points_earned'] / grade['total_points'] * 100) if grade['points_earned'] else 0
        print(f"- {grade['assignment_name']}")
        print(f"  Course: {grade['course_code']}")
        print(f"  Grade: {grade['points_earned']}/{grade['total_points']} ({percentage:.1f}%)")
        print(f"  Feedback: {grade['feedback']}")
    
    # ===== TEACHER: CREATE ANNOUNCEMENT =====
    print("\n17. TEACHER: CREATE ANNOUNCEMENT")
    print("-" * 70)
    
    success, msg = teacher.create_announcement(
        course_id=course_id,
        title="Welcome to CS101!",
        content="Welcome to Introduction to Computer Science. This course covers fundamental programming concepts. Looking forward to a great semester!"
    )
    print(f"{msg}")
    
    # ===== VIEW ANNOUNCEMENTS =====
    print("\n18. VIEW ANNOUNCEMENTS")
    print("-" * 70)
    
    announcements = teacher.get_course_announcements(course_id)
    for announce in announcements:
        print(f"- [{announce['created_at']}] {announce['title']}")
        print(f"  By: {announce['first_name']} {announce['last_name']}")
        print(f"  {announce['content']}")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print(f"\nDatabase created: lms_demo.db")
    print("All data is persisted in SQLite database")


if __name__ == "__main__":
    demo_lms_system()
