# profile.py

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QMessageBox, QListWidgetItem, QSpacerItem,
    QSizePolicy
)
from PyQt5.QtCore import Qt
import sys
import json
import os
import shutil  # डेटा कॉपी करने के लिए
from pathlib import Path
from github_sync import github_sync

class ProfileModule(QWidget):
    def __init__(self):
        super().__init__()

        # Define the default data folder and file path
        self.data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        self.work_types_file = os.path.join(self.data_folder, 'work_types.json')
        self.work_done_file = os.path.join(self.data_folder, 'work_done.json')

        # Check if running from a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Set up a writable directory in the user's home folder
            user_data_folder = Path.home() / ".my_app_data"
            user_data_folder.mkdir(exist_ok=True)

            # Define path for user-specific data.json
            user_work_types_file = user_data_folder / "work_types.json"
            user_work_done_file = user_data_folder / "work_done.json"

            # Copy data.json from bundled resources if it doesn't exist already
            if not user_work_types_file.exists():
                # Path to data.json within the bundled resources
                bundled_work_types_file = Path(sys._MEIPASS) / "data" / "work_types.json"
                if bundled_work_types_file.exists():
                    shutil.copy(str(bundled_work_types_file), str(user_work_types_file))
                else:
                    # Create empty file if bundled file not found
                    user_work_types_file.write_text("[]")

            if not user_work_done_file.exists():
                # Path to data.json within the bundled resources
                bundled_work_done_file = Path(sys._MEIPASS) / "data" / "work_done.json"
                if bundled_work_done_file.exists():
                    shutil.copy(str(bundled_work_done_file), str(user_work_done_file))
                else:
                    # Create empty file if bundled file not found
                    user_work_done_file.write_text("[]")

            # Update the data_file path to point to the writable copy
            self.work_types_file = str(user_work_types_file)
            self.work_done_file = str(user_work_done_file)
        else:
            # Ensure folder exists in normal environment
            os.makedirs(self.data_folder, exist_ok=True)

        # Ensure data is synced from GitHub
        if not os.path.exists(self.work_types_file):
            github_sync.download_file('work_types.json', self.work_types_file)
        if not os.path.exists(self.work_done_file):
            github_sync.download_file('work_done.json', self.work_done_file)

        # Initialize UI components first
        self.init_ui()

        # Load data after UI is initialized
        self.load_work_types()
        self.load_work_done()

    def init_ui(self):
        """Initialize the user interface components."""
        # Apply the overall stylesheet
        self.setWindowTitle("Manage Work Types and Work Done")
        self.setGeometry(300, 300, 600, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #fff6ee;
            }
            QLabel {
                color: #564234;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QPushButton {
                font-size: 16px;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton#addButton {
                background-color: #4CAF50;
                color: white;
                min-width: 100px;
                max-width: 100px;
                min-height: 40px;
                max-height: 40px;
            }
            QPushButton#addButton:hover {
                background-color: #45a049;
            }
            QPushButton#deleteButton {
                background-color: #f44336;
                color: white;
                min-width: 220px;
                max-width: 220px;
                min-height: 40px;
                max-height: 40px;
            }
            QPushButton#deleteButton:hover {
                background-color: #d32f2f;
            }
            QListWidget {
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                font-size: 14px;
                padding: 5px;
            }
        """)

        # Initialize Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(30)

        header_label = QLabel("Manage Work Types and Work Done")
        header_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #564234;")
        main_layout.addWidget(header_label, alignment=Qt.AlignCenter)

        # Work Types Section
        work_types_label = QLabel("Manage Work Types")
        work_types_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #564234;")
        main_layout.addWidget(work_types_label, alignment=Qt.AlignLeft)

        work_types_input_layout = QHBoxLayout()
        self.new_work_type = QLineEdit()
        self.new_work_type.setPlaceholderText("Enter new Work Type")
        add_work_type_button = QPushButton("Add")
        add_work_type_button.setObjectName("addButton")
        add_work_type_button.setFixedSize(100, 40)
        add_work_type_button.clicked.connect(self.add_work_type)
        work_types_input_layout.addWidget(self.new_work_type)
        work_types_input_layout.addWidget(add_work_type_button)
        main_layout.addLayout(work_types_input_layout)

        self.work_types_list = QListWidget()
        main_layout.addWidget(self.work_types_list)

        delete_work_type_button = QPushButton("Delete Selected Work Types")
        delete_work_type_button.setObjectName("deleteButton")
        delete_work_type_button.setFixedSize(220, 40)
        delete_work_type_button.clicked.connect(self.delete_selected_work_types)
        main_layout.addWidget(delete_work_type_button)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addSpacerItem(spacer)

        # Work Done Section
        work_done_label = QLabel("Manage Work Done")
        work_done_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #564234;")
        main_layout.addWidget(work_done_label, alignment=Qt.AlignLeft)

        work_done_input_layout = QHBoxLayout()
        self.new_work_done = QLineEdit()
        self.new_work_done.setPlaceholderText("Enter new Work Done")
        add_work_done_button = QPushButton("Add")
        add_work_done_button.setObjectName("addButton")
        add_work_done_button.setFixedSize(100, 40)
        add_work_done_button.clicked.connect(self.add_work_done)
        work_done_input_layout.addWidget(self.new_work_done)
        work_done_input_layout.addWidget(add_work_done_button)
        main_layout.addLayout(work_done_input_layout)

        self.work_done_list = QListWidget()
        main_layout.addWidget(self.work_done_list)

        delete_work_done_button = QPushButton("Delete Selected Work Done")
        delete_work_done_button.setObjectName("deleteButton")
        delete_work_done_button.setFixedSize(220, 40)
        delete_work_done_button.clicked.connect(self.delete_selected_work_done)
        main_layout.addWidget(delete_work_done_button)

        self.setLayout(main_layout)

    def load_work_types(self):
        try:
            with open(self.work_types_file, 'r', encoding='utf-8') as f:
                self.work_types = json.load(f)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to decode JSON. Please check the work_types.json file.")
            self.work_types = []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading work types:\n{str(e)}")
            self.work_types = []

        # Display all loaded work types
        self.work_types_list.clear()
        for wt in self.work_types:
            item = QListWidgetItem(wt)
            self.work_types_list.addItem(item)

    def add_work_type(self):
        new_type = self.new_work_type.text().strip()
        if not new_type:
            QMessageBox.warning(self, "Input Error", "Please enter a valid Work Type.")
            return

        existing_types = [self.work_types_list.item(i).text() for i in range(self.work_types_list.count())]
        if new_type in existing_types:
            QMessageBox.warning(self, "Duplicate Entry", "This Work Type already exists.")
            return

        self.work_types_list.addItem(new_type)
        self.new_work_type.clear()
        self.save_work_types()

    def delete_selected_work_types(self):
        selected_items = self.work_types_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select at least one Work Type to delete.")
            return

        for item in selected_items:
            self.work_types_list.takeItem(self.work_types_list.row(item))
        self.save_work_types()

    def save_work_types(self):
        work_types = [self.work_types_list.item(i).text() for i in range(self.work_types_list.count())]
        try:
            with open(self.work_types_file, 'w', encoding='utf-8') as f:
                json.dump(work_types, f, indent=4, ensure_ascii=False)
            # Sync with GitHub
            github_sync.sync_file(self.work_types_file)
            QMessageBox.information(self, "Success", "Work Types have been successfully updated and synced.")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save work types: {str(e)}")
            return False

    def load_work_done(self):
        try:
            with open(self.work_done_file, 'r', encoding='utf-8') as f:
                self.work_done = json.load(f)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to decode JSON. Please check the work_done.json file.")
            self.work_done = []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading work done:\n{str(e)}")
            self.work_done = []

        # Display all loaded work done
        self.work_done_list.clear()
        for wd in self.work_done:
            item = QListWidgetItem(wd)
            self.work_done_list.addItem(item)

    def add_work_done(self):
        new_done = self.new_work_done.text().strip()
        if not new_done:
            QMessageBox.warning(self, "Input Error", "Please enter a valid Work Done entry.")
            return

        existing_done = [self.work_done_list.item(i).text() for i in range(self.work_done_list.count())]
        if new_done in existing_done:
            QMessageBox.warning(self, "Duplicate Entry", "This Work Done entry already exists.")
            return

        self.work_done_list.addItem(new_done)
        self.new_work_done.clear()
        self.save_work_done()

    def delete_selected_work_done(self):
        selected_items = self.work_done_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select at least one Work Done entry to delete.")
            return

        for item in selected_items:
            self.work_done_list.takeItem(self.work_done_list.row(item))
        self.save_work_done()

    def save_work_done(self):
        work_done = [self.work_done_list.item(i).text() for i in range(self.work_done_list.count())]
        try:
            with open(self.work_done_file, 'w', encoding='utf-8') as f:
                json.dump(work_done, f, indent=4, ensure_ascii=False)
            # Sync with GitHub
            github_sync.sync_file(self.work_done_file)
            QMessageBox.information(self, "Success", "Work Done entries have been successfully updated and synced.")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save work done: {str(e)}")
            return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProfileModule()
    window.show()
    sys.exit(app.exec_())
