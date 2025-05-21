from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpacerItem, QSizePolicy, QMessageBox, QFormLayout,
    QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QFont
from github_sync import github_sync
import json

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

class ManageLocationsModule(QDialog):
    def __init__(self, locations_data, locations_file, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Locations")
        self.locations_data = locations_data
        self.locations_file = locations_file
        self.parent = parent  # Store parent reference
        self.setGeometry(300, 300, 500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Create editable combo boxes
        self.state_input = CustomComboBox()
        self.state_input.setEditable(True)
        self.state_input.addItems(sorted(self.locations_data.keys()))
        self.state_input.setPlaceholderText("Enter State Name")
        self.state_input.currentTextChanged.connect(self.update_districts)
        
        self.district_input = CustomComboBox()
        self.district_input.setEditable(True)
        self.district_input.setPlaceholderText("Enter District Name")
        self.district_input.currentTextChanged.connect(self.update_talukas)
        
        self.taluka_input = CustomComboBox()
        self.taluka_input.setEditable(True)
        self.taluka_input.setPlaceholderText("Enter Taluka Name")
        
        self.village_input = QLineEdit()
        self.village_input.setPlaceholderText("Enter Village Name")

        form_layout.addRow(QLabel("State:"), self.state_input)
        form_layout.addRow(QLabel("District:"), self.district_input)
        form_layout.addRow(QLabel("Taluka:"), self.taluka_input)
        form_layout.addRow(QLabel("Village:"), self.village_input)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Location")
        add_button.clicked.connect(self.add_location)
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        button_layout.addWidget(add_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def update_districts(self, state):
        self.district_input.clear()
        if state in self.locations_data:
            self.district_input.addItems(sorted(self.locations_data[state].keys()))

    def update_talukas(self, district):
        self.taluka_input.clear()
        state = self.state_input.currentText()
        if state in self.locations_data and district in self.locations_data[state]:
            self.taluka_input.addItems(sorted(self.locations_data[state][district].keys()))

    def add_location(self):
        state_input = self.state_input.currentText().strip()
        district_input = self.district_input.currentText().strip()
        taluka_input = self.taluka_input.currentText().strip()
        village_input = self.village_input.text().strip()

        if not state_input or not district_input or not taluka_input or not village_input:
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        def match_key(mapping, key):
            for k in mapping:
                if k.lower() == key.lower():
                    return k
            return None

        # State level case-insensitive check
        state_key = match_key(self.locations_data, state_input)
        if state_key is None:
            state_key = state_input
            self.locations_data[state_key] = {}
        district_dict = self.locations_data[state_key]

        # District level case-insensitive check
        district_key = match_key(district_dict, district_input)
        if district_key is None:
            district_key = district_input
            district_dict[district_key] = {}
        taluka_dict = district_dict[district_key]

        # Taluka level case-insensitive check
        taluka_key = match_key(taluka_dict, taluka_input)
        if taluka_key is None:
            taluka_key = taluka_input
            taluka_dict[taluka_key] = []
        village_list = taluka_dict[taluka_key]

        # Village level case-insensitive check
        if not any(v.lower() == village_input.lower() for v in village_list):
            village_list.append(village_input)
            QMessageBox.information(self, "Success", f"Added Village '{village_input}' under Taluka '{taluka_key}', District '{district_key}', State '{state_key}'.")
        else:
            QMessageBox.information(self, "Info", f"Village '{village_input}' already exists under Taluka '{taluka_key}', District '{district_key}', State '{state_key}'.")

        try:
            with open(self.locations_file, 'w', encoding='utf-8') as f:
                json.dump(self.locations_data, f, indent=4, ensure_ascii=False)
            
            # Sync with GitHub
            github_sync.sync_file(self.locations_file)
            
            # Refresh AddEntryModule if it exists
            if hasattr(self.parent, 'add_entry_module'):
                self.parent.add_entry_module.refresh_locations()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save locations:\n{str(e)}")
            return

        self.state_input.clear()
        self.district_input.clear()
        self.taluka_input.clear()
        self.village_input.clear() 