# report_module.py

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QSpacerItem, QSizePolicy, QHeaderView, QDialog, QFormLayout, QDialogButtonBox,
    QGridLayout, QAbstractItemView, QDateEdit, QGroupBox, QScrollArea, QTextEdit,
    QTabWidget, QCheckBox, QCompleter, QFileDialog
)
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap, QIntValidator, QPainter, QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import Qt, QStringListModel, QDate, QEvent
from PyQt5.QtWidgets import QCompleter
import sys
import json
import os
from functools import partial
from datetime import datetime
from github_sync import github_sync
from pathlib import Path
from activity_tracker import ActivityTracker

# ======================== Custom ComboBox Classes ========================
class NoScrollComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                padding: 4px 8px;
                font-family: 'Century Gothic';
            }
            QComboBox::drop-down {
                width: 24px;
                border-left: 1px solid #ffcea1;
            }
            QComboBox::down-arrow {
                image: url(icons/dropdown_arrow.svg);
                width: 10px;
                height: 10px;
            }
        """)
    def wheelEvent(self, event):
        event.ignore()

class CustomComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                padding: 4px 8px;
                font-family: 'Century Gothic';
            }
            QComboBox::drop-down {
                width: 24px;
                border-left: 1px solid #ffcea1;
            }
            QComboBox::down-arrow {
                image: url(icons/dropdown_arrow.svg);
                width: 10px;
                height: 10px;
            }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        arrow_color = QColor("#564234")
        painter.setPen(arrow_color)
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(rect.adjusted(0, 0, -10, 0), Qt.AlignVCenter | Qt.AlignRight, " ")
        painter.end()
        
    def wheelEvent(self, event):
        event.ignore()

# ======================== ViewDialog Class ========================
class ViewDialog(QDialog):
    def __init__(self, entry, icons_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("View Entry Details")
        self.entry = entry
        self.icons_path = icons_path
        self.setMinimumWidth(600)
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Style for section headers
        section_style = """
            QLabel {
                color: #2c3e50;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """

        # Style for field labels
        label_style = """
            QLabel {
                color: #34495e;
                font-size: 14px;
                font-weight: bold;
                background-color: #e8f4f8;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #bce0ee;
            }
        """

        # Style for values
        value_style = """
            QLabel {
                color: #2c3e50;
                font-size: 14px;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
                border: 1px solid #dee2e6;
            }
        """

        # Basic Information Section
        basic_info_header = QLabel("Basic Information")
        basic_info_header.setStyleSheet(section_style)
        main_layout.addWidget(basic_info_header)

        basic_info_layout = QGridLayout()
        basic_info_layout.setSpacing(15)

        # Basic Information Fields
        basic_fields = [
            ("File No.", "File No."),
            ("Customer Name", "Customer Name"),
            ("Date", "Date"),
            ("Mobile Number", "Mobile Number"),
            ("District", "District"),
            ("R.S.No./ Block No.", "R.S.No./ Block No."),
            ("New No.", "New No."),
            ("Old No.", "Old No."),
            ("Taluka", "Taluka"),
            ("Village", "Village"),
            ("Final Amount", "Final Amount"),
            ("Party Address", "Party Address")
        ]

        for i, (label_text, key) in enumerate(basic_fields):
            row = i // 2
            col = i % 2 * 2

            label = QLabel(f"{label_text}:")
            label.setStyleSheet(label_style)
            
            # Special handling for Party Address to remove {} and format empty values
            if key == "Party Address":
                value_text = str(self.entry.get(key, "")).strip("{} ")
                if not value_text:
                    value_text = ""
            else:
                value_text = str(self.entry.get(key, ""))
            
            value = QLabel(value_text)
            value.setStyleSheet(value_style)
            value.setWordWrap(True)
            
            # Make Party Address value take full width
            if key == "Party Address":
                basic_info_layout.addWidget(label, row, 0)
                basic_info_layout.addWidget(value, row, 1, 1, 3)  # Span 3 columns
            else:
                basic_info_layout.addWidget(label, row, col)
                basic_info_layout.addWidget(value, row, col + 1)

        main_layout.addLayout(basic_info_layout)

        # Location Information Section
        location_header = QLabel("Location Information")
        location_header.setStyleSheet(section_style)
        main_layout.addWidget(location_header)

        location_layout = QGridLayout()
        location_layout.setSpacing(15)

        # Location Fields
        location_fields = [
            ("District", "District"),
            ("Taluka", "Taluka"),
            ("Village", "Village"),
            ("R.S.No./ Block No.", "R.S.No./ Block No."),
            ("New No.", "New No."),
            ("Old No.", "Old No.")
        ]

        for i, (label_text, key) in enumerate(location_fields):
            row = i // 2
            col = i % 2 * 2

            label = QLabel(f"{label_text}:")
            label.setStyleSheet(label_style)
            
            # Get the value from entry, with special handling for District and Taluka
            if key in ["District", "Taluka"]:
                value_text = str(self.entry.get(key, ""))
                if not value_text:
                    value_text = "Select " + key
            else:
                value_text = str(self.entry.get(key, ""))
            
            value = QLabel(value_text)
            value.setStyleSheet(value_style)
            value.setWordWrap(True)

            location_layout.addWidget(label, row, col)
            location_layout.addWidget(value, row, col + 1)

        main_layout.addLayout(location_layout)

        # Work Information Section
        work_header = QLabel("Work Information")
        work_header.setStyleSheet(section_style)
        main_layout.addWidget(work_header)

        work_layout = QVBoxLayout()
        work_layout.setSpacing(15)

        # Work Types
        work_types_label = QLabel("Work Types:")
        work_types_label.setStyleSheet(label_style)
        work_types_value = QLabel(", ".join(self.entry.get("Work Types", [])))
        work_types_value.setStyleSheet(value_style)
        work_types_value.setWordWrap(True)
        work_layout.addWidget(work_types_label)
        work_layout.addWidget(work_types_value)

        # Work Done
        work_done_label = QLabel("Work Done:")
        work_done_label.setStyleSheet(label_style)
        work_done_value = QLabel(", ".join(self.entry.get("Work Done", [])))
        work_done_value.setStyleSheet(value_style)
        work_done_value.setWordWrap(True)
        work_layout.addWidget(work_done_label)
        work_layout.addWidget(work_done_value)

        main_layout.addLayout(work_layout)

        # PDF and Close buttons
        pdf_button = QPushButton("Generate PDF")
        pdf_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219a52;
            }
        """)
        pdf_button.clicked.connect(self.print_info)

        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        close_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(pdf_button)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

    def print_info(self):
        """Generate PDF document for the entry"""
        try:
            doc = QTextDocument()
            
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # Create list of fields with data
            fields_data = [
                ("File No.", self.entry.get("File No.", "")),
                ("Customer Name", self.entry.get("Customer Name", "")),
                ("Date", f"Date {self.entry.get('Date', '')}" if self.entry.get('Date') else ""),
                ("Mobile Number", self.entry.get("Mobile Number", "")),
                ("District", self.entry.get("District", "")),
                ("Taluka", self.entry.get("Taluka", "")),
                ("Village", self.entry.get("Village", "")),
                ("R.S.No./ Block No.", self.entry.get("R.S.No./ Block No.", "")),
                ("New No.", self.entry.get("New No.", "")),
                ("Old No. -", self.entry.get("Old No.", "")),
                ("Plot No. -", self.entry.get("Old No.", "")),
                ("Work Types", ", ".join(self.entry.get("Work Types", []))),
                ("Work Done", ", ".join(self.entry.get("Work Done", []))),
                ("Final Amount", self.entry.get("Final Amount", "")),
                ("Remark", self.entry.get("Remark", ""))
            ]
            
            html = f"""
            <html>
            <head>
                <style>
                    @page {{
                        margin: 2.5cm;
                        size: A4;
                    }}
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.8;
                        color: #333333;
                        margin: 0;
                        padding: 0;
                        background-color: #ffffff;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 40px;
                        padding: 20px;
                        background: linear-gradient(to bottom, #fff6ee, #ffffff);
                        border-bottom: 3px solid #d17a24;
                    }}
                    .logo {{
                        width: 180px;
                        height: auto;
                        margin-bottom: 15px;
                    }}
                    .company-name {{
                        font-size: 32px;
                        font-weight: bold;
                        color: #d17a24;
                        margin-bottom: 10px;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                    }}
                    .title {{
                        font-size: 28px;
                        font-weight: bold;
                        text-align: center;
                        margin: 30px 0;
                        color: #564234;
                        text-transform: uppercase;
                        padding: 15px;
                        background-color: #fff6ee;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .main-table {{
                        width: 100%;
                        border-collapse: separate;
                        border-spacing: 0;
                        margin-bottom: 50px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        border-radius: 8px;
                        overflow: hidden;
                    }}
                    .main-table th, .main-table td {{
                        border: 1px solid #ffcea1;
                        padding: 15px 25px;
                        text-align: left;
                    }}
                    .main-table th {{
                        font-size: 16px;
                        font-weight: bold;
                        width: 35%;
                        background-color: #fff6ee;
                        color: #564234;
                        text-transform: uppercase;
                    }}
                    .main-table td {{
                        font-size: 15px;
                        background-color: #ffffff;
                        color: #333333;
                    }}
                    .main-table tr:hover td {{
                        background-color: #fffaf5;
                    }}
                    .footer {{
                        text-align: center;
                        font-size: 14px;
                        color: #564234;
                        border-top: 2px solid #ffcea1;
                        padding: 25px;
                        margin-top: 40px;
                        background-color: #fff6ee;
                    }}
                    .footer p {{
                        margin: 8px 0;
                    }}
                    .page-number {{
                        text-align: right;
                        font-size: 12px;
                        color: #666666;
                        margin-top: 25px;
                        font-style: italic;
                    }}
                    @media print {{
                        body {{
                            -webkit-print-color-adjust: exact;
                            print-color-adjust: exact;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <img src="icons/app_icon.svg" class="logo" alt="Global Engineering Logo">
                    <div class="company-name">Global Engineering</div>
                </div>
                
                <div class="title">CASE REPORT</div>
                
                <table class="main-table">
                    {''.join(f'<tr><th>{label}</th><td>{value}</td></tr>' for label, value in fields_data if value)}
                </table>
                
                <div class="footer">
                    <p>Generated on {current_time}</p>
                    <p>© Global Engineering - All Rights Reserved</p>
                </div>
                
                <div class="page-number">Page 1</div>
            </body>
            </html>
            """
            
            doc.setHtml(html)
            
            file_name = f"Case_Report_{self.entry.get('File No.', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save PDF",
                file_name,
                "PDF Files (*.pdf)"
            )
            
            if file_path:
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                printer.setPageSize(QPrinter.A4)
                printer.setOrientation(QPrinter.Portrait)
                
                doc.print_(printer)
                QMessageBox.information(self, "Success", f"PDF saved successfully at:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")

# ======================== EditDialog Class ========================
class EditDialog(QDialog):
    def __init__(self, entry, icons_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Entry")
        self.entry = entry
        self.icons_path = icons_path
        
        # Define paths for user data
        self.user_data_folder = os.path.join(str(Path.home()), '.my_app_data')
        self.work_types_file = os.path.join(self.user_data_folder, 'work_types.json')
        self.work_done_file = os.path.join(self.user_data_folder, 'work_done.json')
        self.locations_file = os.path.join(self.user_data_folder, 'locations.json')
        
        # Initialize location fields
        self.state = None
        self.district = None
        self.taluka = None
        self.village = None
        
        # Initialize party location fields
        self.party_state = None
        self.party_district = None
        self.party_taluka = None
        self.party_village = None
        self.party_village_completer = None
        
        # Load data
        self.load_work_types()
        self.load_work_done()
        self.load_locations()
        
        self.init_ui()
        
        # Install event filter to handle Enter key press
        self.installEventFilter(self)

    def init_ui(self):
        self.setMinimumWidth(1200)
        self.setMinimumHeight(800)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title Label
        title_label = QLabel("Edit Entry")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #564234;
                background: transparent;
                padding: 5px 0;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #fff6ee;
            }
            QScrollBar:vertical {
                border: none;
                background: #fff6ee;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #ffcea1;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Create widget to hold the form
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(20)
        
        # Create horizontal layout for Basic and Location Information
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        basic_layout = QFormLayout()
        basic_layout.setSpacing(15)
        
        # File No.
        self.file_no = QLineEdit(self.entry.get("File No.", ""))
        self.file_no.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ffcea1;
            }
        """)
        basic_layout.addRow("File No.", self.file_no)
        
        # Customer Name
        self.customer_name = QLineEdit(self.entry.get("Customer Name", ""))
        self.customer_name.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ffcea1;
            }
        """)
        basic_layout.addRow("Customer Name", self.customer_name)
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        try:
            date_str = self.entry.get("Date", "")
            if date_str:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
        except:
            self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
                font-size: 14px;
            }
            QDateEdit:focus {
                border: 2px solid #ffcea1;
            }
        """)
        basic_layout.addRow("Date", self.date_edit)
        
        # Mobile Number
        self.mobile_number = QLineEdit(self.entry.get("Mobile Number", ""))
        self.mobile_number.setValidator(QIntValidator())
        self.mobile_number.setMaxLength(10)
        self.mobile_number.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ffcea1;
            }
        """)
        basic_layout.addRow("Mobile Number", self.mobile_number)
        
        basic_group.setLayout(basic_layout)
        info_layout.addWidget(basic_group)
        
        # Location Information Group
        location_group = QGroupBox("Location Information")
        location_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #fff6ee;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #564234;
            }
        """)
        location_layout = QFormLayout()
        location_layout.setSpacing(15)
        
        # State
        self.state = NoScrollComboBox()
        self.state.setFixedHeight(40)
        self.state.addItem("Select State")
        self.state.addItems(sorted(self.locations.keys()))
        self.state.currentIndexChanged.connect(self.update_districts)
        location_layout.addRow("State", self.state)
        
        # District
        self.district = NoScrollComboBox()
        self.district.setFixedHeight(40)
        self.district.addItem("Select District")
        self.district.currentIndexChanged.connect(self.update_talukas)
        location_layout.addRow("District", self.district)
        
        # Taluka
        self.taluka = NoScrollComboBox()
        self.taluka.setFixedHeight(40)
        self.taluka.addItem("Select Taluka")
        self.taluka.currentIndexChanged.connect(self.update_villages)
        location_layout.addRow("Taluka", self.taluka)
        
        # Village
        self.village = NoScrollComboBox()
        self.village.setFixedHeight(40)
        self.village.addItem("Select Village")
        self.village.setEditable(True)
        self.village.lineEdit().editingFinished.connect(self.fill_location_by_village)
        
        # Add completer for village search
        self.village_completer = QCompleter()
        self.village_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.village.setCompleter(self.village_completer)
        self.village.lineEdit().textChanged.connect(self.update_village_suggestions)
        
        location_layout.addRow("Village", self.village)
        
        # R.S.No./ Block No.
        self.rs_block = NoScrollComboBox()
        self.rs_block.setFixedHeight(40)
        self.rs_block.addItems(["R.S.No.", "Block No.", "City S.R.", "Gamtad"])
        location_layout.addRow("R.S.No./ Block No.", self.rs_block)
        
        # New No.
        self.new_no = QLineEdit()
        self.new_no.setFixedHeight(40)
        self.new_no.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ffcea1;
            }
        """)
        location_layout.addRow("New No.", self.new_no)
        
        # Old No.
        self.old_no = QLineEdit()
        self.old_no.setFixedHeight(40)
        self.old_no.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ffcea1;
            }
        """)
        location_layout.addRow("Old No.", self.old_no)
        
        location_group.setLayout(location_layout)
        info_layout.addWidget(location_group)
        
        # Add the horizontal layout to the form layout
        form_layout.addLayout(info_layout)
        
        # Work Information Group
        work_group = QGroupBox("Work Information")
        work_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #fff6ee;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #564234;
            }
        """)
        work_layout = QFormLayout()
        work_layout.setSpacing(15)
        
        # Work Types
        work_types_widget = QWidget()
        work_types_layout = QHBoxLayout(work_types_widget)
        work_types_layout.setSpacing(10)
        work_types_layout.setContentsMargins(5, 5, 5, 5)
        
        self.work_types_checkboxes = {}
        for work_type in self.work_types_list:
            checkbox = QCheckBox(work_type)
            checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 13px;
                    color: #564234;
                    padding: 5px;
                    background-color: #fffcfa;
                    border: 1px solid #ffcea1;
                    border-radius: 4px;
                }
                QCheckBox:hover {
                    background-color: #ffe5cc;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QCheckBox::indicator:unchecked {
                    border: 2px solid #ffcea1;
                    background-color: #fffcfa;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #ffcea1;
                    background-color: #ffcea1;
                    border-radius: 3px;
                }
            """)
            if work_type in self.entry.get("Work Types", []):
                checkbox.setChecked(True)
            self.work_types_checkboxes[work_type] = checkbox
            work_types_layout.addWidget(checkbox)
        
        work_types_scroll = QScrollArea()
        work_types_scroll.setWidget(work_types_widget)
        work_types_scroll.setWidgetResizable(True)
        work_types_scroll.setMinimumHeight(80)
        work_types_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        work_types_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
            }
            QScrollBar:vertical {
                border: none;
                background: #fffcfa;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #ffcea1;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #fffcfa;
                height: 5px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #ffcea1;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        work_layout.addRow("Work Types", work_types_scroll)
        
        # Work Done
        work_done_widget = QWidget()
        work_done_layout = QHBoxLayout(work_done_widget)
        work_done_layout.setSpacing(10)
        work_done_layout.setContentsMargins(5, 5, 5, 5)
        
        self.work_done_checkboxes = {}
        for work_done in self.work_done_list:
            checkbox = QCheckBox(work_done)
            checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 13px;
                    color: #564234;
                    padding: 5px;
                    background-color: #fffcfa;
                    border: 1px solid #ffcea1;
                    border-radius: 4px;
                }
                QCheckBox:hover {
                    background-color: #ffe5cc;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QCheckBox::indicator:unchecked {
                    border: 2px solid #ffcea1;
                    background-color: #fffcfa;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #ffcea1;
                    background-color: #ffcea1;
                    border-radius: 3px;
                }
            """)
            if work_done in self.entry.get("Work Done", []):
                checkbox.setChecked(True)
            self.work_done_checkboxes[work_done] = checkbox
            work_done_layout.addWidget(checkbox)
        
        work_done_scroll = QScrollArea()
        work_done_scroll.setWidget(work_done_widget)
        work_done_scroll.setWidgetResizable(True)
        work_done_scroll.setMinimumHeight(80)
        work_done_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        work_done_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
            }
            QScrollBar:vertical {
                border: none;
                background: #fffcfa;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #ffcea1;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #fffcfa;
                height: 5px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #ffcea1;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        work_layout.addRow("Work Done", work_done_scroll)
        
        # Final Amount
        self.final_amount = QLineEdit(self.entry.get("Final Amount", ""))
        self.final_amount.setFixedHeight(40)
        self.final_amount.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ffcea1;
            }
        """)
        work_layout.addRow("Final Amount", self.final_amount)
        
        # Remark
        self.remark = QTextEdit(self.entry.get("Remark", ""))
        self.remark.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
                font-size: 14px;
                min-height: 60px;
            }
            QTextEdit:focus {
                border: 2px solid #ffcea1;
            }
        """)
        work_layout.addRow("Remark", self.remark)
        
        work_group.setLayout(work_layout)
        form_layout.addWidget(work_group)
        
        # Party Address Group
        party_group = QGroupBox("Party Address")
        party_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #fff6ee;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #564234;
            }
        """)
        party_layout = QFormLayout()
        party_layout.setSpacing(15)

        # Party Address Location Fields
        # State
        self.party_state = NoScrollComboBox()
        self.party_state.setFixedHeight(40)
        self.party_state.addItem("Select State")
        self.party_state.addItems(sorted(self.locations.keys()))
        self.party_state.currentIndexChanged.connect(self.update_party_districts)
        party_layout.addRow("State", self.party_state)

        # District
        self.party_district = NoScrollComboBox()
        self.party_district.setFixedHeight(40)
        self.party_district.addItem("Select District")
        self.party_district.currentIndexChanged.connect(self.update_party_talukas)
        party_layout.addRow("District", self.party_district)

        # Taluka
        self.party_taluka = NoScrollComboBox()
        self.party_taluka.setFixedHeight(40)
        self.party_taluka.addItem("Select Taluka")
        self.party_taluka.currentIndexChanged.connect(self.update_party_villages)
        party_layout.addRow("Taluka", self.party_taluka)

        # Village
        self.party_village = NoScrollComboBox()
        self.party_village.setFixedHeight(40)
        self.party_village.addItem("Select Village")
        self.party_village.setEditable(True)
        self.party_village.lineEdit().editingFinished.connect(self.fill_party_location_by_village)

        # Add completer for village search
        self.party_village_completer = QCompleter()
        self.party_village_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.party_village.setCompleter(self.party_village_completer)
        self.party_village.lineEdit().textChanged.connect(self.update_party_village_suggestions)

        party_layout.addRow("Village", self.party_village)

        party_group.setLayout(party_layout)
        form_layout.addWidget(party_group)

        # Add the form widget to the scroll area
        scroll.setWidget(form_widget)
        
        # Add the scroll area to the main layout
        main_layout.addWidget(scroll)

        # Dialog buttons with styling
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_changes)
        buttons.rejected.connect(self.reject)
        
        # Style the buttons
        buttons.setStyleSheet("""
            QPushButton {
                padding: 10px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 100px;
                height: 35px;
            }
            QPushButton[text="Save"] {
                background-color: #2ecc71;
                color: white;
                border: none;
            }
            QPushButton[text="Save"]:hover {
                background-color: #27ae60;
            }
            QPushButton[text="Cancel"] {
                background-color: #e74c3c;
                color: white;
                border: none;
            }
            QPushButton[text="Cancel"]:hover {
                background-color: #c0392b;
            }
        """)
        
        main_layout.addWidget(buttons)
        
        self.setLayout(main_layout)
        
        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #fff6ee;
            }
        """)

        # Load existing data
        self.set_location_fields()
        self.set_party_address_fields()

    def set_location_fields(self):
        """Set location fields based on existing data"""
        # Set State
        state_value = self.entry.get("State", "")
        if state_value:
            index = self.state.findText(state_value, Qt.MatchFixedString)
            if index >= 0:
                self.state.setCurrentIndex(index)
                # Update districts based on the selected state
                self.update_districts(index)
            else:
                self.state.setCurrentIndex(0) # Reset if state not found

        # Set District
        district_value = self.entry.get("District", "")
        if district_value and self.state.currentIndex() > 0:
            index = self.district.findText(district_value, Qt.MatchFixedString)
            if index >= 0:
                self.district.setCurrentIndex(index)
                # Update talukas based on the selected district
                self.update_talukas(index)
            else:
                # If district not in the list, add it and select
                self.district.addItem(district_value)
                self.district.setCurrentText(district_value)
                self.update_talukas(self.district.currentIndex())

        # Set Taluka
        taluka_value = self.entry.get("Taluka", "")
        if taluka_value and self.district.currentIndex() > 0:
            index = self.taluka.findText(taluka_value, Qt.MatchFixedString)
            if index >= 0:
                self.taluka.setCurrentIndex(index)
                # Update villages based on the selected taluka
                self.update_villages(index)
            else:
                self.taluka.addItem(taluka_value)
                self.taluka.setCurrentText(taluka_value)
                self.update_villages(self.taluka.currentIndex())

        # Set Village
        village_value = self.entry.get("Village", "")
        if village_value and self.taluka.currentIndex() > 0:
            index = self.village.findText(village_value, Qt.MatchFixedString)
            if index >= 0:
                self.village.setCurrentIndex(index)
            else:
                # Village might be custom, add and select
                self.village.addItem(village_value)
                self.village.setCurrentText(village_value)

        # Set R.S.No./ Block No.
        rs_block_value = self.entry.get("R.S.No./ Block No.", "")
        if rs_block_value:
            index = self.rs_block.findText(rs_block_value, Qt.MatchFixedString)
            if index >= 0:
                self.rs_block.setCurrentIndex(index)

        # Set New No.
        new_no_value = self.entry.get("New No.", "")
        if new_no_value:
            self.new_no.setText(new_no_value)

        # Set Old No.
        old_no_value = self.entry.get("Old No.", "")
        if old_no_value:
            self.old_no.setText(old_no_value)

    def set_party_address_fields(self):
        """Parse the existing Party Address and set the dropdowns"""
        full_address = self.entry.get("Party Address", "")
        
        # Ensure full_address is a string before trying to split it
        if not isinstance(full_address, str):
            # If it's not a string (e.g., an old dict format), treat as empty
            print(f"Warning: Party Address for entry {self.entry.get('File No.', '')} is not a string: {full_address}. Treating as empty.")
            full_address = ""
            
        if not full_address:
            # Clear fields if address is empty
            self.party_state.setCurrentIndex(0)
            self.party_district.clear()
            self.party_district.addItem("Select District")
            self.party_taluka.clear()
            self.party_taluka.addItem("Select Taluka")
            self.party_village.clear()
            self.party_village.addItem("Select Village")
            return

        lines = full_address.split('\n')
        parsed_locations = {}

        for line in lines:
            if line.startswith("State:"):
                parsed_locations["State"] = line.split(":", 1)[1].strip()
            elif line.startswith("District:"):
                parsed_locations["District"] = line.split(":", 1)[1].strip()
            elif line.startswith("Taluka:"):
                parsed_locations["Taluka"] = line.split(":", 1)[1].strip()
            elif line.startswith("Village:"):
                parsed_locations["Village"] = line.split(":", 1)[1].strip()

        # Set State
        state_value = parsed_locations.get("State", "")
        if state_value:
            index = self.party_state.findText(state_value, Qt.MatchFixedString)
            if index >= 0:
                self.party_state.setCurrentIndex(index)
                # Update districts based on the selected state
                self.update_party_districts(index)
            else:
                self.party_state.setCurrentIndex(0) # Reset if state not found

        # Set District
        district_value = parsed_locations.get("District", "")
        if district_value and self.party_state.currentIndex() > 0:
            index = self.party_district.findText(district_value, Qt.MatchFixedString)
            if index >= 0:
                self.party_district.setCurrentIndex(index)
                # Update talukas based on the selected district
                self.update_party_talukas(index)
            else:
                # If district not in the list, add it and select
                self.party_district.addItem(district_value)
                self.party_district.setCurrentText(district_value)
                self.update_party_talukas(self.party_district.currentIndex())

        # Set Taluka
        taluka_value = parsed_locations.get("Taluka", "")
        if taluka_value and self.party_district.currentIndex() > 0:
            index = self.party_taluka.findText(taluka_value, Qt.MatchFixedString)
            if index >= 0:
                self.party_taluka.setCurrentIndex(index)
                # Update villages based on the selected taluka
                self.update_party_villages(index)
            else:
                self.party_taluka.addItem(taluka_value)
                self.party_taluka.setCurrentText(taluka_value)
                self.update_party_villages(self.party_taluka.currentIndex())

        # Set Village
        village_value = parsed_locations.get("Village", "")
        if village_value and self.party_taluka.currentIndex() > 0:
            index = self.party_village.findText(village_value, Qt.MatchFixedString)
            if index >= 0:
                self.party_village.setCurrentIndex(index)
            else:
                # Village might be custom, add and select
                self.party_village.addItem(village_value)
                self.party_village.setCurrentText(village_value)

    def load_work_types(self):
        """Load work types from JSON file"""
        try:
            if os.path.exists(self.work_types_file):
                with open(self.work_types_file, 'r', encoding='utf-8') as f:
                    self.work_types_list = json.load(f)
            else:
                self.work_types_list = []
        except Exception as e:
            print(f"Error loading work types: {e}")
            self.work_types_list = []

    def load_work_done(self):
        """Load work done from JSON file"""
        try:
            if os.path.exists(self.work_done_file):
                with open(self.work_done_file, 'r', encoding='utf-8') as f:
                    self.work_done_list = json.load(f)
            else:
                self.work_done_list = []
        except Exception as e:
            print(f"Error loading work done: {e}")
            self.work_done_list = []

    def load_locations(self):
        """Load locations from JSON file"""
        try:
            if os.path.exists(self.locations_file):
                with open(self.locations_file, 'r', encoding='utf-8') as f:
                    self.locations = json.load(f)
            else:
                self.locations = {}
        except Exception as e:
            print(f"Error loading locations: {e}")
            self.locations = {}

    def update_districts(self, index):
        state = self.state.currentText()
        if not hasattr(self, 'district') or self.district is None:
            return
            
        self.district.clear()
        self.district.addItem("Select District")
        
        if not hasattr(self, 'taluka') or self.taluka is None:
            return
            
        self.taluka.clear()
        self.taluka.addItem("Select Taluka")
        
        if not hasattr(self, 'village') or self.village is None:
            return
            
        self.village.clear()
        self.village.addItem("Select Village")
        
        if state in self.locations:
            districts = sorted(self.locations[state].keys())
            self.district.addItems(districts)
            
            # Try to set the previous value
            district_value = self.entry.get("District", "")
            index = self.district.findText(district_value)
            if index >= 0:
                self.district.setCurrentIndex(index)

    def update_talukas(self, index):
        state = self.state.currentText()
        district = self.district.currentText()
        
        if not hasattr(self, 'taluka') or self.taluka is None:
            return
            
        self.taluka.clear()
        self.taluka.addItem("Select Taluka")
        
        if not hasattr(self, 'village') or self.village is None:
            return
            
        self.village.clear()
        self.village.addItem("Select Village")
        
        if state in self.locations and district in self.locations[state]:
            talukas = sorted(self.locations[state][district].keys())
            self.taluka.addItems(talukas)
            
            # Try to set the previous value
            taluka_value = self.entry.get("Taluka", "")
            index = self.taluka.findText(taluka_value)
            if index >= 0:
                self.taluka.setCurrentIndex(index)

    def update_villages(self, index):
        state = self.state.currentText()
        district = self.district.currentText()
        taluka = self.taluka.currentText()
        
        if not hasattr(self, 'village') or self.village is None:
            return
            
        self.village.clear()
        self.village.addItem("Select Village")
        
        if state in self.locations and district in self.locations[state] and taluka in self.locations[state][district]:
            villages = sorted(self.locations[state][district][taluka])
            self.village.addItems(villages)
            
            # Try to set the previous value
            village_value = self.entry.get("Village", "")
            index = self.village.findText(village_value)
            if index >= 0:
                self.village.setCurrentIndex(index)
            else:
                self.village.addItem(village_value)
                self.village.setCurrentText(village_value)

    def fill_location_by_village(self):
        """Fill location fields automatically based on village name"""
        village_name = self.village.currentText().strip()
        if not village_name or village_name == "Select Village":
            return

        # Search locations_data for village_name case-insensitively
        for state, districts in self.locations.items():
            for district, talukas in districts.items():
                for taluka, villages in talukas.items():
                    for v in villages:
                        if v.lower() == village_name.lower():
                            # Set state
                            idx_state = self.state.findText(state)
                            if idx_state != -1:
                                self.state.setCurrentIndex(idx_state)
                                self.update_districts(idx_state)
                            # Set district
                            idx_district = self.district.findText(district)
                            if idx_district != -1:
                                self.district.setCurrentIndex(idx_district)
                                self.update_talukas(idx_district)
                            # Set taluka
                            idx_taluka = self.taluka.findText(taluka)
                            if idx_taluka != -1:
                                self.taluka.setCurrentIndex(idx_taluka)
                                self.update_villages(idx_taluka)
                            # Set village
                            idx_village = self.village.findText(village_name)
                            if idx_village == -1:
                                self.village.addItem(village_name)
                                idx_village = self.village.findText(village_name)
                            self.village.setCurrentIndex(idx_village)
                            return

    def update_village_suggestions(self, text):
        """Update village suggestions based on input text"""
        if not text:
            self.village_completer.setModel(None)
            return

        suggestions = []
        for state in self.locations:
            for district in self.locations[state]:
                for taluka in self.locations[state][district]:
                    for village in self.locations[state][district][taluka]:
                        if text.lower() in village.lower():
                            suggestions.append(village)

        # Remove duplicates and sort
        unique_suggestions = sorted(list(set(suggestions)))
        model = QStringListModel(unique_suggestions)
        self.village_completer.setModel(model)

    def update_party_districts(self, index):
        state = self.party_state.currentText()
        
        if not hasattr(self, 'party_district') or self.party_district is None:
            return
            
        self.party_district.clear()
        self.party_district.addItem("Select District")
        
        if not hasattr(self, 'party_taluka') or self.party_taluka is None:
            return
            
        self.party_taluka.clear()
        self.party_taluka.addItem("Select Taluka")
        
        if not hasattr(self, 'party_village') or self.party_village is None:
            return
            
        self.party_village.clear()
        self.party_village.addItem("Select Village")
        
        if state in self.locations:
            districts = sorted(self.locations[state].keys())
            self.party_district.addItems(districts)

    def update_party_talukas(self, index):
        state = self.party_state.currentText()
        district = self.party_district.currentText()
        
        if not hasattr(self, 'party_taluka') or self.party_taluka is None:
            return
            
        self.party_taluka.clear()
        self.party_taluka.addItem("Select Taluka")
        
        if not hasattr(self, 'party_village') or self.party_village is None:
            return
            
        self.party_village.clear()
        self.party_village.addItem("Select Village")
        
        if state in self.locations and district in self.locations[state]:
            talukas = sorted(self.locations[state][district].keys())
            self.party_taluka.addItems(talukas)

    def update_party_villages(self, index):
        state = self.party_state.currentText()
        district = self.party_district.currentText()
        taluka = self.party_taluka.currentText()
        
        if not hasattr(self, 'party_village') or self.party_village is None:
            return
            
        self.party_village.clear()
        self.party_village.addItem("Select Village")
        
        if state in self.locations and district in self.locations[state] and taluka in self.locations[state][district]:
            villages = sorted(self.locations[state][district][taluka])
            self.party_village.addItems(villages)

    def fill_party_location_by_village(self):
        """Fill party location fields automatically based on village name"""
        village_name = self.party_village.currentText().strip()
        if not village_name or village_name == "Select Village":
            return

        # Search locations_data for village_name case-insensitively
        for state, districts in self.locations.items():
            for district, talukas in districts.items():
                for taluka, villages in talukas.items():
                    for v in villages:
                        if v.lower() == village_name.lower():
                            # Set state
                            idx_state = self.party_state.findText(state)
                            if idx_state != -1:
                                self.party_state.setCurrentIndex(idx_state)
                                self.update_party_districts(idx_state)
                            # Set district
                            idx_district = self.party_district.findText(district)
                            if idx_district != -1:
                                self.party_district.setCurrentIndex(idx_district)
                                self.update_party_talukas(idx_district)
                            # Set taluka
                            idx_taluka = self.party_taluka.findText(taluka)
                            if idx_taluka != -1:
                                self.party_taluka.setCurrentIndex(idx_taluka)
                                self.update_party_villages(idx_taluka)
                            # Set village
                            idx_village = self.party_village.findText(village_name)
                            if idx_village == -1:
                                self.party_village.addItem(village_name)
                                idx_village = self.party_village.findText(village_name)
                            self.party_village.setCurrentIndex(idx_village)
                            return

    def update_party_village_suggestions(self, text):
        """Update party village suggestions based on input text"""
        if not text:
            self.party_village_completer.setModel(None)
            return

        suggestions = []
        for state in self.locations:
            for district in self.locations[state]:
                for taluka in self.locations[state][district]:
                    for village in self.locations[state][district][taluka]:
                        if text.lower() in village.lower():
                            suggestions.append(village)

        # Remove duplicates and sort
        unique_suggestions = sorted(list(set(suggestions)))
        model = QStringListModel(unique_suggestions)
        self.party_village_completer.setModel(model)

    def save_changes(self):
        """Save changes to the entry"""
        # Validate the date format
        date_str = self.date_edit.date().toString("dd/MM/yyyy")

        # Validate village name exists in locations.json
        village_name = self.village.currentText().strip()
        if village_name and village_name != "Select Village":
            village_found = False
            for state in self.locations:
                for district in self.locations[state]:
                    for taluka in self.locations[state][district]:
                        if village_name in self.locations[state][district][taluka]:
                            village_found = True
                            break
                    if village_found:
                        break
                if village_found:
                    break
            
            if not village_found:
                QMessageBox.warning(self, "Invalid Village", 
                    f"Village '{village_name}' does not exist in the database. Please select a valid village.")
                return

        # Validate party village name exists in locations.json
        party_village_name = self.party_village.currentText().strip()
        if party_village_name and party_village_name != "Select Village":
            party_village_found = False
            for state in self.locations:
                for district in self.locations[state]:
                    for taluka in self.locations[state][district]:
                        if party_village_name in self.locations[state][district][taluka]:
                            party_village_found = True
                            break
                    if party_village_found:
                        break
                if party_village_found:
                    break
            
            if not party_village_found:
                QMessageBox.warning(self, "Invalid Party Village", 
                    f"Party Village '{party_village_name}' does not exist in the database. Please select a valid village.")
                return

        # Gather updated data
        self.entry["File No."] = self.file_no.text().strip()
        self.entry["Customer Name"] = self.customer_name.text().strip()
        self.entry["Date"] = date_str
        self.entry["Mobile Number"] = self.mobile_number.text().strip()
        self.entry["Remark"] = self.remark.toPlainText().strip()
        self.entry["State"] = self.state.currentText()
        self.entry["District"] = self.district.currentText()
        self.entry["R.S.No./ Block No."] = self.rs_block.currentText()
        self.entry["New No."] = self.new_no.text().strip()
        self.entry["Old No."] = self.old_no.text().strip()
        self.entry["Taluka"] = self.taluka.currentText()
        self.entry["Village"] = self.village.currentText()
        self.entry["Final Amount"] = self.final_amount.text().strip()
        
        # Work Types and Work Done from checkboxes
        self.entry["Work Types"] = [wt for wt, cb in self.work_types_checkboxes.items() if cb.isChecked()]
        self.entry["Work Done"] = [wd for wd, cb in self.work_done_checkboxes.items() if cb.isChecked()]
        
        # Party Address with location (removed address text field)
        party_address_lines = []
        if self.party_state.currentText() != "Select State":
            party_address_lines.append(f"State: {self.party_state.currentText()}")
        if self.party_district.currentText() != "Select District":
            party_address_lines.append(f"District: {self.party_district.currentText()}")
        if self.party_taluka.currentText() != "Select Taluka":
            party_address_lines.append(f"Taluka: {self.party_taluka.currentText()}")
        if self.party_village.currentText() != "Select Village":
            party_address_lines.append(f"Village: {self.party_village.currentText()}")
        
        self.entry["Party Address"] = "\n".join(party_address_lines)

        # Log activity from parent ReportModule
        parent = self.parent()
        if isinstance(parent, ReportModule):
            activity_details = f"Modified report entry details for {self.entry.get('Customer Name', 'Unknown')}"
            parent.activity_tracker.log_activity("Report", "Modified", activity_details)
            
            # Refresh dashboard if exists
            main_window = parent.window()
            if hasattr(main_window, 'dashboard'):
                main_window.dashboard.load_activities()

        self.accept()

    def eventFilter(self, source, event):
        """Handle Enter key press to prevent accidental saving."""
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Return or key == Qt.Key_Enter:
                # Check if the source is a QTextEdit, QLineEdit, or the line edit of a QComboBox
                if isinstance(source, QTextEdit) or \
                   isinstance(source, QLineEdit) or \
                   (isinstance(source, QComboBox) and source.isEditable() and source.lineEdit() == QApplication.focusWidget()):
                   
                    # Special handling for QTextEdit to allow new lines with Shift+Enter
                    if isinstance(source, QTextEdit) and (event.modifiers() & Qt.ShiftModifier):
                        return super().eventFilter(source, event) # Allow Shift+Enter
                    
                    # Ignore Enter key press in input fields to prevent dialog submission
                    return True 
        
        # Process other events normally
        return super().eventFilter(source, event)

# ======================== ReportModule Class ========================
class ReportModule(QWidget):
    def __init__(self):
        super().__init__()
        self.activity_tracker = ActivityTracker()

        # Window settings
        self.setWindowTitle("Case Reports")
        self.setGeometry(150, 150, 1200, 600)

        # Define the icons path
        self.icons_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')

        # Apply the overall stylesheet
        down_arrow_style = """image: url("icons/down_arrow.svg"); width: 16px; height: 16px;"""

        # Set the stylesheet with updated QComboBox dimensions and arrow
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #fff6ee;
            }}
            QLabel {{
                color: #564234;
                font-size: 14px;
            }}
            QLineEdit, QComboBox, QPushButton {{
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                padding: 10px 10px;
                font-size: 14px;
                height: 30px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 2px solid #ffcea1;
            }}
            QPushButton {{
                font-size: 14px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #ff8c00;
            }}
            QPushButton#viewBtn, QPushButton#editBtn, QPushButton#deleteBtn {{
                padding: 5px 10px;
                font-size: 12px;
                border: none;
            }}
            QPushButton#refreshBtn {{
                background-color: #FFA500;
                color: white;
            }}
            QPushButton#refreshBtn:hover {{
                background-color: #FF8C00;
            }}
            QComboBox {{
                width: 100px;
                height: 30px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 50px;
                height: 30px;
            }}
            QComboBox::down-arrow {{
                {down_arrow_style}
            }}
            QComboBox QAbstractItemView {{
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
            }}

        """)

        # Define paths for user data
        self.user_data_folder = os.path.join(str(Path.home()), '.my_app_data')
        self.data_file = os.path.join(self.user_data_folder, 'data.json')
        
        # Create user data folder if it doesn't exist
        os.makedirs(self.user_data_folder, exist_ok=True)
        
        # If running from PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # If data.json doesn't exist in user folder, try to download from Drive
            if not os.path.exists(self.data_file):
                drive_sync.download_file('data.json', self.data_file)

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header Layout with Title and Refresh Button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        # Header Label
        header_label = QLabel("All Cases")
        header_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #d17a24;")
        header_layout.addWidget(header_label, alignment=Qt.AlignLeft)

        # Spacer to push the refresh button to the right
        header_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Refresh Button
        refresh_btn = QPushButton()
        refresh_icon_path = os.path.join(self.icons_folder, 'refresh.svg')
        if os.path.exists(refresh_icon_path):
            refresh_btn.setIcon(QIcon(refresh_icon_path))
        else:
            refresh_btn.setText("Refresh")
        refresh_btn.setToolTip("Refresh Data")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)

        main_layout.addLayout(header_layout)

        # Search and Filter Layout
        search_filter_layout = QHBoxLayout()
        search_filter_layout.setSpacing(20)

        # Search Box
        search_label = QLabel("Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Enter keyword to search...")
        self.search_box.textChanged.connect(self.apply_filters)

        # Add completer for search
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_box.setCompleter(self.completer)
        self.search_box.textChanged.connect(self.update_completer)

        search_filter_layout.addWidget(search_label)
        search_filter_layout.addWidget(self.search_box)

        # Date Filters: Day, Month, Year
        self.date_filters = {}
        # For user-friendliness, set them by default to "All Day", "All Month", "All Years"
        day_combo = QComboBox()
        day_combo.addItem("All Day")
        day_combo.addItems([str(day).zfill(2) for day in range(1, 32)])
        day_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url("icons/dropdown_arrow.svg");
                width: 10px;
                height: 10px;
            }
        """)
        day_combo.setToolTip("Filter by Day")
        day_combo.currentIndexChanged.connect(self.apply_filters)
        self.date_filters["Day"] = day_combo
        search_filter_layout.addWidget(day_combo)

        month_combo = QComboBox()
        month_combo.addItem("All Month")
        month_combo.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        month_combo.setToolTip("Filter by Month")
        month_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url("icons/dropdown_arrow.svg");
                width: 10px;
                height: 10px;
            }
        """)
        month_combo.currentIndexChanged.connect(self.apply_filters)
        self.date_filters["Month"] = month_combo
        search_filter_layout.addWidget(month_combo)

        year_combo = QComboBox()
        year_combo.addItem("All Years")
        # Assuming entries are within 2000 to current year + 5
        current_year = datetime.now().year
        years = [str(year) for year in range(2000, current_year + 6)]
        year_combo.addItems(years)
        year_combo.setToolTip("Filter by Year")
        year_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url("icons/dropdown_arrow.svg");
                width: 10px;
                height: 10px;
            }
        """)
        year_combo.currentIndexChanged.connect(self.apply_filters)
        self.date_filters["Year"] = year_combo
        search_filter_layout.addWidget(year_combo)

        # Add Spacer to push filters to the left
        search_filter_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        main_layout.addLayout(search_filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(15)
        self.table.setHorizontalHeaderLabels([
            "SN", "File No.", "Customer Name", "Mobile No.", "Date",
            "R.S.No./ Block No.", "New No.", "Old No.", "Plot No.", "District",
            "Taluka", "Village", "Work Types", "Work Done", "Action"
        ])
        
        # Enable word wrap for all items
        self.table.setWordWrap(True)
        
        # Set column widths
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # SN
        self.table.setColumnWidth(0, 40)
        
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)  # File No.
        self.table.setColumnWidth(1, 80)
        
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Customer Name
        
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)  # Mobile No.
        self.table.setColumnWidth(3, 110)
        
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)  # Date
        self.table.setColumnWidth(4, 100)
        
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)  # R.S.No./ Block No.
        self.table.setColumnWidth(5, 120)
        
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)  # New No.
        self.table.setColumnWidth(6, 80)
        
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)  # Old No.
        self.table.setColumnWidth(7, 80)
        
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)  # Plot No.
        self.table.setColumnWidth(8, 100)
        
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)  # District
        self.table.setColumnWidth(9, 100)
        
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)  # Taluka
        self.table.setColumnWidth(10, 100)
        
        self.table.horizontalHeader().setSectionResizeMode(11, QHeaderView.Fixed)  # Village
        self.table.setColumnWidth(11, 100)
        
        self.table.horizontalHeader().setSectionResizeMode(12, QHeaderView.Fixed)  # Work Types
        self.table.setColumnWidth(12, 140)
        
        self.table.horizontalHeader().setSectionResizeMode(13, QHeaderView.Fixed)  # Work Done
        self.table.setColumnWidth(13, 100)
        
        self.table.horizontalHeader().setSectionResizeMode(14, QHeaderView.Fixed)  # Action
        self.table.setColumnWidth(14, 100)
        
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #ffe9d7;
                color: #d17a24;
                padding: 5px;
                border: none solid #ffcea1;
                border-bottom: 2px solid #ffcea1;
                font-size: 12px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
                font-size: 12px;
                border: none solid #ffcea1;
                border-bottom: 0.5px solid #ffe9d7;
                color: #564234;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #ffcea1;
                color: #ffffff;
            }
            QScrollBar:vertical {
                border: none;
                background: #fffcfa;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #ffcea1;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #fffcfa;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #ffcea1;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        # Set minimum row height and enable auto-resize
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        # Load data and populate filters
        self.load_data()


    def load_data(self):
        """Load data from data.json and populate the table."""
        try:
            # Agar file nahi hai to empty file create karo
            if not os.path.exists(self.data_file):
                # Create empty data structure
                empty_data = []
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(empty_data, f, indent=4)
                self.data = empty_data
            else:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Creating new data file as no existing data found.")
            self.data = []
        
        self.display_data(self.data)

    def apply_filters(self):
        """Filter data based on search box and selected date filters."""
        if not hasattr(self, 'data'):
            return

        keyword = self.search_box.text().lower()

        selected_day = self.date_filters["Day"].currentText()
        selected_month = self.date_filters["Month"].currentText()
        selected_year = self.date_filters["Year"].currentText()

        filtered_data = []
        for entry in self.data:
            # Keyword search filter (checks all values in the entry)
            if keyword:
                all_values_str = " ".join(str(v).lower() for v in entry.values())
                if keyword not in all_values_str:
                    continue

            # Date-related filters
            date_str = entry.get("Date", "")
            try:
                entry_date = datetime.strptime(date_str, "%d/%m/%Y")
            except ValueError:
                entry_date = None

            # Day filter
            if entry_date and selected_day != "All Day":
                if entry_date.strftime("%d") != selected_day:
                    continue
            # If entry has no valid date but the user wants a specific day, skip it
            elif not entry_date and selected_day != "All Day":
                continue

            # Month filter
            if entry_date and selected_month != "All Month":
                if entry_date.strftime("%B") != selected_month:
                    continue
            elif not entry_date and selected_month != "All Month":
                continue

            # Year filter
            if entry_date and selected_year != "All Years":
                if entry_date.strftime("%Y") != selected_year:
                    continue
            elif not entry_date and selected_year != "All Years":
                continue

            filtered_data.append(entry)

        self.display_data(filtered_data)

    def refresh_data(self):
        """Refresh data from GitHub"""
        try:
            # Try to download latest data from GitHub
            if github_sync.download_file('data.json', self.data_file):
                QMessageBox.information(self, "Success", "Data successfully synced")
            else:
                QMessageBox.warning(self, "Warning", "Could not sync from GitHub. Using local data.")
            
            # Reload data from file
            self.load_data()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error refreshing data: {str(e)}")

    def view_entry(self, file_no):
        """Display the details of the selected entry in a user-friendly dialog."""
        entry = next((item for item in self.data if item.get("File No.", "") == file_no), None)
        if not entry:
            QMessageBox.warning(self, "Not Found", "The selected entry was not found.")
            return

        dialog = ViewDialog(entry, self.icons_folder, self)
        dialog.exec_()

    def edit_entry(self, file_no):
        """Edit an existing entry"""
        try:
            entry = next((e for e in self.data if e["File No."] == file_no), None)
            if entry:
                dialog = EditDialog(entry, self.icons_folder, self)
                if dialog.exec_() == QDialog.Accepted:
                    # Update the entry
                    for i, e in enumerate(self.data):
                        if e["File No."] == file_no:
                            self.data[i] = dialog.entry
                            break
                    
                    # Save changes
                    self.save_data()
                    
                    # Refresh display
                    self.display_data(self.data)
                    
                    # Log activity
                    activity_details = f"Modified report entry for File No. {file_no} - {entry.get('Customer Name', 'Unknown')}"
                    self.activity_tracker.log_activity("Report", "Modified", activity_details)
                    
                    # Refresh dashboard if exists
                    main_window = self.window()
                    if hasattr(main_window, 'dashboard'):
                        main_window.dashboard.load_activities()
                    
                    return True
            return False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit entry: {str(e)}")
            return False

    def delete_entry(self, file_no):
        """Delete an existing entry"""
        try:
            entry = next((e for e in self.data if e["File No."] == file_no), None)
            if entry:
                reply = QMessageBox.question(
                    self, "Confirm Deletion",
                    f"Are you sure you want to delete the entry for File No. {file_no}?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Remove the entry
                    self.data = [e for e in self.data if e["File No."] != file_no]
                    
                    # Save changes
                    self.save_data()
                    
                    # Refresh display
                    self.display_data(self.data)
                    
                    # Log activity
                    activity_details = f"Deleted report entry for File No. {file_no} - {entry.get('Customer Name', 'Unknown')}"
                    self.activity_tracker.log_activity("Report", "Deleted", activity_details)
                    
                    # Refresh dashboard if exists
                    main_window = self.window()
                    if hasattr(main_window, 'dashboard'):
                        main_window.dashboard.load_activities()
                    
                    return True
            return False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete entry: {str(e)}")
            return False

    def update_completer(self, text):
        """Update completer suggestions based on current text"""
        if not text:
            self.completer.setModel(None)
            return

        suggestions = []
        for entry in self.data:
            # Search in all relevant fields
            fields = [
                entry.get("File No.", ""),
                entry.get("Customer Name", ""),
                entry.get("Mobile Number", ""),
                entry.get("Village", ""),
                entry.get("District", ""),
                entry.get("Taluka", ""),
                ", ".join(entry.get("Work Types", []))
            ]
            
            for field in fields:
                if text.lower() in str(field).lower():
                    suggestions.append(str(field))

        # Remove duplicates and sort
        unique_suggestions = sorted(list(set(suggestions)))
        
        # Update completer model
        model = QStringListModel(unique_suggestions)
        self.completer.setModel(model)

    def save_data(self):
        """Save data to file and sync with Google Drive"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            
            # Sync with GitHub
            github_sync.sync_file(self.data_file)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {str(e)}")
            return False

    def display_data(self, data):
        """Display data in the table."""
        self.table.setRowCount(0)  # Clear existing data

        for index, entry in enumerate(data, start=1):
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            # SN. Column
            sn_item = QTableWidgetItem(str(index))
            sn_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 0, sn_item)

            # Other Columns
            file_no_item = QTableWidgetItem(entry.get("File No.", ""))
            file_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 1, file_no_item)

            customer_name_item = QTableWidgetItem(entry.get("Customer Name", ""))
            customer_name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 2, customer_name_item)

            date_item = QTableWidgetItem(entry.get("Date", ""))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 4, date_item)

            mobile_number_item = QTableWidgetItem(entry.get("Mobile Number", ""))
            mobile_number_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 3, mobile_number_item)

            district_item = QTableWidgetItem(entry.get("District", ""))
            district_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 9, district_item)

            rs_block_item = QTableWidgetItem(entry.get("R.S.No./ Block No.", ""))
            rs_block_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 5, rs_block_item)

            new_no_item = QTableWidgetItem(entry.get("New No.", ""))
            new_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 6, new_no_item)

            old_no_item = QTableWidgetItem(entry.get("Old No.", ""))
            old_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 7, old_no_item)

            plot_no_item = QTableWidgetItem(entry.get("Plot No.", ""))
            plot_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 8, plot_no_item)

            taluka_item = QTableWidgetItem(entry.get("Taluka", ""))
            taluka_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 10, taluka_item)

            village_item = QTableWidgetItem(entry.get("Village", ""))
            village_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 11, village_item)

            work_types_item = QTableWidgetItem(", ".join(entry.get("Work Types", [])))
            work_types_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 12, work_types_item)

            work_done_item = QTableWidgetItem(", ".join(entry.get("Work Done", [])))
            work_done_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 13, work_done_item)

            # Create Actions (View, Edit, Delete) buttons with SVG icons
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(5)

            # View Button
            view_btn = QPushButton()
            view_icon_path = os.path.join(self.icons_folder, 'view.svg')
            if os.path.exists(view_icon_path):
                view_btn.setIcon(QIcon(view_icon_path))
            else:
                view_btn.setText("View")
            view_btn.setToolTip("View Entry")
            view_btn.setObjectName("viewBtn")
            view_btn.setStyleSheet("""
                QPushButton#viewBtn {
                    background-color: #fff6ee;
                    color: white;
                }
                QPushButton#viewBtn:hover {
                    background-color: rgb(201, 253, 204);
                }
            """)
            view_btn.clicked.connect(partial(self.view_entry, entry.get("File No.", "")))

            # Edit Button
            edit_btn = QPushButton()
            edit_icon_path = os.path.join(self.icons_folder, 'edit.svg')
            if os.path.exists(edit_icon_path):
                edit_btn.setIcon(QIcon(edit_icon_path))
            else:
                edit_btn.setText("Edit")
            edit_btn.setToolTip("Edit Entry")
            edit_btn.setObjectName("editBtn")
            edit_btn.setStyleSheet("""
                QPushButton#editBtn {
                    background-color: #fff6ee;
                    color: white;
                }
                QPushButton#editBtn:hover {
                    background-color: rgb(195, 228, 255);
                }
            """)
            edit_btn.clicked.connect(partial(self.edit_entry, entry.get("File No.", "")))

            # Delete Button
            delete_btn = QPushButton()
            delete_icon_path = os.path.join(self.icons_folder, 'delete.svg')
            if os.path.exists(delete_icon_path):
                delete_btn.setIcon(QIcon(delete_icon_path))
            else:
                delete_btn.setText("Delete")
            delete_btn.setToolTip("Delete Entry")
            delete_btn.setObjectName("deleteBtn")
            delete_btn.setStyleSheet("""
                QPushButton#deleteBtn {
                    background-color: #fff6ee;
                    color: white;
                }
                QPushButton#deleteBtn:hover {
                    background-color: rgb(255, 199, 195);
                }
            """)
            delete_btn.clicked.connect(partial(self.delete_entry, entry.get("File No.", "")))

            # Add buttons to layout
            action_layout.addWidget(view_btn)
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_widget.setLayout(action_layout)

            self.table.setCellWidget(row_position, 14, action_widget)  # Actions column

# ======================== Main Application ========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReportModule()
    window.show()
    sys.exit(app.exec_())
