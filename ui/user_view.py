from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListWidget, QMessageBox, QHBoxLayout, QComboBox, QFrame
)
from PyQt6.QtGui import QPalette, QBrush, QPixmap
from PyQt6.QtCore import Qt
from models.user import User
import sqlite3
from database.db_handler import get_db_connection


class UserView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
              QWidget {
                  background-color: #F4F6F7;
              }
              QLineEdit {
                  padding: 8px;
                  border: 1px solid #ccc;
                  border-radius: 6px;
                  font-size: 14px;
              }
              QPushButton {
                  padding: 9px 15px;
                  border-radius: 6px;
                  background-color: #2E86C1;
                  color: white;
                  font-weight: bold;
              }
              QPushButton:hover {
                  background-color: #21618C;
              }
              QListWidget {
                  border: 1px solid #ccc;
                  border-radius: 6px;
                  padding: 6px;
              }
          """)

        main_layout = QVBoxLayout()

        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 10px; padding: 20px;")
        card_layout = QVBoxLayout()

        self.layout = QVBoxLayout()

        # Input username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.layout.addWidget(self.username_input)

        # Input password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addWidget(self.password_input)

        # Role selection ComboBox
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Admin", "Manager", "C.E.O"])
        self.role_combo.setEditable(True)  # Enable search/filter
        self.layout.addWidget(self.role_combo)

        # Add User Button
        add_button = QPushButton("Add User")
        add_button.clicked.connect(self.add_user)
        self.layout.addWidget(add_button)

        # User List
        self.user_list = QListWidget()
        self.layout.addWidget(self.user_list)

        # Delete Button
        delete_button = QPushButton("Delete Selected User")
        delete_button.clicked.connect(self.delete_user)
        self.layout.addWidget(delete_button)

        self.setLayout(self.layout)
        self.load_users()


    def load_users(self):
        self.user_list.clear()
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT username, role FROM users ORDER BY username")
        users = cursor.fetchall()
        connection.close()

        for user in users:
            self.user_list.addItem(f"{user[0]} ({user[1]})")

    def add_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password cannot be empty.")
            return

        try:
            User.add_user(username, password, role)
            QMessageBox.information(self, "Success", f"User '{username}' added as '{role}'.")
            self.load_users()
            self.username_input.clear()
            self.password_input.clear()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", f"Username '{username}' already exists.")

    def delete_user(self):
        selected_item = self.user_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Select User", "Please select a user to delete.")
            return

        username = selected_item.text().split(" (")[0]  # Cleanly extract username
        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete user '{username}'?")

        if confirm == QMessageBox.StandardButton.Yes:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            connection.commit()
            connection.close()
            QMessageBox.information(self, "Deleted", f"User '{username}' deleted.")
            self.load_users()
