# add_entry.py

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QSpacerItem,
    QSizePolicy, QDateEdit, QMessageBox, QGroupBox, QFormLayout, QScrollArea, QTextEdit,
    QTabWidget, QDialog, QCompleter
)
from PyQt5.QtCore import Qt, QDate, QStringListModel
from PyQt5.QtGui import QIntValidator, QPainter, QColor, QFont
import sys
import json
import os
import shutil  # For copying files
from github_sync import github_sync
from pathlib import Path

class NoScrollComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # सभी dropdowns के लिए dropdown_arrow.svg सेट करना
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

class AddEntryModule(QWidget):
    def __init__(self):
        super().__init__()
        
        # Define paths for user data
        self.user_data_folder = os.path.join(str(Path.home()), '.my_app_data')
        self.data_file = os.path.join(self.user_data_folder, 'data.json')
        self.work_types_file = os.path.join(self.user_data_folder, 'work_types.json')
        self.work_done_file = os.path.join(self.user_data_folder, 'work_done.json')
        self.locations_file = os.path.join(self.user_data_folder, 'locations.json')
        
        # Create user data folder if it doesn't exist
        os.makedirs(self.user_data_folder, exist_ok=True)
        
        # If running from PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Download files from Drive if they don't exist
            if not os.path.exists(self.data_file):
                github_sync.download_file('data.json', self.data_file)
            if not os.path.exists(self.work_types_file):
                github_sync.download_file('work_types.json', self.work_types_file)
            if not os.path.exists(self.work_done_file):
                github_sync.download_file('work_done.json', self.work_done_file)
            if not os.path.exists(self.locations_file):
                github_sync.download_file('locations.json', self.locations_file)
        
        # Load location data
        self.load_locations()

        # Window settings

        self.setWindowTitle("Add New Case")
        self.setGeometry(200, 200, 1000, 800)

        self.setStyleSheet("""
            QWidget {
                background-color: #fff6ee;
            }
            QLabel {
                color: #564234;
                font-size: 14px;
            }
            QLineEdit, QDateEdit, QComboBox, QTextEdit {
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                padding: 5px 10px;
                color: #564234;
                font-size: 14px;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 2px solid #ffcea1;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #ffcea1;
            }
            QCheckBox {
                color: #564234;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QPushButton {
                font-size: 16px;
                border-radius: 5px;
            }
            QGroupBox {
                border: 2px solid #ffcea1;
                border-radius: 5px;
                margin-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #564234;
                font-size: 18px;
                font-weight: bold;
            }
            QScrollBar:vertical {
                border: none;
                background: #fffcfa;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #ffcea1;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.create_add_entry_tab())
        self.setLayout(main_layout)

    def create_add_entry_tab(self):
        # Main Layout for Add Entry
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        header_label = QLabel("Add New Case")
        header_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #564234;")
        main_layout.addWidget(header_label, alignment=Qt.AlignLeft)

        form_container = QHBoxLayout()
        form_container.setSpacing(40)

        # Left Form Layout
        left_form_layout = QVBoxLayout()
        left_form_layout.setSpacing(15)

        self.file_no_label = QLabel("File No.")
        self.file_no = QLineEdit()
        self.file_no.setPlaceholderText("Enter File Number")
        self.file_no.setFixedHeight(40)
        left_form_layout.addWidget(self.file_no_label)
        left_form_layout.addWidget(self.file_no)

        self.date_label = QLabel("Date")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        self.date_edit.setFixedHeight(40)
        left_form_layout.addWidget(self.date_label)
        left_form_layout.addWidget(self.date_edit)

        self.state_label = QLabel("State")
        self.state = NoScrollComboBox()
        self.state.setFixedHeight(40)
        self.state.addItem("Select State")
        self.state.addItems(sorted(self.locations_data.keys()))
        self.state.currentIndexChanged.connect(self.update_districts)
        left_form_layout.addWidget(self.state_label)
        left_form_layout.addWidget(self.state)

        self.district_label = QLabel("District")
        self.district = NoScrollComboBox()
        self.district.setFixedHeight(40)
        self.district.addItem("Select District")
        self.district.currentIndexChanged.connect(self.update_talukas)
        left_form_layout.addWidget(self.district_label)
        left_form_layout.addWidget(self.district)

        self.taluka_label = QLabel("Taluka")
        self.taluka = NoScrollComboBox()
        self.taluka.setFixedHeight(40)
        self.taluka.addItem("Select Taluka")
        self.taluka.currentIndexChanged.connect(self.update_villages)
        left_form_layout.addWidget(self.taluka_label)
        left_form_layout.addWidget(self.taluka)

        self.village_label = QLabel("Village")
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
        
        left_form_layout.addWidget(self.village_label)
        left_form_layout.addWidget(self.village)

        self.customer_name_label = QLabel("Customer Name")
        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("Enter Customer Name")
        self.customer_name.setFixedHeight(40)
        
        # Add completer for customer name search
        self.customer_completer = QCompleter()
        self.customer_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.customer_name.setCompleter(self.customer_completer)
        self.customer_name.textChanged.connect(self.update_customer_suggestions)
        
        left_form_layout.addWidget(self.customer_name_label)
        left_form_layout.addWidget(self.customer_name)

        # Right Form Layout
        right_form_layout = QVBoxLayout()
        right_form_layout.setSpacing(15)

        self.mobile_number_label = QLabel("Mobile Number")
        self.mobile_number = QLineEdit()
        self.mobile_number.setPlaceholderText("e.g., 94269-62470")
        self.mobile_number.setInputMask("99999-99999;_")
        self.mobile_number.setFixedHeight(40)
        right_form_layout.addWidget(self.mobile_number_label)
        right_form_layout.addWidget(self.mobile_number)

        self.rs_block_label = QLabel("R.S.No./ Block No.")
        self.rs_block_combo = CustomComboBox()
        self.rs_block_combo.addItems(["Select Option", "R.S.No.", "Block No.", "City S.R.", "Gamtad"])
        self.rs_block_combo.setFixedHeight(40)
        right_form_layout.addWidget(self.rs_block_label)
        right_form_layout.addWidget(self.rs_block_combo)

        self.new_no_label = QLabel("New No.")
        self.new_no = QLineEdit()
        self.new_no.setPlaceholderText("Enter New Number")        
        self.new_no.setFixedHeight(40)
        right_form_layout.addWidget(self.new_no_label)
        right_form_layout.addWidget(self.new_no)

        self.old_no_label = QLabel("Old No.")
        self.old_no = QLineEdit()
        self.old_no.setPlaceholderText("Enter Old Number")
        self.old_no.setFixedHeight(40)
        right_form_layout.addWidget(self.old_no_label)
        right_form_layout.addWidget(self.old_no)

        self.plot_no_label = QLabel("Plot No.")
        self.plot_no = QLineEdit()
        self.plot_no.setPlaceholderText("Enter Plot Number")
        self.plot_no.setFixedHeight(40)
        right_form_layout.addWidget(self.plot_no_label)
        right_form_layout.addWidget(self.plot_no)

        self.final_amount_label = QLabel("Final Amount")
        self.final_amount = QLineEdit()
        self.final_amount.setPlaceholderText("Enter Final Amount")
        self.final_amount.setValidator(QIntValidator())
        self.final_amount.setFixedHeight(40)
        right_form_layout.addWidget(self.final_amount_label)
        right_form_layout.addWidget(self.final_amount)

        self.remark_label = QLabel("Remark")
        self.remark = QTextEdit()
        self.remark.setPlaceholderText("Enter Remark")
        self.remark.setFixedHeight(80)
        right_form_layout.addWidget(self.remark_label)
        right_form_layout.addWidget(self.remark)

        form_container.addLayout(left_form_layout)
        form_container.addLayout(right_form_layout)
        main_layout.addLayout(form_container)

        work_type_label = QLabel("Work Type")
        work_type_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #564234;")
        main_layout.addWidget(work_type_label, alignment=Qt.AlignLeft)

        work_type_layout = QHBoxLayout()
        work_type_layout.setSpacing(20)
        self.work_type_checks = self.load_work_types()
        for cb in self.work_type_checks:
            cb.setFixedHeight(30)
            cb.setStyleSheet("""
                QCheckBox {
                    font-size: 16px;
                    color: #564234;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)
            work_type_layout.addWidget(cb)
        main_layout.addLayout(work_type_layout)

        work_done_label = QLabel("Work Done")
        work_done_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #564234; margin-top: 20px;")
        main_layout.addWidget(work_done_label, alignment=Qt.AlignLeft)

        work_done_layout = QHBoxLayout()
        work_done_layout.setSpacing(20)
        self.work_done_checks = self.load_work_done()
        for cb in self.work_done_checks:
            cb.setFixedHeight(30)
            cb.setStyleSheet("""
                QCheckBox {
                    font-size: 14px;
                    color: #564234;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)
            work_done_layout.addWidget(cb)
        main_layout.addLayout(work_done_layout)

        party_address_group = QGroupBox("Party Address")
        party_address_layout = QFormLayout()
        party_address_layout.setSpacing(15)

        self.party_state_label = QLabel("State")
        self.party_state = NoScrollComboBox()
        self.party_state.addItem("Select State")
        self.party_state.addItems(sorted(self.locations_data.keys()))
        self.party_state.currentIndexChanged.connect(self.update_party_districts)
        party_address_layout.addRow(self.party_state_label, self.party_state)

        self.party_district_label = QLabel("District")
        self.party_district = NoScrollComboBox()
        self.party_district.addItem("Select District")
        self.party_district.currentIndexChanged.connect(self.update_party_talukas)
        party_address_layout.addRow(self.party_district_label, self.party_district)

        self.party_taluka_label = QLabel("Taluka")
        self.party_taluka = NoScrollComboBox()
        self.party_taluka.addItem("Select Taluka")
        self.party_taluka.currentIndexChanged.connect(self.update_party_villages)
        party_address_layout.addRow(self.party_taluka_label, self.party_taluka)

        self.party_village_label = QLabel("Village")
        self.party_village = NoScrollComboBox()
        self.party_village.addItem("Select Village")
        self.party_village.setEditable(True)  # Make it editable for searching
        self.party_village.lineEdit().editingFinished.connect(self.fill_party_location_by_village)  # Add search handler

        # Add completer for party village search
        self.party_village_completer = QCompleter()
        self.party_village_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.party_village.setCompleter(self.party_village_completer)
        self.party_village.lineEdit().textChanged.connect(self.update_party_village_suggestions)

        party_address_layout.addRow(self.party_village_label, self.party_village)

        party_address_group.setLayout(party_address_layout)
        main_layout.addWidget(party_address_group)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # Clear Button
        clear_button = QPushButton("Clear Form")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        clear_button.setFixedHeight(40)
        clear_button.clicked.connect(self.clear_form)
        button_layout.addWidget(clear_button)
        
        # Add spacer to push buttons to the right
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Submit Button
        submit_button = QPushButton("Submit Form")
        submit_button.setStyleSheet("""
            QPushButton {
                background-color: #ffa33e;
                color: #564234;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ff8c00;
            }
        """)
        submit_button.setFixedHeight(40)
        submit_button.clicked.connect(self.submit_form)
        button_layout.addWidget(submit_button)
        
        main_layout.addLayout(button_layout)

        container_widget = QWidget()
        container_widget.setLayout(main_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container_widget)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)

        return scroll_area

    def load_locations(self):
        if os.path.exists(self.locations_file):
            try:
                with open(self.locations_file, 'r', encoding='utf-8') as f:
                    self.locations_data = json.load(f)
                if not isinstance(self.locations_data, dict):
                    raise ValueError("locations.json must contain a dictionary.")
            except (json.JSONDecodeError, ValueError) as e:
                QMessageBox.critical(self, "Error", f"Failed to load Locations:\n{str(e)}")
                self.locations_data = {}
        else:
            QMessageBox.critical(self, "Error", f"locations.json not found in {self.user_data_folder}.")
            self.locations_data = {}

    def update_districts(self, index):
        state = self.state.currentText()
        self.district.clear()
        self.district.addItem("Select District")
        self.taluka.clear()
        self.taluka.addItem("Select Taluka")
        self.village.clear()
        self.village.addItem("Select Village")
        if state in self.locations_data:
            districts = sorted(self.locations_data[state].keys())
            self.district.addItems(districts)

    def update_talukas(self, index):
        state = self.state.currentText()
        district = self.district.currentText()
        self.taluka.clear()
        self.taluka.addItem("Select Taluka")
        self.village.clear()
        self.village.addItem("Select Village")
        if state in self.locations_data and district in self.locations_data[state]:
            talukas = sorted(self.locations_data[state][district].keys())
            self.taluka.addItems(talukas)

    def update_villages(self, index):
        state = self.state.currentText()
        district = self.district.currentText()
        taluka = self.taluka.currentText()
        self.village.clear()
        self.village.addItem("Select Village")
        if state in self.locations_data and district in self.locations_data[state] and taluka in self.locations_data[state][district]:
            villages = sorted(self.locations_data[state][district][taluka])
            self.village.addItems(villages)

    def update_party_districts(self, index):
        state = self.party_state.currentText()
        self.party_district.clear()
        self.party_district.addItem("Select District")
        self.party_taluka.clear()
        self.party_taluka.addItem("Select Taluka")
        self.party_village.clear()
        self.party_village.addItem("Select Village")
        if state in self.locations_data:
            districts = sorted(self.locations_data[state].keys())
            self.party_district.addItems(districts)

    def update_party_talukas(self, index):
        state = self.party_state.currentText()
        district = self.party_district.currentText()
        self.party_taluka.clear()
        self.party_taluka.addItem("Select Taluka")
        self.party_village.clear()
        self.party_village.addItem("Select Village")
        if state in self.locations_data and district in self.locations_data[state]:
            talukas = sorted(self.locations_data[state][district].keys())
            self.party_taluka.addItems(talukas)

    def update_party_villages(self, index):
        state = self.party_state.currentText()
        district = self.party_district.currentText()
        taluka = self.party_taluka.currentText()
        self.party_village.clear()
        self.party_village.addItem("Select Village")
        if state in self.locations_data and district in self.locations_data[state] and taluka in self.locations_data[state][district]:
            villages = sorted(self.locations_data[state][district][taluka])
            self.party_village.addItems(villages)

    def load_work_types(self):
        work_types = []
        if os.path.exists(self.work_types_file):
            try:
                with open(self.work_types_file, 'r', encoding='utf-8') as f:
                    types = json.load(f)
                if not isinstance(types, list):
                    raise ValueError("work_types.json must contain a list.")
                for wt in types:
                    cb = QCheckBox(wt)
                    work_types.append(cb)
            except (json.JSONDecodeError, ValueError) as e:
                QMessageBox.critical(self, "Error", f"Failed to load Work Types:\n{str(e)}")
        else:
            with open(self.work_types_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        return work_types

    def load_work_done(self):
        work_done = []
        if os.path.exists(self.work_done_file):
            try:
                with open(self.work_done_file, 'r', encoding='utf-8') as f:
                    done = json.load(f)
                if not isinstance(done, list):
                    raise ValueError("work_done.json must contain a list.")
                for wd in done:
                    cb = QCheckBox(wd)
                    work_done.append(cb)
            except (json.JSONDecodeError, ValueError) as e:
                QMessageBox.critical(self, "Error", f"Failed to load Work Done entries:\n{str(e)}")
        else:
            with open(self.work_done_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        return work_done

    def fill_location_by_village(self):
        village_name = self.village.currentText().strip()
        if not village_name:
            return
        # Search locations_data for village_name case-insensitively
        for state, districts in self.locations_data.items():
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

    def fill_party_location_by_village(self):
        """Fill party address location fields automatically based on village name"""
        village_name = self.party_village.currentText().strip()
        if not village_name or village_name == "Select Village":
            return

        # Search for the village in locations data
        for state in self.locations_data:
            for district in self.locations_data[state]:
                for taluka in self.locations_data[state][district]:
                    if village_name in self.locations_data[state][district][taluka]:
                        # Set state
                        state_index = self.party_state.findText(state)
                        if state_index != -1:
                            self.party_state.setCurrentIndex(state_index)
                            
                        # Set district
                        self.update_party_districts(state_index)
                        district_index = self.party_district.findText(district)
                        if district_index != -1:
                            self.party_district.setCurrentIndex(district_index)
                            
                        # Set taluka
                        self.update_party_talukas(district_index)
                        taluka_index = self.party_taluka.findText(taluka)
                        if taluka_index != -1:
                            self.party_taluka.setCurrentIndex(taluka_index)
                            
                        # Set village
                        self.update_party_villages(taluka_index)
                        village_index = self.party_village.findText(village_name)
                        if village_index != -1:
                            self.party_village.setCurrentIndex(village_index)
                        return

    def update_village_suggestions(self, text):
        """Update village suggestions based on input text"""
        if not text:
            self.village_completer.setModel(None)
            return

        suggestions = []
        for state in self.locations_data:
            for district in self.locations_data[state]:
                for taluka in self.locations_data[state][district]:
                    for village in self.locations_data[state][district][taluka]:
                        if text.lower() in village.lower():
                            suggestions.append(village)

        # Remove duplicates and sort
        unique_suggestions = sorted(list(set(suggestions)))
        model = QStringListModel(unique_suggestions)
        self.village_completer.setModel(model)

    def update_party_village_suggestions(self, text):
        """Update party village suggestions based on input text"""
        if not text:
            self.party_village_completer.setModel(None)
            return

        suggestions = []
        for state in self.locations_data:
            for district in self.locations_data[state]:
                for taluka in self.locations_data[state][district]:
                    for village in self.locations_data[state][district][taluka]:
                        if text.lower() in village.lower():
                            suggestions.append(village)

        # Remove duplicates and sort
        unique_suggestions = sorted(list(set(suggestions)))
        model = QStringListModel(unique_suggestions)
        self.party_village_completer.setModel(model)

    def update_customer_suggestions(self, text):
        """Update customer name suggestions based on input text"""
        if not text:
            self.customer_completer.setModel(None)
            return

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            suggestions = []
            customer_data = {}  # Store full customer data
            for entry in data:
                customer_name = entry.get("Customer Name", "")
                if text.lower() in customer_name.lower():
                    suggestions.append(customer_name)
                    # Store the most recent entry for each customer
                    customer_data[customer_name] = entry

            # Remove duplicates and sort
            unique_suggestions = sorted(list(set(suggestions)))
            model = QStringListModel(unique_suggestions)
            self.customer_completer.setModel(model)

            # Auto-fill form if exact match found
            if text in customer_data:
                self.auto_fill_customer_data(customer_data[text])

        except Exception as e:
            print(f"Error in update_customer_suggestions: {str(e)}")
            pass

    def set_party_address(self, state, district, taluka, village):
        """Set party address fields directly without triggering updates"""
        try:
            print(f"Setting party address - State: {state}, District: {district}, Taluka: {taluka}, Village: {village}")
            
            # First, block all signals
            self.party_state.blockSignals(True)
            self.party_district.blockSignals(True)
            self.party_taluka.blockSignals(True)
            self.party_village.blockSignals(True)
            
            # Set State (convert to uppercase since data is in uppercase)
            state = state.upper() if state else ""
            if state and state in self.locations_data:
                state_index = self.party_state.findText(state)
                if state_index != -1:
                    self.party_state.setCurrentIndex(state_index)
                
                # Set District
                if district and district in self.locations_data[state]:
                    self.party_district.clear()
                    self.party_district.addItem("Select District")
                    districts = sorted(self.locations_data[state].keys())
                    self.party_district.addItems(districts)
                    district_index = self.party_district.findText(district)
                    if district_index != -1:
                        self.party_district.setCurrentIndex(district_index)
                    
                    # Set Taluka
                    if taluka and taluka in self.locations_data[state][district]:
                        self.party_taluka.clear()
                        self.party_taluka.addItem("Select Taluka")
                        talukas = sorted(self.locations_data[state][district].keys())
                        self.party_taluka.addItems(talukas)
                        taluka_index = self.party_taluka.findText(taluka)
                        if taluka_index != -1:
                            self.party_taluka.setCurrentIndex(taluka_index)
                        
                        # Set Village
                        if village:
                            self.party_village.clear()
                            self.party_village.addItem("Select Village")
                            villages = sorted(self.locations_data[state][district][taluka])
                            self.party_village.addItems(villages)
                            village_index = self.party_village.findText(village)
                            if village_index != -1:
                                self.party_village.setCurrentIndex(village_index)
            
            # Unblock signals after all updates
            self.party_state.blockSignals(False)
            self.party_district.blockSignals(False)
            self.party_taluka.blockSignals(False)
            self.party_village.blockSignals(False)
            
            print("Party address set successfully")
            
        except Exception as e:
            print(f"Error setting party address: {str(e)}")
            # Unblock signals in case of error
            self.party_state.blockSignals(False)
            self.party_district.blockSignals(False)
            self.party_taluka.blockSignals(False)
            self.party_village.blockSignals(False)

    def auto_fill_customer_data(self, entry):
        """Auto-fill form fields based on customer entry data"""
        try:
            print("\n=== Starting Auto-Fill Process ===")
            print(f"Full Entry Data: {entry}")
            
            if not isinstance(entry, dict):
                print("Entry is not a dictionary")
                return

            # Fill mobile number
            mobile = entry.get("Mobile Number", "")
            print(f"Setting Mobile Number: {mobile}")
            self.mobile_number.setText(mobile)

            # Get Party Address
            party_address = entry.get("Party Address", {})
            print(f"\nParty Address Raw Data: {party_address}")
            
            # Handle party address whether it's a dict or string
            if isinstance(party_address, dict):
                state = party_address.get("State", "")
                district = party_address.get("District", "")
                taluka = party_address.get("Taluka", "")
                village = party_address.get("Village", "")
            elif isinstance(party_address, str):
                # Try to parse the string as a dictionary-like structure
                try:
                    # Convert string representation to dictionary
                    address_parts = dict(item.strip().split(": ") for item in 
                                       party_address.strip("{}").replace("'", "").split(", "))
                    state = address_parts.get("State", "")
                    district = address_parts.get("District", "")
                    taluka = address_parts.get("Taluka", "")
                    village = address_parts.get("Village", "")
                except:
                    state = district = taluka = village = ""
            else:
                state = district = taluka = village = ""
                
            print(f"\nExtracting Party Address Components:")
            print(f"State: {state}")
            print(f"District: {district}")
            print(f"Taluka: {taluka}")
            print(f"Village: {village}")
            
            # If party address is empty or contains "Select" values, try main location fields
            if not any([state, district, taluka, village]) or all(x.startswith("Select") for x in [state, district, taluka, village] if x):
                print("No valid party address data found in the entry")
                # Try to get address from main location fields as fallback
                state = entry.get("State", "")
                district = entry.get("District", "")
                taluka = entry.get("Taluka", "")
                village = entry.get("Village", "")
                print(f"\nTrying main location fields as fallback:")
                print(f"State: {state}")
                print(f"District: {district}")
                print(f"Taluka: {taluka}")
                print(f"Village: {village}")
            
            if any([state, district, taluka, village]) and not all(x.startswith("Select") for x in [state, district, taluka, village] if x):
                print("\nCalling set_party_address with data...")
                self.set_party_address(state, district, taluka, village)
            else:
                print("No valid address data found")

            # Show a message to inform user
            QMessageBox.information(
                self,
                "Auto-Fill",
                f"Mobile number and party address have been auto-filled with {entry.get('Customer Name', '')}'s previous data.\nPlease verify the details before submitting."
            )
            print("=== Auto-Fill Process Completed ===\n")

        except Exception as e:
            print(f"Error in auto_fill_customer_data: {str(e)}")
            import traceback
            print(f"Full error traceback:\n{traceback.format_exc()}")
            QMessageBox.warning(
                self,
                "Auto-Fill Error",
                f"Failed to auto-fill form: {str(e)}"
            )

    def reset_field_highlights(self):
        """Reset all field highlights to default"""
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
        self.rs_block_combo.setStyleSheet("""
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

    def submit_form(self):
        # Reset all field highlights first
        self.reset_field_highlights()

        file_no = self.file_no.text().strip()
        customer_name = self.customer_name.text().strip()
        current_date = self.date_edit.date()
        date = f"{current_date.day():02d}-{current_date.month():02d}-{current_date.year()}"
        mobile_number = self.mobile_number.text().strip()
        final_amount = self.final_amount.text().strip()

        # Validate File No.
        if not file_no:
            self.file_no.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid red;
                    border-radius: 5px;
                    background-color: #fff0f0;
                    font-size: 14px;
                }
            """)
            QMessageBox.warning(
                self,
                "File No. Error",
                "Please enter a File No."
            )
            return

        # Validate Customer Name
        if not customer_name:
            self.customer_name.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid red;
                    border-radius: 5px;
                    background-color: #fff0f0;
                    font-size: 14px;
                }
            """)
            QMessageBox.warning(
                self,
                "Customer Name Error",
                "Please enter a Customer Name"
            )
            return

        # Validate Final Amount
        if not final_amount:
            self.final_amount.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid red;
                    border-radius: 5px;
                    background-color: #fff0f0;
                    font-size: 14px;
                }
            """)
            QMessageBox.warning(
                self,
                "Final Amount Error",
                "Please enter a Final Amount"
            )
            return

        # Validate Final Amount is numeric and positive
        try:
            amount = float(final_amount)
            if amount < 0:
                self.final_amount.setStyleSheet("""
                    QLineEdit {
                        padding: 8px;
                        border: 2px solid red;
                        border-radius: 5px;
                        background-color: #fff0f0;
                        font-size: 14px;
                    }
                """)
                QMessageBox.warning(
                    self,
                    "Final Amount Error",
                    "Final Amount cannot be negative"
                )
                return
        except ValueError:
            self.final_amount.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid red;
                    border-radius: 5px;
                    background-color: #fff0f0;
                    font-size: 14px;
                }
            """)
            QMessageBox.warning(
                self,
                "Final Amount Error",
                "Please enter a valid numeric amount"
            )
            return

        # Validate Mobile Number first
        if not mobile_number or mobile_number == "_____-_____" or mobile_number == "-":
            self.mobile_number.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid red;
                    border-radius: 5px;
                    background-color: #fff0f0;
                    font-size: 14px;
                }
            """)
            QMessageBox.warning(
                self,
                "Mobile Number Error",
                "Please enter a valid mobile number"
            )
            return

        # Also validate mobile number format
        if not mobile_number.replace("-", "").isdigit() or len(mobile_number.replace("-", "")) != 10:
            self.mobile_number.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid red;
                    border-radius: 5px;
                    background-color: #fff0f0;
                    font-size: 14px;
                }
            """)
            QMessageBox.warning(
                self,
                "Mobile Number Error",
                "Please enter a valid 10-digit mobile number in format: 99999-99999"
            )
            return

        # Validate New No.
        if not self.new_no.text().strip():
            self.new_no.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid red;
                    border-radius: 5px;
                    background-color: #fff0f0;
                    font-size: 14px;
                }
            """)
            QMessageBox.warning(
                self,
                "New No. Error",
                "Please enter New No."
            )
            return

        # Validate Old No.
        if not self.old_no.text().strip():
            self.old_no.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid red;
                    border-radius: 5px;
                    background-color: #fff0f0;
                    font-size: 14px;
                }
            """)
            QMessageBox.warning(
                self,
                "Old No. Error",
                "Please enter Old No."
            )
            return

        # Validate Plot No.
        if not self.plot_no.text().strip():
            self.plot_no.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid red;
                    border-radius: 5px;
                    background-color: #fff0f0;
                    font-size: 14px;
                }
            """)
            QMessageBox.warning(
                self,
                "Plot No. Error",
                "Please enter Plot No."
            )
            return

        # Validate Party Address
        if self.party_state.currentText() == "Select State" or self.party_district.currentText() == "Select District" or self.party_taluka.currentText() == "Select Taluka" or self.party_village.currentText() == "Select Village":
            QMessageBox.warning(
                self,
                "Party Address Error",
                "Please fill complete Party Address"
            )
            return

        district = self.district.currentText()
        state = self.state.currentText()
        rs_block = self.rs_block_combo.currentText()

        # Validate R.S.No./Block No.
        if not rs_block or rs_block == "Select Option":
            self.rs_block_combo.setStyleSheet("""
                QComboBox {
                    background-color: #fff0f0;
                    border: 2px solid red;
                    border-radius: 5px;
                    padding: 4px 8px;
                    font-family: 'Century Gothic';
                }
                QComboBox::drop-down {
                    width: 24px;
                    border-left: 2px solid red;
                }
                QComboBox::down-arrow {
                    image: url(icons/dropdown_arrow.svg);
                    width: 10px;
                    height: 10px;
                }
            """)
            QMessageBox.warning(
                self,
                "R.S.No./Block No. Error",
                "Please select a valid option for R.S.No./Block No."
            )
            return

        new_no = self.new_no.text().strip()
        old_no = self.old_no.text().strip()
        plot_no = self.plot_no.text().strip()
        taluka = self.taluka.currentText()
        village = self.village.currentText()
        remark = self.remark.toPlainText().strip()

        party_state = self.party_state.currentText()
        party_district = self.party_district.currentText()
        party_taluka = self.party_taluka.currentText()
        party_village = self.party_village.currentText()

        # Check if village exists in locations.json
        village_exists = False
        if state in self.locations_data and district in self.locations_data[state] and taluka in self.locations_data[state][district]:
            if village in self.locations_data[state][district][taluka]:
                village_exists = True
        
        if not village_exists:
            self.village.setStyleSheet("""
                QComboBox {
                    background-color: #fff0f0;
                    border: 2px solid red;
                    border-radius: 5px;
                    padding: 4px 8px;
                    font-family: 'Century Gothic';
                }
                QComboBox::drop-down {
                    width: 24px;
                    border-left: 2px solid red;
                }
                QComboBox::down-arrow {
                    image: url(icons/dropdown_arrow.svg);
                    width: 10px;
                    height: 10px;
                }
            """)
            QMessageBox.warning(
                self,
                "Invalid Village",
                f"The village '{village}' does not exist in {taluka} taluka of {district} district in {state} state.\nPlease select a valid village from the dropdown."
            )
            return

        # Check if party village exists in locations.json (only if village is entered)
        if party_village and party_village != "Select Village":
            party_village_exists = False
            if party_state in self.locations_data and party_district in self.locations_data[party_state] and party_taluka in self.locations_data[party_state][party_district]:
                if party_village in self.locations_data[party_state][party_district][party_taluka]:
                    party_village_exists = True
            
            if not party_village_exists:
                self.party_village.setStyleSheet("""
                    QComboBox {
                        background-color: #fff0f0;
                        border: 2px solid red;
                        border-radius: 5px;
                        padding: 4px 8px;
                        font-family: 'Century Gothic';
                    }
                    QComboBox::drop-down {
                        width: 24px;
                        border-left: 2px solid red;
                    }
                    QComboBox::down-arrow {
                        image: url(icons/dropdown_arrow.svg);
                        width: 10px;
                        height: 10px;
                    }
                """)
                QMessageBox.warning(
                    self,
                    "Invalid Party Village",
                    f"The party village '{party_village}' does not exist in {party_taluka} taluka of {party_district} district in {party_state} state.\nPlease select a valid village from the dropdown."
                )
                return

        # Validate Work Types and Work Done
        work_types = [cb.text() for cb in self.work_type_checks if cb.isChecked()]
        work_done = [cb.text() for cb in self.work_done_checks if cb.isChecked()]

        if not work_types:
            QMessageBox.warning(
                self,
                "Work Types Error",
                "Please select at least one Work Type"
            )
            return

        if not work_done:
            QMessageBox.warning(
                self,
                "Work Done Error",
                "Please select at least one Work Done"
            )
            return

        try:
            if os.path.exists(self.data_file) and os.path.getsize(self.data_file) > 0:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                duplicate = any(entry.get("File No.", "").lower() == file_no.lower() for entry in data)
                if duplicate:
                    self.file_no.setStyleSheet("""
                        QLineEdit {
                            padding: 8px;
                            border: 2px solid red;
                            border-radius: 5px;
                            background-color: #fff0f0;
                            font-size: 14px;
                        }
                    """)
                    QMessageBox.warning(
                        self,
                        "Duplicate File No.",
                        f"The File No. '{file_no}' already exists. Please enter a unique File No."
                    )
                    return
            else:
                data = []
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to decode JSON from data.json. Please check the file format.")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while checking File No. duplicates:\n{str(e)}")
            return

        entry = {
            "File No.": file_no,
            "Customer Name": customer_name,
            "Date": date,
            "Mobile Number": mobile_number,
            "District": district,
            "State": state,
            "R.S.No./ Block No.": rs_block,
            "New No.": new_no,
            "Old No.": old_no,
            "Plot No.": plot_no,
            "Taluka": taluka,
            "Village": village,
            "Final Amount": final_amount,
            "Remark": remark,
            "Work Types": work_types,
            "Work Done": work_done,
            "Party Address": f"State: {party_state}\nDistrict: {party_district}\nTaluka: {party_taluka}\nVillage: {party_village}"
        }

        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                data.append(entry)
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            # Sync with Google Drive
            github_sync.sync_file(self.data_file)
            
            QMessageBox.information(self, "Form Submitted", "Data has been successfully saved and synced.")
            self.clear_form()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while saving data:\n{str(e)}")

    def clear_form(self):
        self.file_no.clear()
        self.customer_name.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.mobile_number.clear()
        self.district.setCurrentIndex(0)
        self.state.setCurrentIndex(0)
        self.rs_block_combo.setCurrentIndex(0)
        self.new_no.clear()
        self.old_no.clear()
        self.plot_no.clear()
        self.final_amount.clear()
        self.remark.clear()
        self.party_district.setCurrentIndex(0)
        self.party_state.setCurrentIndex(0)
        self.party_taluka.setCurrentIndex(0)
        self.party_village.setCurrentIndex(0)

        for cb in self.work_type_checks + self.work_done_checks:
            cb.setChecked(False)

    def refresh_locations(self):
        """Refresh locations data and update UI"""
        self.load_locations()
        
        # Update district comboboxes
        self.district.clear()
        self.district.addItems(self.locations_data.keys())
        
        self.party_district.clear()
        self.party_district.addItems(self.locations_data.keys())
        
        # Update village suggestions
        self.update_village_suggestions(self.village.text())
        self.update_party_village_suggestions(self.party_village.text())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AddEntryModule()
    window.show()
    sys.exit(app.exec_())
