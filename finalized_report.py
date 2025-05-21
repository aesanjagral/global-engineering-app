# finalized_report.py

import sys
import os
import json
import shutil
from functools import partial
from datetime import datetime
from pathlib import Path
from github_sync import github_sync

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QComboBox, QLineEdit, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class FinalizedReportModule(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Finalized Reports")
        
        # Define paths for user data
        self.user_data_folder = os.path.join(str(Path.home()), '.my_app_data')
        self.data_file = os.path.join(self.user_data_folder, 'data.json')
        
        # Create user data folder if it doesn't exist
        os.makedirs(self.user_data_folder, exist_ok=True)
        
        # If running from PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Download files from Drive if they don't exist
            if not os.path.exists(self.data_file):
                github_sync.download_file('data.json', self.data_file)

        # Initialize UI components
        self.init_ui()

        # Load data after UI is initialized
        self.load_payments()

    def init_ui(self):
        """Initialize the user interface components."""
        # Define the icons path
        self.icons_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Icons')

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Finalized Report")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Refresh Button
        self.refresh_button = QPushButton()
        refresh_icon_path = os.path.join(self.icons_folder, 'refresh.svg')
        if os.path.exists(refresh_icon_path):
            self.refresh_button.setIcon(QIcon(refresh_icon_path))
        else:
            self.refresh_button.setText("Refresh")
        self.refresh_button.setToolTip("Refresh Data")
        self.refresh_button.setFixedSize(30, 30)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_button)

        # Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by File No. or Date...")
        self.search_box.setFixedWidth(250)
        self.search_box.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #a5d6a7;
                border-radius: 5px;
                background-color: #e8f5e9;
            }
        """)
        self.search_box.textChanged.connect(self.apply_filter)
        header_layout.addWidget(self.search_box)

        # Month Filter ComboBox
        self.month_filter_combo = QComboBox()
        self.month_filter_combo.addItem("All Months")
        self.month_filter_combo.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        self.month_filter_combo.setFixedWidth(150)
        self.month_filter_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #a5d6a7;
                border-radius: 5px;
                background-color: #e8f5e9;
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
        self.month_filter_combo.currentIndexChanged.connect(self.apply_filter)
        header_layout.addWidget(self.month_filter_combo)

        # Year Filter ComboBox
        self.year_filter_combo = QComboBox()
        self.year_filter_combo.addItem("All Years")
        self.year_filter_combo.addItems([str(year) for year in range(2020, 2041)])
        self.year_filter_combo.setFixedWidth(100)
        self.year_filter_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #a5d6a7;
                border-radius: 5px;
                background-color: #e8f5e9;
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
        self.year_filter_combo.currentIndexChanged.connect(self.apply_filter)
        header_layout.addWidget(self.year_filter_combo)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(10)

        # Finalized Payments Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)  # SN, File No., Date, R.S.No./Block No., New No., Old No., Plot No., Payment Status, Work Status
        self.table.setHorizontalHeaderLabels([
            "SN", "File No.", "Date", "R.S.No./Block No.", "New No.", 
            "Old No.", "Plot No.", "Payment Status", "Work Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #e8f5e9;
                border: 1px solid #a5d6a7;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #c4edc6;
                color: #355837;
                padding: 10px;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
                font-size: 14px;
                border: none;
                border-bottom: 1px solid #c8e6c9;
                color: #2e7d32;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #81c784;
                color: #ffffff;
            }
        """)
        self.table.verticalHeader().setDefaultSectionSize(50)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

    def load_payments(self):
        """Load payment data from data.json and populate the table."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.payments = json.load(f)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to decode JSON. Please check the data.json file.")
            self.payments = []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading payments:\n{str(e)}")
            self.payments = []

        # Filter payments based on all three conditions with exact values
        self.payments = [
            p for p in self.payments 
            if p.get("Payment Prrovel status", "").lower() == "done" and
               p.get("Payment Status", "").lower() == "completed" and
               p.get("Work Status", "").lower() == "approved"
        ]

        self.display_payments(self.payments)

    def display_payments(self, payments):
        """Display finalized payment data in the table."""
        self.table.setRowCount(0)

        for idx, payment in enumerate(payments, start=1):
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            # SN
            sn_item = QTableWidgetItem(str(idx))
            sn_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 0, sn_item)

            # File No.
            file_no_item = QTableWidgetItem(payment.get("File No.", ""))
            file_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 1, file_no_item)

            # Date
            date_item = QTableWidgetItem(payment.get("Date", ""))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 2, date_item)

            # R.S.No./Block No.
            rs_block = payment.get("R.S.No./ Block No.", "")
            rs_block_item = QTableWidgetItem(rs_block)
            rs_block_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 3, rs_block_item)

            # New No.
            new_no = payment.get("New No.", "")
            new_no_item = QTableWidgetItem(new_no)
            new_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 4, new_no_item)

            # Old No.
            old_no = payment.get("Old No.", "")
            old_no_item = QTableWidgetItem(old_no)
            old_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 5, old_no_item)

            # Plot No.
            plot_no = payment.get("Plot No.", "")
            plot_no_item = QTableWidgetItem(plot_no)
            plot_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 6, plot_no_item)

            # Payment Status
            status = payment.get("Payment Status", "")
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 7, status_item)

            # Work Status
            work_status = payment.get("Work Status", "")
            work_status_item = QTableWidgetItem(work_status)
            work_status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 8, work_status_item)

    def apply_filter(self):
        """Filter the table based on the selected filters and search query."""
        selected_month = self.month_filter_combo.currentText()
        selected_year = self.year_filter_combo.currentText()
        search_query = self.search_box.text().strip().lower()

        filtered_payments = self.payments

        if selected_month != "All Months":
            filtered_payments = [
                p for p in filtered_payments
                if self.get_month(p.get("Date", "")) == selected_month
            ]

        if selected_year != "All Years":
            filtered_payments = [
                p for p in filtered_payments
                if self.get_year(p.get("Date", "")) == selected_year
            ]

        if search_query:
            filtered_payments = [
                p for p in filtered_payments
                if search_query in p.get("File No.", "").lower() or
                   search_query in p.get("Date", "").lower()
            ]

        self.display_payments(filtered_payments)

    def get_month(self, date_str):
        """Extract the month name from a date string formatted as DD/MM/YYYY."""
        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            return date_obj.strftime("%B")
        except:
            return ""

    def get_year(self, date_str):
        """Extract the year from a date string formatted as DD/MM/YYYY."""
        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            return str(date_obj.year)
        except:
            return ""

    def refresh_data(self):
        """Refresh data from GitHub"""
        try:
            # Try to download latest data from GitHub
            if github_sync.download_file('data.json', self.data_file):
                QMessageBox.information(self, "Success", "Data successfully synced")
            else:
                QMessageBox.warning(self, "Warning", "Could not sync from GitHub. Using local data.")
            
            # Reload data
            self.load_payments()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error refreshing data: {str(e)}")


# To run this module independently for testing purposes
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = FinalizedReportModule()
    window.setWindowTitle("Finalized Report")
    window.resize(1200, 700)
    window.show()
    sys.exit(app.exec_())
