import sys
import os
import json
import uuid
import shutil  # Ensure shutil is imported for file operations
from pathlib import Path
from PIL import Image
import io

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QStackedWidget, QMessageBox, QPushButton, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from dashboard import DashboardModule
from finalized_report import FinalizedReportModule
from add_entry import AddEntryModule
from report import ReportModule
from payment import PaymentModule
from approve import ApprovalModule
from paymentdon import PaymentDoneModule
from profile import ProfileModule
from manage_locations import ManageLocationsModule

from github_sync import github_sync

# NEW: import PrintReportModule
from print_report import PrintReportModule
from updater import show_update_dialog

# User credentials and roles
USERS = {
    'all': {
        'password': 'all123',
        'role': 'regular'
    },
    'vip_user': {
        'password': 'vippass',
        'role': 'vip'
    }
}

DATA_DIR = 'data'
LICENSE_FILE = os.path.join(DATA_DIR, 'license_active.json')

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_app_icon():
    """Get application icon path"""
    try:
        # Try to use ICO file directly
        ico_path = resource_path(os.path.join('icons', 'app_icon.ico'))
        if os.path.exists(ico_path):
            return ico_path
            
        # If ICO doesn't exist, try PNG
        png_path = resource_path(os.path.join('icons', 'app_icon.png'))
        if os.path.exists(png_path):
            return png_path
            
        return None
    except Exception as e:
        print(f"Error loading icon: {e}")
        return None

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Set application icon globally
app = QApplication(sys.argv)
icon_path = get_app_icon()
if icon_path:
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

class LicenseWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Global Engineering - License Activation")
        self.setGeometry(600, 300, 400, 400)
        self.setStyleSheet("background-color: #FFF6EE;")
        
        # Set application icon
        icon_path = get_app_icon()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        # Title
        self.title_label = QLabel("Activate License")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #B75700;
            }
        """)
        layout.addWidget(self.title_label)

        # Email
        self.email_label = QLabel("Email ID:")
        self.email_label.setStyleSheet("font-size: 14px; color: #564234;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setFixedHeight(30)
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #B75700;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        # Password
        self.password_label = QLabel("Password:")
        self.password_label.setStyleSheet("font-size: 14px; color: #564234;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(30)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #B75700;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # License Key
        self.license_label = QLabel("License Key:")
        self.license_label.setStyleSheet("font-size: 14px; color: #564234;")
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Enter your license key")
        self.license_input.setFixedHeight(30)
        self.license_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #B75700;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.license_label)
        layout.addWidget(self.license_input)

        # Activate button
        self.activate_button = QPushButton("Activate")
        self.activate_button.setFixedHeight(40)
        self.activate_button.setStyleSheet("""
            QPushButton {
                background-color: #FFA33E;
                border: none;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #FF8C00;
            }
        """)
        self.activate_button.clicked.connect(self.handle_activation)
        layout.addSpacing(20)
        layout.addWidget(self.activate_button)

        self.setLayout(layout)

    def handle_activation(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        license_key = self.license_input.text().strip()

        if not email or not password or not license_key:
            QMessageBox.warning(self, 'Error', 'Please fill all fields.')
            return

        device_id = self.get_device_id()

        # Check if license is already activated
        if os.path.exists(LICENSE_FILE):
            with open(LICENSE_FILE, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}

            existing_license_key = data.get('license_key', '')
            existing_device_id = data.get('device_id', '')

            if existing_license_key:
                if existing_license_key == license_key:
                    if existing_device_id == device_id:
                        QMessageBox.information(self, 'Info', 'License already activated on this device.')
                        self.open_login_window()
                        self.close()
                        return
                    else:
                        QMessageBox.warning(self, 'Error', 'License key is already activated on another device.')
                        return
                else:
                    QMessageBox.warning(self, 'Error', 'Invalid license key or already in use.')
                    return

        # Save license info
        license_data = {
            "email": email,
            "password": password,
            "license_key": license_key,
            "device_id": device_id
        }

        try:
            with open(LICENSE_FILE, 'w') as f:
                json.dump(license_data, f, indent=4)
            QMessageBox.information(self, 'Success', 'License activated successfully.')
            self.open_login_window()
            self.close()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to activate license: {str(e)}')

    def get_device_id(self):
        return str(uuid.getnode())

    def open_login_window(self):
        self.login_window = LoginWindow()
        self.login_window.show()


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Global Engineering - Login")
        self.setGeometry(600, 300, 400, 400)
        self.setStyleSheet("background-color: #FFF6EE;")
        
        # Set application icon
        icon_path = get_app_icon()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        # Title
        self.title_label = QLabel("Log in")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #B75700;
            }
        """)
        layout.addWidget(self.title_label)

        # Username
        self.username_label = QLabel("Username:")
        self.username_label.setStyleSheet("font-size: 14px; color: #564234;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFixedHeight(30)
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #B75700;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        # Password
        self.password_label = QLabel("Password:")
        self.password_label.setStyleSheet("font-size: 14px; color: #564234;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(30)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #B75700;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setFixedHeight(40)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #FFA33E;
                border: none;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #FF8C00;
            }
        """)
        self.login_button.clicked.connect(self.handle_login)

        # Activate License button
        self.activate_license_button = QPushButton("Activate License")
        self.activate_license_button.setFixedHeight(40)
        self.activate_license_button.setStyleSheet("""
            QPushButton {
                background-color: #B75700;
                border: none;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #D86D01;
            }
        """)
        self.activate_license_button.clicked.connect(self.open_license_window)

        layout.addSpacing(20)
        layout.addWidget(self.login_button)
        layout.addSpacing(10)
        layout.addWidget(self.activate_license_button)

        self.setLayout(layout)

    def handle_login(self):
        if not self.is_license_active():
            QMessageBox.warning(self, 'Error', 'Please activate your license first.')
            return

        username = self.username_input.text()
        password = self.password_input.text()

        if username in USERS and USERS[username]['password'] == password:
            role = USERS[username]['role']
            self.open_main_window(role)
        else:
            QMessageBox.warning(self, 'Error', 'Incorrect username or password')

    def is_license_active(self):
        if not os.path.exists(LICENSE_FILE):
            return False
        with open(LICENSE_FILE, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return False
            license_key = data.get('license_key', '')
            device_id = data.get('device_id', '')
            current_device_id = self.get_device_id()

            if device_id != current_device_id or not license_key:
                return False

            return True

    def get_device_id(self):
        return str(uuid.getnode())

    def open_main_window(self, role):
        self.main_window = MainWindow(user_role=role)
        self.main_window.show()
        self.close()

    def open_license_window(self):
        self.license_window = LicenseWindow()
        self.license_window.show()
        self.close()


class MainWindow(QWidget):
    def __init__(self, user_role='regular'):
        super().__init__()
        self.user_role = user_role
        self.setWindowTitle("Global Engineering")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #FFF6EE;")
        
        # Set application icon
        icon_path = get_app_icon()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        
        # Store icons folder path
        self.icons_folder = resource_path('icons')

        # Load locations data
        self.user_data_folder = os.path.join(str(Path.home()), '.my_app_data')
        self.locations_file = os.path.join(self.user_data_folder, 'locations.json')
        try:
            with open(self.locations_file, 'r', encoding='utf-8') as f:
                self.locations_data = json.load(f)
        except:
            self.locations_data = {}

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Layout
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_layout.setSpacing(15)

        # Sidebar Buttons
        self.dashboard_button = self.add_sidebar_button("\U0001F4CA Dashboard", "#ffe5cc", active=True)
        self.add_entry_button = self.add_sidebar_button("\U00002795 Add Entry", "#ffe5cc")
        self.report_button = self.add_sidebar_button("\U0001F4C8 All Cases", "#ffe5cc")
        self.payment_button = self.add_sidebar_button("\U0001F4B8 Payment", "#ffe5cc")
        self.approve_button = self.add_sidebar_button("\U00002705 Approve", "#ffe5cc")
        self.payment_done_button = self.add_sidebar_button("\U0001F4B3 Payment Done", "#ffe5cc")
        self.finalized_report_button = self.add_sidebar_button("\U0001F4C4 Finalized Report", "#ffe5cc")
        self.print_report_button = self.add_sidebar_button("\U0001F5A8 Print Report", "#ffe5cc")
        self.manage_locations_button = self.add_sidebar_button("\U0001F4CD Manage Locations", "#ffe5cc")
        self.profile_button = self.add_sidebar_button("\U0001F464 Profile", "#ffe5cc")
        self.logout_button = self.add_sidebar_button("\U0001F511 Logout", "#896e58")

        # Role-based visibility
        if self.user_role == 'regular':
            self.dashboard_button.hide()
            self.payment_button.hide()
            self.approve_button.hide()
            self.payment_done_button.hide()
            self.profile_button.hide()
            self.finalized_report_button.hide()
            self.print_report_button.hide()
            self.report_button.hide()
            self.manage_locations_button.hide()
        elif self.user_role == 'vip':
            pass

        self.sidebar_layout.addStretch()

        sidebar_content = QWidget()
        sidebar_content.setLayout(self.sidebar_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(sidebar_content)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setFixedWidth(200)
        self.scroll_area.setStyleSheet("background-color: #FFA33E; border: none;")

        main_layout.addWidget(self.scroll_area)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.dashboard_module = DashboardModule()
        self.stacked_widget.addWidget(self.dashboard_module)

        self.add_entry_module = AddEntryModule()
        self.stacked_widget.addWidget(self.add_entry_module)

        self.report_module = ReportModule()
        self.stacked_widget.addWidget(self.report_module)

        self.payment_module = PaymentModule()
        self.stacked_widget.addWidget(self.payment_module)

        self.approval_module = ApprovalModule()
        self.stacked_widget.addWidget(self.approval_module)

        self.payment_done_module = PaymentDoneModule()
        self.stacked_widget.addWidget(self.payment_done_module)

        self.finalized_report_module = FinalizedReportModule()
        self.stacked_widget.addWidget(self.finalized_report_module)

        self.print_report_module = PrintReportModule()
        self.stacked_widget.addWidget(self.print_report_module)

        self.profile_module = ProfileModule()
        self.stacked_widget.addWidget(self.profile_module)

        if self.user_role == 'regular':
            self.stacked_widget.setCurrentWidget(self.add_entry_module)
            self.update_sidebar_styles(active_button=self.add_entry_button)
        else:
            self.stacked_widget.setCurrentWidget(self.dashboard_module)
            self.update_sidebar_styles(active_button=self.dashboard_button)

        self.setLayout(main_layout)

        self.dashboard_button.clicked.connect(self.show_dashboard)
        self.add_entry_button.clicked.connect(self.show_add_entry_module)
        self.report_button.clicked.connect(self.show_report_module)
        self.payment_button.clicked.connect(self.show_payment_module)
        self.approve_button.clicked.connect(self.show_approval_module)
        self.payment_done_button.clicked.connect(self.show_payment_done_module)
        self.finalized_report_button.clicked.connect(self.show_finalized_report_module)
        self.print_report_button.clicked.connect(self.show_print_report_module)
        self.profile_button.clicked.connect(self.show_profile_module)
        self.logout_button.clicked.connect(self.logout)
        self.manage_locations_button.clicked.connect(self.show_manage_locations)

    def add_sidebar_button(self, text, bg_color, active=False):
        button = QPushButton(text)
        button.setFixedSize(180, 50)
        if active:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #ffa33e;
                    border: none;
                    padding: 10px;
                    text-align: left;
                    font-size: 14px;
                    font-weight: bold;
                    color: #564234;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #ff8c00;
                }
            """)
        else:
            if text == "\U0001F511 Logout":
                bg = "#896e58"
            else:
                bg = "#ffe5cc"
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    border: none;
                    padding: 10px;
                    text-align: left;
                    font-size: 14px;
                    font-weight: bold;
                    color: #564234;
                    border-radius: 5px;
                }}
                QPushButton:hover {{
                    background-color: #ffd2a6;
                }}
            """)
        self.sidebar_layout.addWidget(button)
        return button

    def show_dashboard(self):
        self.stacked_widget.setCurrentWidget(self.dashboard_module)
        self.update_sidebar_styles(self.dashboard_button)

    def show_add_entry_module(self):
        self.stacked_widget.setCurrentWidget(self.add_entry_module)
        self.update_sidebar_styles(self.add_entry_button)

    def show_report_module(self):
        self.stacked_widget.setCurrentWidget(self.report_module)
        self.update_sidebar_styles(self.report_button)

    def show_payment_module(self):
        self.stacked_widget.setCurrentWidget(self.payment_module)
        self.update_sidebar_styles(self.payment_button)

    def show_approval_module(self):
        self.stacked_widget.setCurrentWidget(self.approval_module)
        self.update_sidebar_styles(self.approve_button)

    def show_payment_done_module(self):
        self.stacked_widget.setCurrentWidget(self.payment_done_module)
        self.update_sidebar_styles(self.payment_done_button)

    def show_finalized_report_module(self):
        self.stacked_widget.setCurrentWidget(self.finalized_report_module)
        self.update_sidebar_styles(self.finalized_report_button)

    def show_print_report_module(self):
        self.stacked_widget.setCurrentWidget(self.print_report_module)
        self.update_sidebar_styles(self.print_report_button)

    def show_profile_module(self):
        self.stacked_widget.setCurrentWidget(self.profile_module)
        self.update_sidebar_styles(self.profile_button)

    def show_manage_locations(self):
        self.manage_locations_dialog = ManageLocationsModule(self.locations_data, self.locations_file, self)
        self.manage_locations_dialog.exec_()
        self.update_sidebar_styles(self.manage_locations_button)

    def logout(self):
        reply = QMessageBox.question(
            self, 'Logout Confirmation',
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()

    def update_sidebar_styles(self, active_button):
        buttons = [
            self.dashboard_button, self.add_entry_button, self.report_button,
            self.payment_button, self.approve_button, self.payment_done_button,
            self.finalized_report_button, self.print_report_button,
            self.profile_button, self.logout_button, self.manage_locations_button
        ]
        for btn in buttons:
            if btn == active_button:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #B75700;
                        border: none;
                        padding: 10px;
                        text-align: left;
                        font-size: 14px;
                        font-weight: bold;
                        color: #FFCD97;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #D86D01;
                        color: #ffffff;
                    }
                """)
            else:
                if btn == self.logout_button:
                    bg = "#896e58"
                else:
                    bg = "#ffe5cc"
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {bg};
                        border: none;
                        padding: 10px;
                        text-align: left;
                        font-size: 14px;
                        font-weight: bold;
                        color: #564234;
                        border-radius: 5px;
                    }}
                    QPushButton:hover {{
                        background-color: #ffd2a6;
                    }}
                """)

    def check_for_updates(self):
        show_update_dialog()

def sync_all_data():
    """Sync all data files from GitHub"""
    data_files = [
        'data.json',
        'work_types.json',
        'work_done.json',
        'locations.json'
    ]
    
    user_data_folder = os.path.join(str(Path.home()), '.my_app_data')
    os.makedirs(user_data_folder, exist_ok=True)
    
    failed_files = []
    for file in data_files:
        local_path = os.path.join(user_data_folder, file)
        if not github_sync.download_file(file, local_path):
            failed_files.append(file)
            
    return failed_files

if __name__ == "__main__":
    try:
        # Create loading splash screen
        splash = QLabel("Syncing data files...")
        splash.setWindowIcon(app_icon if 'app_icon' in locals() else QIcon())
        splash.setStyleSheet("""
            QLabel {
                background-color: #FFF6EE;
                color: #564234;
                padding: 20px;
                border: 2px solid #ffcea1;
                border-radius: 10px;
                font-size: 16px;
            }
        """)
        splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        # Center the splash screen
        screen = app.primaryScreen().geometry()
        splash.move(screen.center() - splash.rect().center())
        splash.show()
        app.processEvents()  # Ensure splash is shown
        
        # Sync data files
        failed_files = sync_all_data()
        splash.close()
        
        if failed_files:
            error_msg = "Following files failed to sync:\n- " + "\n- ".join(failed_files)
            error_msg += "\n\nThe app will use local data if available."
            QMessageBox.warning(None, "Sync Warning", error_msg)
        
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to initialize application: {str(e)}")
        sys.exit(1)
    
    login = LoginWindow()
    login.show()
    sys.exit(app.exec_())
