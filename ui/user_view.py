#Import Framework and Library
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListWidget, QMessageBox, QComboBox, QFrame
)
from models.user import User
import sqlite3
from database.db_handler import get_db_connection

#User View Class
class UserView(QWidget):
    def __init__(self, current_user_role="Manager"):
        super().__init__()
        self.current_user_role = current_user_role
        #UserView Style
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
                  background-color: #21618C;
                  color: white;
                  font-weight: bold;
              }
              QPushButton:hover {
                  background-color: #3498db;
              }
              QListWidget {
                  border: 1px solid #ccc;
                  border-radius: 6px;
                  padding: 6px;
              }
          """)

        main_layout = QVBoxLayout() #Set Layout

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
        self.password_input.returnPressed.connect(self.add_user)
        self.username_input.returnPressed.connect(self.add_user)
        self.layout.addWidget(self.password_input)

        role_layout = QVBoxLayout()
        role_label = QLabel("Access Level:")
        self.role_combo = QComboBox()
        # Include all roles so Admin users and Admin accounts can be viewed.
        # Permission checks later will prevent non-Admins from creating/editing/deleting Admin users.
        self.role_combo.addItems(["Manager", "CEO", "Admin"])
        role_layout.addWidget(role_label)
        role_layout.addWidget(self.role_combo)
        self.layout.addLayout(role_layout)



        # Add User Button
        add_button = QPushButton("Add User")
        add_button.clicked.connect(self.add_user)
        self.layout.addWidget(add_button)


        # User List
        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self.populate_user_fields)
        self.layout.addWidget(self.user_list)

        # Update User Button
        update_button = QPushButton("Update User")
        update_button.clicked.connect(self.update_user)
        self.layout.addWidget(update_button)


        # Delete User Button
        delete_button = QPushButton("Delete Selected User")
        delete_button.clicked.connect(self.delete_user)
        self.layout.addWidget(delete_button)

        self.setLayout(self.layout)
        self.load_users()

    #Load all current Users
    def load_users(self):
        self.user_list.clear()
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT username, role FROM users ORDER BY username")
        users = cursor.fetchall()
        connection.close()

        for user in users:
            self.user_list.addItem(f"{user[0]} ({user[1]})")

    #Act Upon Click on Add User
    def add_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()
        # Compare roles case-insensitively to avoid mismatch when role strings differ in case
        if role.lower() == "admin" and str(self.current_user_role).lower() != "admin":
            QMessageBox.warning(self, "Permission Denied", "Only Admin can add another Admin user.")
            return

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

    # Populate fields with user data for editing
    def populate_user_fields(self, item):
        # Defensive: Ensure item has the expected format
        text = item.text()
        if " (" not in text:
            QMessageBox.warning(self, "Error", "Selected item format is invalid.")
            return
        username = text.split(" (" )[0]
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT username, role FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        connection.close()
        if user:
            self.username_input.setText(user[0])
            self.password_input.clear()  # Do not show password hash
            # Ensure the role exists in the combo box (in case roles list changes elsewhere)
            if self.role_combo.findText(user[1]) == -1:
                self.role_combo.addItem(user[1])
            self.role_combo.setCurrentText(user[1])
        else:
             QMessageBox.warning(self, "Error", f"User '{username}' not found in database.")

    def update_user(self):
        selected_item = self.user_list.currentItem()
        if not selected_item:
            return
        username = selected_item.text().split(" (")[0]
        role = self.role_combo.currentText()
        # Prevent editing Admin details unless the current user is Admin
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT role FROM users WHERE username=?", (username,))
        user_role = cursor.fetchone()
        connection.close()
        if user_role and str(user_role[0]).lower() == "admin" and str(self.current_user_role).lower() != "admin":
            QMessageBox.warning(self, "Permission Denied", "Only Admin can edit Admin user details.")
            return
        new_username = self.username_input.text().strip()
        new_password = self.password_input.text().strip()
        new_role = self.role_combo.currentText()
        if not new_username or not new_password:
            QMessageBox.warning(self, "Input Error", "Username and password cannot be empty.")
            return
        try:
            User.update_user(username, new_username, new_password, new_role)
            QMessageBox.information(self, "Success", f"User '{username}' updated.")
            self.load_users()
            self.username_input.clear()
            self.password_input.clear()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))


     #Act Upon a click on Delete User
    def delete_user(self):
        selected_item = self.user_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Select User", "Please select a user to delete.")
            return
        username = selected_item.text().split(" (" )[0]
        # Check if target user is Admin
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
        user_role = cursor.fetchone()
        connection.close()
        if user_role and str(user_role[0]).lower() == "admin" and str(self.current_user_role).lower() != "admin":
            QMessageBox.warning(self, "Permission Denied", "Only Admin can delete Admin user.")
            return
        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete user '{username}'?")
        if confirm == QMessageBox.StandardButton.Yes:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            connection.commit()
            connection.close()
            QMessageBox.information(self, "Deleted", f"User '{username}' deleted.")
            self.load_users()
