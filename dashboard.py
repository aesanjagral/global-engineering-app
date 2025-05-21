# dashboard.py

import sys
import os
import json
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QComboBox, QMessageBox, QDateEdit
)
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QIcon
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QDate, QTimer
from github_sync import github_sync
from activity_tracker import ActivityTracker

# PyQtChart imports for the graph
from PyQt5.QtChart import (
    QChart, QChartView, QBarSet, QBarSeries,
    QBarCategoryAxis, QValueAxis
)


class DataLoader(QThread):
    data_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, data_file):
        super().__init__()
        self.data_file = data_file
        
    def run(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.data_loaded.emit(data)
            else:
                self.data_loaded.emit([])
        except Exception as e:
            self.error_occurred.emit(str(e))

class DashboardModule(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize activity tracker
        self.activity_tracker = ActivityTracker()

        # Cache mechanism
        self._data_cache = None
        self._last_load_time = None
        
        # Filter state flag
        self.date_filter_applied = False # Ensure this is initialized early

        # Define paths for user data
        self.user_data_folder = os.path.join(str(Path.home()), '.my_app_data')
        self.data_file = os.path.join(self.user_data_folder, 'data.json')

        # Create user data folder if it doesn't exist
        os.makedirs(self.user_data_folder, exist_ok=True)

        # Initialize data loader
        self.data_loader = DataLoader(self.data_file)
        self.data_loader.data_loaded.connect(self.on_data_loaded)
        self.data_loader.error_occurred.connect(self.on_load_error)

        # If running from PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Download files from Drive if they don't exist
            if not os.path.exists(self.data_file):
                github_sync.download_file('data.json', self.data_file)

        # Define the default data folder and file path
        self.data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

        # Check if running from a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Set up a writable directory in the user's home folder
            user_data_folder = Path.home() / ".my_app_data"
            user_data_folder.mkdir(exist_ok=True)

            # Define path for user-specific data.json
            user_data_file = user_data_folder / "data.json"

            # Copy data.json from bundled resources if it doesn't exist already
            if not user_data_file.exists():
                # Path to data.json within the bundled resources
                bundled_data_file = Path(sys._MEIPASS) / "data" / "data.json"
                if bundled_data_file.exists():
                    shutil.copy(str(bundled_data_file), str(user_data_file))
                else:
                    # Create an empty file if bundled file not found
                    user_data_file.write_text("[]")

            # Update the data_file path to point to the writable copy
            self.data_file = str(user_data_file)
        else:
            # Ensure folder exists in normal environment
            os.makedirs(self.data_folder, exist_ok=True)

        # Ensure data is synced from GitHub
        if not os.path.exists(self.data_file):
            github_sync.download_file('data.json', self.data_file)

        self.setWindowTitle("Dashboard with Advanced Scroll + Filter")
        self.setStyleSheet("""
            QWidget {
                background-color: #FFF6EE; /* Main background */
            }
            /* Add styles for Calendar Widget Popup */
            QCalendarWidget QToolButton {
                color: black; /* Month/Year text */
                font-size: 12px; /* Adjust size if needed */
                background-color: transparent;
                padding: 2px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #ffedd8; /* Light hover */
                 border-radius: 3px;
            }
             QCalendarWidget QSpinBox { /* Year editor */
                 color: black;
                 background-color: white;
                 selection-background-color: #FFA33E;
                 selection-color: black;
                 padding: 2px;
                 border: 1px solid #ffcea1;
                 border-radius: 3px;
            }
            QCalendarWidget QAbstractItemView:enabled { /* Dates grid */
                 font-size: 12px;
                 color: black; 
                 background-color: white;
                 selection-background-color: #FFA33E; 
                 selection-color: white; 
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar { /* Top navigation bar */
                 background-color: #FFE7D2; 
                 border: 1px solid #ffcea1;
                 border-bottom: none;
                 border-top-left-radius: 3px;
                 border-top-right-radius: 3px;
            }
            QCalendarWidget QAbstractItemView:disabled { /* Dates for other months */
                 color: #cccccc; 
            }
        """)
        self.resize(1300, 750)

        # ---------------------------------------------------------
        # 1) Data / Summaries (variables)
        # ---------------------------------------------------------
        self.data = []
        self.filtered_data = []  # Month/Year filter applied data

        self.total_pending_amount = 0.0
        self.total_remaining_amount = 0.0
        self.total_completed_amount = 0.0
        self.total_amount = 0.0

        # For counting number of cases
        self.all_case_count = 0
        self.final_case_count = 0       # Payment Status = Completed/Done
        self.approve_case_count = 0     # Work Status = Approved
        self.pending_case_count = 0     # Payment Status != Completed/Done

        # ---------------------------------------------------------
        # 2) Main Layout + ScrollArea
        # ---------------------------------------------------------
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # content_widget will hold all content, placed in scroll_area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)

        # ScrollArea with advanced scrollbar styling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(content_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #FFF6EE;
            }
            QScrollBar:vertical {
                background: #ffedd8;
                width: 5px;                
            }
            QScrollBar::handle:vertical {
                background: #FFA33E;
                min-height: 10px;
                border-radius: 8px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff8c00;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
        """)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

        # ---------------------------------------------------------
        # 3) Top Bar (Filters + Refresh + AddEntry)
        # ---------------------------------------------------------
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setSpacing(10)

        heading_label = QLabel("Global Engineering")
        heading_label.setFont(QFont("Century Gothic", 24, QFont.Bold))
        heading_label.setStyleSheet("color: #7e5d47;")
        top_bar_layout.addWidget(heading_label)

        top_bar_layout.addStretch()

        # -- Date Range Filter --
        date_filter_style = """
            QDateEdit {
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                padding: 4px 8px;
            }
            QDateEdit::up-button, QDateEdit::down-button {
                width: 0px; 
            }
            QDateEdit::drop-down {
                 image: url(icons/calendar_brown.svg); /* Use brown icon */
                 width: 20px;
                 height: 20px;
                 subcontrol-position: center right;
                 padding-right: 5px;
                 border: none;
            }
            QDateEdit::drop-down:hover {
                background-color: #ffedd8; /* Add hover effect */
            }
        """
        
        top_bar_layout.addWidget(QLabel("From:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1)) 
        self.start_date_edit.setFixedWidth(120)
        self.start_date_edit.setStyleSheet(date_filter_style)
        top_bar_layout.addWidget(self.start_date_edit)

        top_bar_layout.addWidget(QLabel("To:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate()) 
        self.end_date_edit.setFixedWidth(120)
        self.end_date_edit.setStyleSheet(date_filter_style)
        top_bar_layout.addWidget(self.end_date_edit)
        
        # -- Filter Button RE-ADDED --
        self.apply_filter_button = QPushButton("Filter")
        self.apply_filter_button.setFixedSize(70, 30)
        self.apply_filter_button.setStyleSheet("""
            QPushButton {
                background-color: #FFA33E;
                color: #564234;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff8c00;
            }
        """)
        self.apply_filter_button.clicked.connect(self.apply_date_range_filter) # Connect Filter button
        top_bar_layout.addWidget(self.apply_filter_button)

        # -- Refresh button --
        self.refresh_button = QPushButton()
        refresh_icon_path = os.path.join("icons", "refresh_dashborad.svg")
        if os.path.exists(refresh_icon_path):
            self.refresh_button.setIcon(QIcon(refresh_icon_path))
            self.refresh_button.setIconSize(QSize(20, 20))
        else:
            self.refresh_button.setText("↻")
        self.refresh_button.setFixedSize(35, 35)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFCFA;
                border: 1px solid #FFE3CC;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #FFEDE1;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_data)
        top_bar_layout.addWidget(self.refresh_button)

        # -- Add New Entry button --
        add_entry_button = QPushButton("Add New Entry")
        add_entry_button.setStyleSheet("""
            QPushButton {
                background-color: #7b614f;
                border: none;
                color: white;
                font-size: 14px;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #6d5442;
            }
        """)
        top_bar_layout.addWidget(add_entry_button)

        content_layout.addLayout(top_bar_layout)

        # ---------------------------------------------------------
        # 4) Cards Row (with Icons)
        # ---------------------------------------------------------
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        self.pending_card_label = None
        self.remaining_card_label = None
        self.completed_card_label = None
        self.amount_card_label = None

        def create_card(title, amount_float, icon_name):
            card_frame = QFrame()
            card_frame.setStyleSheet("""
                QFrame {
                    background-color: #FFA33E;
                    border-radius: 10px;
                }
            """)
            card_layout = QVBoxLayout(card_frame)
            card_layout.setContentsMargins(20, 20, 20, 20)
            card_layout.setSpacing(5)

            icon_title_layout = QHBoxLayout()
            icon_title_layout.setSpacing(8)

            icon_label = QLabel()
            icon_path = os.path.join("icons", icon_name)
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(pixmap)
            else:
                icon_label.setText("")

            title_label = QLabel(title)
            title_label.setFont(QFont("Century Gothic", 12, QFont.Bold))
            title_label.setStyleSheet("color: #fff;")

            icon_title_layout.addWidget(icon_label)
            icon_title_layout.addWidget(title_label)
            icon_title_layout.addStretch()

            card_layout.addLayout(icon_title_layout)

            amount_label = QLabel(f"₹ {amount_float:,.2f}")
            amount_label.setFont(QFont("Century Gothic", 16, QFont.Bold))
            amount_label.setStyleSheet("color: #fff;")
            card_layout.addWidget(amount_label)

            return card_frame, amount_label

        pending_card, self.pending_card_label = create_card("Total Pending", 0.0, "pending.svg")
        remaining_card, self.remaining_card_label = create_card("Total Remaining", 0.0, "remaining.svg")
        completed_card, self.completed_card_label = create_card("Total Completed", 0.0, "completed.svg")
        amount_card, self.amount_card_label = create_card("Total Amount", 0.0, "amount.svg")

        cards_layout.addWidget(pending_card)
        cards_layout.addWidget(remaining_card)
        cards_layout.addWidget(completed_card)
        cards_layout.addWidget(amount_card)

        content_layout.addLayout(cards_layout)

        # ---------------------------------------------------------
        # 5) Body Layout (Left + Right) - Reinstated
        # ---------------------------------------------------------
        body_layout = QHBoxLayout() # Recreate body layout
        body_layout.setSpacing(20)
        # body_layout.setContentsMargins(0, 15, 0, 0) # Remove top margin if not desired

        # ----- 5(A) Left Section - Reinstated
        left_section_layout = QVBoxLayout()
        left_section_layout.setSpacing(20)

        # Graph
        graph_frame = QFrame()
        graph_frame.setStyleSheet("QFrame { background-color: #FFF6EE; }")
        graph_layout = QVBoxLayout(graph_frame)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(5)

        graph_title = QLabel("Cases Graph")
        graph_title.setFont(QFont("Century Gothic", 14, QFont.Bold))
        graph_title.setStyleSheet("color: #7e5d47;")

        self.chart_view = QChartView()  # Placeholder
        self.chart_view.setStyleSheet("background-color: #fffefd;")
        self.chart_view.setFixedHeight(320) # Adjust height if needed

        graph_layout.addWidget(graph_title)
        graph_layout.addWidget(self.chart_view)
        left_section_layout.addWidget(graph_frame) # Add graph back to left layout

        # All Cases Table - Moved back to left section
        all_cases_label = QLabel("All Cases (Filtered)")
        all_cases_label.setFont(QFont("Century Gothic", 14, QFont.Bold))
        all_cases_label.setStyleSheet("color: #7e5d47;") # Removed margin-top
        left_section_layout.addWidget(all_cases_label)

        self.all_cases_table = QTableWidget()
        self.all_cases_table.setColumnCount(7) # Adjust column count as needed
        self.all_cases_table.setHorizontalHeaderLabels([
            "File No.", "Customer Name", "Date", "Village", 
            "Payment Status", "Work Status", "Final Amount"
        ])
        self.all_cases_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.all_cases_table.verticalHeader().setDefaultSectionSize(40)
        self.all_cases_table.verticalHeader().setVisible(False)
        self.all_cases_table.setShowGrid(False)
        # Apply the same stylesheet as other tables
        self.all_cases_table.setStyleSheet("""
            QTableWidget {
                background-color: #fffefd;
                border: 0px solid #ffcea1;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #fffefd;
                color: #d17a24;
                padding: 10px;
                border: none solid #ffcea1;
                border-bottom: 2px solid #ffcea1;                
                font-size: 14px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
                font-size: 14px;
                border: none solid #ffcea1;
                border-bottom: 0.5px solid #ffe9d7;
                color: #564234;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #ffcea1;
                color: #ffffff;
            }
            QPushButton {
                padding: 5px;
                font-size: 14px;
            }
            QScrollBar:vertical {
                background: #FFF;
                width: 5px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #ffa33e;
                min-height: 20px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff8c00;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
        """)
        self.all_cases_table.setFixedHeight(300) # Keep height or revert if needed
        left_section_layout.addWidget(self.all_cases_table) # Add table back to left layout

        # Pending Case Report
        pending_label = QLabel("Old Pending Case")
        pending_label.setFont(QFont("Century Gothic", 14, QFont.Bold))
        pending_label.setStyleSheet("color: #7e5d47;")
        left_section_layout.addWidget(pending_label)
        self.pending_table = QTableWidget()
        self.pending_table.setColumnCount(6)
        self.pending_table.setHorizontalHeaderLabels([
            "File No.", "Customer Name", "Date",
            "Village", "Payment Status", "Final Amount"
        ])
        self.pending_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pending_table.verticalHeader().setDefaultSectionSize(40)
        self.pending_table.verticalHeader().setVisible(False)
        self.pending_table.setShowGrid(False)
        self.pending_table.setStyleSheet("""
            QTableWidget {
                background-color: #fffefd;
                border: 0px solid #ffcea1;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #fffefd;
                color: #d17a24;
                padding: 10px;
                border: none solid #ffcea1;
                border-bottom: 2px solid #ffcea1;                
                font-size: 14px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
                font-size: 14px;
                border: none solid #ffcea1;
                border-bottom: 0.5px solid #ffe9d7;
                color: #564234;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #ffcea1;
                color: #ffffff;
            }
            QPushButton {
                padding: 5px;
                font-size: 14px;
            }
            QScrollBar:vertical {
                background: #FFF;
                width: 5px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #ffa33e;
                min-height: 20px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff8c00;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
        """)
        self.pending_table.setFixedHeight(300) # Keep height or revert if needed
        left_section_layout.addWidget(self.pending_table) # Add table back to left layout

        # Finalized Report
        finalized_label = QLabel("Finalized Case")
        finalized_label.setFont(QFont("Century Gothic", 14, QFont.Bold))
        finalized_label.setStyleSheet("color: #7e5d47;")
        left_section_layout.addWidget(finalized_label)
        self.finalized_table = QTableWidget()
        self.finalized_table.setColumnCount(4)
        self.finalized_table.setHorizontalHeaderLabels([
            "File No.", "Date", "Payment Status", "Work Status"
        ])
        self.finalized_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.finalized_table.verticalHeader().setDefaultSectionSize(40)
        self.finalized_table.setAlternatingRowColors(False)
        self.finalized_table.verticalHeader().setVisible(False)
        self.finalized_table.setShowGrid(False)
        self.finalized_table.setStyleSheet("""
            QTableWidget {
                background-color: #fffefd;
                border: 0px solid #ffcea1;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #fffefd;
                color: #d17a24;
                padding: 10px;
                border: none solid #ffcea1;
                border-bottom: 2px solid #ffcea1;
                font-size: 14px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
                font-size: 14px;
                border: none solid #ffcea1;
                border-bottom: 0.5px solid #ffe9d7;
                color: #564234;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #ffcea1;
                color: #ffffff;
            }
            QPushButton {
                padding: 5px;
                font-size: 14px;
            }
            QScrollBar:vertical {
                background: #FFF;
                width: 5px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #ffa33e;
                min-height: 20px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff8c00;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
        """)
        self.finalized_table.setFixedHeight(480) # Revert to original height? Or keep 300?
        left_section_layout.addWidget(self.finalized_table) # Add table back to left layout

        body_layout.addLayout(left_section_layout) # Add left section back to body

        # ----- 5(B) Right Section - Reinstated
        right_section_layout = QVBoxLayout()
        right_section_layout.setSpacing(20)

        all_case_report_label = QLabel("All Case Report") # Reinstate label
        all_case_report_label.setFont(QFont("Century Gothic", 14))
        all_case_report_label.setStyleSheet("color: #7e5d47;")
        right_section_layout.addWidget(all_case_report_label)

        lorem_label = QLabel("Lorem ipsum dolor sit amet,\n" # Reinstate label
                             "consectetuer adipiscing elit,\n"
                             "sed diam nonummy nibh.")
        lorem_label.setStyleSheet("color: #7e5d47;")
        right_section_layout.addWidget(lorem_label)

        self.all_case_box_label = None
        self.final_case_box_label = None
        self.approve_case_box_label = None
        self.pending_case_box_label = None

        def create_status_box(box_title, value):
            box_frame = QFrame()
            box_frame.setStyleSheet("""
                QFrame {
                    background-color: #FFE7D2;
                    border-radius: 8px;
                }
            """)
            box_layout = QVBoxLayout(box_frame)
            box_layout.setContentsMargins(10, 10, 100, 30) # Original margins
            box_layout.setSpacing(5)

            title_lbl = QLabel(box_title)
            title_lbl.setStyleSheet("""
                color: #AD6721;
                font-weight: bold;
                font-family: "Century Gothic";
            """)
            title_lbl.setAlignment(Qt.AlignLeft)

            val_lbl = QLabel(str(value))
            val_lbl.setStyleSheet("""
                color: #ffa33e;
                font-weight: bold;
                font-size: 22px;
                font-family: "Century Gothic";
            """)
            val_lbl.setAlignment(Qt.AlignLeft)

            box_layout.addWidget(title_lbl)
            box_layout.addWidget(val_lbl)
            return box_frame, val_lbl
        
        all_case_box, self.all_case_box_label = create_status_box("All Case", 0)
        right_section_layout.addWidget(all_case_box)

        final_case_box, self.final_case_box_label = create_status_box("Final Case", 0)
        right_section_layout.addWidget(final_case_box)

        approve_case_box, self.approve_case_box_label = create_status_box("Approve Case", 0)
        right_section_layout.addWidget(approve_case_box)

        pending_case_box, self.pending_case_box_label = create_status_box("Pending Case", 0)
        right_section_layout.addWidget(pending_case_box)

        right_section_layout.addStretch()

        body_layout.addLayout(right_section_layout) # Add right section back to body

        content_layout.addLayout(body_layout) # Add the main body layout back

        # ---------------------------------------------------------
        # 6) Activity Section (Adjust numbering if needed)
        # ---------------------------------------------------------
        activity_section = QFrame()
        activity_section.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 5px;
                /* margin-top: 15px; */ /* Remove or keep margin? */
            }
        """)
        activity_layout = QVBoxLayout(activity_section)
        
        # Activity Header with Filter
        activity_header = QHBoxLayout()
        activity_title = QLabel("Recent Activities")
        activity_title.setFont(QFont("Century Gothic", 16, QFont.Bold))
        activity_title.setStyleSheet("color: #7e5d47; padding: 10px 0;")
        activity_header.addWidget(activity_title)
        
        # Add date filter for activities
        self.activity_date_filter = QComboBox()
        self.activity_date_filter.setFixedWidth(150)
        self.activity_date_filter.setStyleSheet("""
            QComboBox {
                padding: 5px;
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
        self.activity_date_filter.currentIndexChanged.connect(self.filter_activities)
        activity_header.addWidget(self.activity_date_filter)
        
        # Refresh button for activities
        refresh_activities_btn = QPushButton()
        refresh_activities_btn.setIcon(QIcon("icons/refresh_dashborad.svg"))
        refresh_activities_btn.setFixedSize(35, 35)
        refresh_activities_btn.setStyleSheet("""
            QPushButton {
                background-color: #fff6ee;
                border: 1px solid #ffcea1;
                border-radius: 17px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #ffe4cc;
            }
        """)
        refresh_activities_btn.clicked.connect(self.load_activities)
        activity_header.addWidget(refresh_activities_btn)
        activity_layout.addLayout(activity_header)
        
        # Add spacing after header
        activity_layout.addSpacing(10)
        
        # Activity Table
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Time", "Module", "Action", "Details"])
        self.activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.activity_table.verticalHeader().setDefaultSectionSize(40)
        self.activity_table.setAlternatingRowColors(False)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setShowGrid(False)
        self.activity_table.setFixedHeight(300)
        self.activity_table.setStyleSheet("""
            QTableWidget {
                background-color: #fffefd;
                border: 0px solid #ffcea1;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #fffefd;
                color: #d17a24;
                padding: 10px;
                border: none solid #ffcea1;
                border-bottom: 2px solid #ffcea1;
                font-size: 14px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
                font-size: 14px;
                border: none solid #ffcea1;
                border-bottom: 0.5px solid #ffe9d7;
                color: #564234;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #ffcea1;
                color: #ffffff;
            }
            QPushButton {
                padding: 5px;
                font-size: 14px;
            }
            QScrollBar:vertical {
                background: #FFF;
                width: 5px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #ffa33e;
                min-height: 20px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff8c00;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
        """)
        activity_layout.addWidget(self.activity_table)
        
        # Add activity section to content layout
        content_layout.addWidget(activity_section)
        
        # Load initial activities
        self.load_activities()

        # Finally, load data and refresh
        self.load_data()

        # Add auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    # --------------------------------------------------
    #   DATA REFRESH/LOAD
    # --------------------------------------------------
    def refresh_data(self):
        """Refresh data from GitHub and reset filter state"""
        self.date_filter_applied = False # Reset filter flag
        try:
            if github_sync.download_file('data.json', self.data_file):
                self.activity_tracker.log_activity("Dashboard", "Data Sync", "Successfully synced data from GitHub")
                QMessageBox.information(self, "Success", "Data successfully synced")
            else:
                self.activity_tracker.log_activity("Dashboard", "Data Sync", "Failed to sync from GitHub")
                QMessageBox.warning(self, "Warning", "Could not sync from GitHub. Using local data.")
            
            self.load_data() # Load data (will trigger update_dashboard showing all data)
        except Exception as e:
            self.activity_tracker.log_activity("Dashboard", "Error", f"Error refreshing data: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error refreshing data: {str(e)}")
            
    def on_data_loaded(self, data):
        """Called when data is loaded in background"""
        self._data_cache = data
        self._last_load_time = datetime.now()
        self.data = data
        self.update_dashboard() # Update dashboard (will use self.date_filter_applied state)
        
    def on_load_error(self, error_message):
        """Called when error occurs during data loading"""
        QMessageBox.critical(self, "Error", f"Error loading data: {error_message}")
        
    def load_data(self):
        """Load data with caching"""
        # If cache exists and is less than 5 minutes old, use it
        if self._data_cache and self._last_load_time:
            cache_age = (datetime.now() - self._last_load_time).total_seconds()
            if cache_age < 300:  # 5 minutes
                self.data = self._data_cache
                self.update_dashboard() # Update with cached data (uses self.date_filter_applied state)
                return
                
        # Start background loading
        self.data_loader.start()

    # --------------------------------------------------
    #   FILTERING
    # --------------------------------------------------
    def apply_date_range_filter(self):
        """Applies the date range filter and updates the dashboard."""
        self.date_filter_applied = True # Set flag to apply filter
        self.update_dashboard()
        # Log activity 
        start_date = self.start_date_edit.date().toString("dd/MM/yyyy")
        end_date = self.end_date_edit.date().toString("dd/MM/yyyy")
        self.log_activity("Dashboard", "Filter Applied", f"Date Range: {start_date} - {end_date}")

    def apply_filter(self, records):
        """Filters records based on the date range IF the filter is applied."""
        if not self.date_filter_applied:
            return records # Return all records if filter is not active

        # Apply date range filter only if flag is True
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()

        filtered = []
        for r in records:
            date_str = r.get("Date", "")
            try:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
                qt_date_obj = QDate(date_obj.year, date_obj.month, date_obj.day)
                if start_date <= qt_date_obj <= end_date:
                    filtered.append(r)
            except ValueError:
                continue 
        return filtered

    # --------------------------------------------------
    #   COMPUTE SUMMARY
    # --------------------------------------------------
    def compute_summary(self):
        self.total_pending_amount = 0.0
        self.total_completed_amount = 0.0
        self.total_amount = 0.0
        self.total_remaining_amount = 0.0

        self.all_case_count = 0
        self.final_case_count = 0
        self.approve_case_count = 0
        self.pending_case_count = 0

        for record in self.filtered_data:
            final_amt_str = record.get("Final Amount", "0")
            try:
                final_amt = float(final_amt_str)
            except:
                final_amt = 0.0

            self.total_amount += final_amt
            self.all_case_count += 1

            pay_status = record.get("Payment Status", "").lower()
            if pay_status in ("completed", "done"):
                self.total_completed_amount += final_amt
                self.final_case_count += 1
            else:
                self.total_pending_amount += final_amt
                self.pending_case_count += 1

            work_status = record.get("Work Status", "").lower()
            if work_status == "approved":
                self.approve_case_count += 1

        self.total_remaining_amount = self.total_amount - self.total_completed_amount

    # --------------------------------------------------
    #   GRAPH (Bar Chart) CREATION
    # --------------------------------------------------
    def create_bar_chart(self):
        set_pending = QBarSet("Pending")
        set_allcase = QBarSet("All")
        set_approve = QBarSet("Approve")
        set_final = QBarSet("Finalize")

        set_pending.append(self.pending_case_count)
        set_allcase.append(self.all_case_count)
        set_approve.append(self.approve_case_count)
        set_final.append(self.final_case_count)

        series = QBarSeries()
        series.append(set_pending)
        series.append(set_allcase)
        series.append(set_approve)
        series.append(set_final)

        set_pending.setColor(QColor("#FFA33E"))  
        set_allcase.setColor(QColor("#47bfff"))
        set_approve.setColor(QColor("#c7f464"))
        set_final.setColor(QColor("#ff8c00"))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Cases Overview")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundRoundness(10)

        categories = [""]
        axisX = QBarCategoryAxis()
        axisX.append(categories)
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        max_val = max(
            self.all_case_count,
            self.approve_case_count,
            self.final_case_count,
            self.pending_case_count
        )
        axisY = QValueAxis()
        axisY.setRange(0, max_val + 1)
        axisY.setLabelFormat("%.0f")
        chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.legend().setFont(QFont("Century Gothic", 10))

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setFixedHeight(500)
        return chart_view

    # --------------------------------------------------
    #   TABLES
    # --------------------------------------------------
    def populate_all_cases_table(self):
        """Populate the table showing all cases within the filtered date range."""
        try:
            # Sort filtered data by date (optional, can sort as needed)
            def parse_date(record):
                date_str = record.get("Date", "")
                try:
                    return datetime.strptime(date_str, "%d/%m/%Y")
                except:
                    return datetime.min # Oldest possible date for sorting errors
            
            sorted_data = sorted(self.filtered_data, key=parse_date, reverse=True) # Newest first

            self.all_cases_table.setRowCount(len(sorted_data))

            for row_index, record in enumerate(sorted_data):
                file_no = record.get("File No.", "")
                cust_name = record.get("Customer Name", "")
                date = record.get("Date", "")
                village = record.get("Village", "")
                payment_status = record.get("Payment Status", "")
                work_status = record.get("Work Status", "")
                amt_str = record.get("Final Amount", "0")
                try:
                    amt_val = float(amt_str)
                    final_amt_formatted = f"₹{amt_val:,.2f}"
                except:
                    final_amt_formatted = "₹0.00" 

                row_data = [file_no, cust_name, date, village, payment_status, work_status, final_amt_formatted]

                for col_index, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.all_cases_table.setItem(row_index, col_index, item)
        except Exception as e:
            print(f"Error populating all cases table: {e}")
            QMessageBox.warning(self, "Table Error", f"Could not populate All Cases table: {e}")

    def populate_pending_table(self):
        pending_records = []
        for r in self.filtered_data:
            pay_status = r.get("Payment Status", "").lower()
            if pay_status not in ("completed", "done"):
                pending_records.append(r)

        def parse_date(record):
            date_str = record.get("Date", "")
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                return datetime.min

        pending_records.sort(key=parse_date)
        pending_records = pending_records[:10]

        self.pending_table.setRowCount(len(pending_records))

        for row_index, record in enumerate(pending_records):
            file_no = record.get("File No.", "")
            cust_name = record.get("Customer Name", "")
            date = record.get("Date", "")
            village = record.get("Village", "")
            payment_status = record.get("Payment Status", "")
            amt_str = record.get("Final Amount", "0")
            try:
                amt_val = float(amt_str)
            except:
                amt_val = 0.0

            final_amt_formatted = f"₹{amt_val:,.2f}"
            row_data = [file_no, cust_name, date, village, payment_status, final_amt_formatted]

            for col_index, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.pending_table.setItem(row_index, col_index, item)

    def populate_finalized_table(self):
        finalized_records = []
        for r in self.filtered_data:
            pay_status = r.get("Payment Status", "").lower()
            if pay_status in ("completed", "done"):
                finalized_records.append(r)

        def parse_date(record):
            date_str = record.get("Date", "")
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                return datetime.min

        finalized_records.sort(key=parse_date)
        finalized_records = finalized_records[:10]

        self.finalized_table.setRowCount(len(finalized_records))

        for row_index, record in enumerate(finalized_records):
            file_no = record.get("File No.", "")
            date = record.get("Date", "")
            pay_status = record.get("Payment Status", "")
            work_status = record.get("Work Status", "")

            row_data = [file_no, date, pay_status, work_status]

            for col_index, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.finalized_table.setItem(row_index, col_index, item)

    # --------------------------------------------------
    #   UPDATE DASHBOARD
    # --------------------------------------------------
    def update_dashboard(self):
        # Filter data based on the current state of self.date_filter_applied
        self.filtered_data = self.apply_filter(self.data)

        # Compute summary based on filtered_data (which might be all data or ranged data)
        self.compute_summary()

        # Update cards
        if self.pending_card_label:
            self.pending_card_label.setText(f"₹ {self.total_pending_amount:,.2f}")
        if self.remaining_card_label:
            self.remaining_card_label.setText(f"₹ {self.total_remaining_amount:,.2f}")
        if self.completed_card_label:
            self.completed_card_label.setText(f"₹ {self.total_completed_amount:,.2f}")
        if self.amount_card_label:
            self.amount_card_label.setText(f"₹ {self.total_amount:,.2f}")

        # Update status boxes
        if self.all_case_box_label:
            self.all_case_box_label.setText(f"{self.all_case_count:,}")
        if self.final_case_box_label:
            self.final_case_box_label.setText(f"{self.final_case_count:,}")
        if self.approve_case_box_label:
            self.approve_case_box_label.setText(f"{self.approve_case_count:,}")
        if self.pending_case_box_label:
            self.pending_case_box_label.setText(f"{self.pending_case_count:,}")
            
        # Update charts and tables using self.filtered_data
        # Re-create chart with filtered data
        new_chart_view = self.create_bar_chart()
        # Find the layout containing the chart view
        parent_layout = self.chart_view.parentWidget().layout()
        # Get the index of the current chart view
        idx = parent_layout.indexOf(self.chart_view)
        if idx != -1:
            # Properly remove the old widget
            old_widget = parent_layout.takeAt(idx).widget()
            if old_widget:
                old_widget.deleteLater() # Schedule deletion
        # Add the new chart view
        self.chart_view = new_chart_view
        parent_layout.insertWidget(idx, self.chart_view) # Insert at the original index

        # Populate tables
        self.populate_all_cases_table()
        self.populate_pending_table()
        self.populate_finalized_table()

        # Update activities (remains separate filter)
        self.filter_activities()

    def load_activities(self):
        """Load and display recent activities with date filtering"""
        # Get unique dates from last 30 days of activities
        activities = self.activity_tracker.get_activities(limit=None)  # Get all activities from last 30 days
        
        # Update date filter options
        dates = set()
        for activity in activities:
            try:
                activity_date = datetime.strptime(activity['datetime'].split()[0], "%Y-%m-%d")
                if (datetime.now() - activity_date).days <= 30:  # Only include last 30 days
                    dates.add(activity_date.strftime("%Y-%m-%d"))
            except:
                continue
        
        # Update combobox items
        current_text = self.activity_date_filter.currentText()
        self.activity_date_filter.clear()
        self.activity_date_filter.addItem("All Days")
        for date in sorted(dates, reverse=True):
            self.activity_date_filter.addItem(date)
        
        # Restore previous selection if possible
        index = self.activity_date_filter.findText(current_text)
        if index >= 0:
            self.activity_date_filter.setCurrentIndex(index)
        else:
            self.activity_date_filter.setCurrentIndex(0)
        
        self.filter_activities()

    def filter_activities(self):
        """Filter activities based on selected date"""
        selected_date = self.activity_date_filter.currentText()
        activities = self.activity_tracker.get_activities(limit=None)  # Get all activities from last 30 days
        
        filtered_activities = []
        for activity in activities:
            try:
                activity_date = datetime.strptime(activity['datetime'].split()[0], "%Y-%m-%d")
                # Only include activities from last 30 days
                if (datetime.now() - activity_date).days > 30:
                    continue
                    
                if selected_date == "All Days" or activity['datetime'].startswith(selected_date):
                    filtered_activities.append(activity)
            except:
                continue
        
        # Update table with filtered activities
        self.update_activity_table(filtered_activities)

    def update_activity_table(self, activities):
        """Update the activity table with the provided activities"""
        # Filter out Data Sync and refresh activities
        filtered_activities = [
            activity for activity in activities 
            if not (activity['action'] == 'Data Sync' or 
                   activity['action'] == 'Refresh' or 
                   'refresh' in activity['details'].lower() or 
                   'sync' in activity['details'].lower())
        ]
        
        # Sort activities by datetime in reverse order (newest first)
        filtered_activities.sort(key=lambda x: datetime.strptime(x['datetime'], '%Y-%m-%d %H:%M:%S'), reverse=True)
        
        self.activity_table.setRowCount(len(filtered_activities))
        for row, activity in enumerate(filtered_activities):
            # Time
            time_item = QTableWidgetItem(activity['datetime'])
            time_item.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 0, time_item)
            
            # Module
            module_item = QTableWidgetItem(activity['module'])
            module_item.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 1, module_item)
            
            # Action
            action_item = QTableWidgetItem(activity['action'])
            action_item.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 2, action_item)
            
            # Details
            details_item = QTableWidgetItem(activity['details'])
            self.activity_table.setItem(row, 3, details_item)
            
        # Adjust column widths
        self.activity_table.setColumnWidth(0, 150)  # Time
        self.activity_table.setColumnWidth(1, 100)  # Module
        self.activity_table.setColumnWidth(2, 100)  # Action
        # Details column is already set to stretch

    def log_activity(self, module: str, action: str, details: str):
        """Log a new activity and refresh the activity table"""
        if self.activity_tracker.log_activity(module, action, details):
            self.load_activities()  # Refresh the activity table

    def save_activity(self, module, action, details):
        """Save a new activity"""
        self.activity_tracker.log_activity(module, action, details)

    def on_refresh_clicked(self):
        self.load_data()
        self.update_dashboard()
        self.save_activity("Dashboard", "Refresh", "Dashboard data refreshed")
        
    def auto_refresh(self):
        """Automatically refresh data if it's not locked"""
        try:
            if not github_sync.is_locked():
                self.refresh_data()
        except Exception as e:
            self.activity_tracker.log_activity("Dashboard", "Error", f"Auto-refresh failed: {str(e)}")
            
    def closeEvent(self, event):
        """Clean up when window is closed"""
        self.refresh_timer.stop()
        super().closeEvent(event)

# For standalone testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard_window = DashboardModule()
    dashboard_window.show()
    sys.exit(app.exec_())
