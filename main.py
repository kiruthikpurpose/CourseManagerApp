import sys
import sqlite3
import hashlib
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
                             QMessageBox, QDialog, QLineEdit, QFormLayout,
                             QDialogButtonBox, QTableWidget, QTableWidgetItem)

class DatabaseManager:
    def __init__(self):
        self.connection = sqlite3.connect('college_enrollment.db')
        self.create_tables()

    def create_tables(self):
        with self.connection:
            self.connection.execute('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, course_name TEXT, course_code TEXT, min_cgpa REAL, credits INTEGER)')
            self.connection.execute('CREATE TABLE IF NOT EXISTS admin_credentials (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT)')

    def add_course(self, course_name, course_code, min_cgpa, credits):
        with self.connection:
            self.connection.execute('INSERT INTO courses (course_name, course_code, min_cgpa, credits) VALUES (?, ?, ?, ?)', (course_name, course_code, min_cgpa, credits))

    def delete_course(self, course_id):
        with self.connection:
            self.connection.execute('DELETE FROM courses WHERE id = ?', (course_id,))

    def get_courses(self):
        with self.connection:
            return self.connection.execute('SELECT * FROM courses').fetchall()

    def get_admin_credentials(self):
        with self.connection:
            return self.connection.execute('SELECT username, password_hash FROM admin_credentials').fetchone()

    def add_admin_credentials(self, username, password_hash):
        with self.connection:
            self.connection.execute('INSERT INTO admin_credentials (username, password_hash) VALUES (?, ?)')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("College Enrollment System")
        layout = QVBoxLayout()
        self.student_button = QPushButton("Student Login")
        self.admin_button = QPushButton("Admin Login")
        layout.addWidget(self.student_button)
        layout.addWidget(self.admin_button)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.student_button.clicked.connect(self.show_student_login)
        self.admin_button.clicked.connect(self.show_admin_login)

    def show_student_login(self):
        pass

    def show_admin_login(self):
        self.admin_login = AdminLoginDialog()
        if self.admin_login.exec_() == QDialog.Accepted:
            self.admin_dashboard = AdminDashboard()
            self.admin_dashboard.show()

class AdminLoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Login")
        layout = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        layout.addRow("Username:", self.username)
        layout.addRow("Password:", self.password)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def accept(self):
        db_manager = DatabaseManager()
        credentials = db_manager.get_admin_credentials()
        if credentials:
            username, password_hash = credentials
            input_hash = hashlib.sha256(self.password.text().encode()).hexdigest()
            if self.username.text() == username and input_hash == password_hash:
                super().accept()
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password")
                self.reject()
        else:
            QMessageBox.warning(self, "Error", "No admin credentials found")
            self.reject()

class AdminDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Dashboard")
        self.db_manager = DatabaseManager()
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.load_courses()
        self.add_course_button = QPushButton("Add Course")
        self.add_course_button.clicked.connect(self.add_course)
        layout.addWidget(self.table)
        layout.addWidget(self.add_course_button)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_courses(self):
        courses = self.db_manager.get_courses()
        self.table.setRowCount(len(courses))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Course Name", "Course Code", "Min CGPA", "Credits"])
        for row, course in enumerate(courses):
            for col, data in enumerate(course):
                self.table.setItem(row, col, QTableWidgetItem(str(data)))
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, cid=course[0]: self.delete_course(cid))
            self.table.setCellWidget(row, 5, delete_button)

    def add_course(self):
        dialog = AddCourseDialog(self.db_manager)
        if dialog.exec_() == QDialog.Accepted:
            self.load_courses()

    def delete_course(self, course_id):
        self.db_manager.delete_course(course_id)
        self.load_courses()

class AddCourseDialog(QDialog):
    def __init__(self, db_manager):
        super().__init__()
        self.setWindowTitle("Add Course")
        self.db_manager = db_manager
        layout = QFormLayout()
        self.course_name = QLineEdit()
        self.course_code = QLineEdit()
        self.min_cgpa = QLineEdit()
        self.credits = QLineEdit()
        layout.addRow("Course Name:", self.course_name)
        layout.addRow("Course Code:", self.course_code)
        layout.addRow("Min CGPA:", self.min_cgpa)
        layout.addRow("Credits:", self.credits)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def accept(self):
        course_name = self.course_name.text()
        course_code = self.course_code.text()
        min_cgpa = float(self.min_cgpa.text())
        credits = int(self.credits.text())
        self.db_manager.add_course(course_name, course_code, min_cgpa, credits)
        super().accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
