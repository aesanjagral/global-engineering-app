# approve.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QComboBox, QLineEdit, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import json
import os
import sys
import shutil
from pathlib import Path
from functools import partial
from datetime import datetime
from github_sync import github_sync

class ApprovalModule(QWidget):
    def __init__(self):
        super().__init__()

        # Define paths for user data
        self.user_data_folder = os.path.join(str(Path.home()), '.my_app_data')
        self.data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        self.data_file = os.path.join(self.user_data_folder, 'data.json')

        # Create user data folder if it doesn't exist
        os.makedirs(self.user_data_folder, exist_ok=True)

        # If running from PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Download files from Drive if they don't exist
            if not os.path.exists(self.data_file):
                github_sync.download_file('data.json', self.data_file)
        else:
            # Ensure folder exists in normal environment
            os.makedirs(self.data_folder, exist_ok=True)

        # Ensure data is synced from Google Drive
        if not os.path.exists(self.data_file):
            github_sync.download_file('data.json', self.data_file)

        # Define the icons path
        self.icons_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Icons')

        # Initialize Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header Layout and Widgets
        header_layout = QHBoxLayout()
        header_label = QLabel("Work Approval Management")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFA33E;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        load_button = QPushButton("Load Approvals")
        load_button.setFixedSize(150, 40)
        load_button.setStyleSheet("""
            QPushButton {
                background-color: #FFA33E;
                border: none;
                color: white;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #FF8C00;
            }
        """)
        load_button.clicked.connect(self.load_approvals)
        header_layout.addWidget(load_button)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.setFixedWidth(200)
        self.search_box.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
            }
        """)
        self.search_box.textChanged.connect(self.apply_filter)
        header_layout.addWidget(self.search_box)

        self.month_filter_combo = QComboBox()
        self.month_filter_combo.addItem(QIcon("icons/filter.svg"), "All")

        self.month_filter_combo.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        self.month_filter_combo.setFixedWidth(150)
        self.month_filter_combo.setStyleSheet("""
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
        self.month_filter_combo.currentIndexChanged.connect(self.apply_filter)
        header_layout.addWidget(self.month_filter_combo)

        self.year_filter_combo = QComboBox()
        self.year_filter_combo.addItem(QIcon("icons/filter.svg"), "All")
        self.year_filter_combo.addItems([str(year) for year in range(2020, 2041)])
        self.year_filter_combo.setFixedWidth(100)
        self.year_filter_combo.setStyleSheet("""
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
        self.year_filter_combo.currentIndexChanged.connect(self.apply_filter)
        header_layout.addWidget(self.year_filter_combo)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem(QIcon("icons/filter.svg"), "All")
        self.filter_combo.addItem(QIcon("icons/pending.svg"), "Pending")
        self.filter_combo.addItem(QIcon("icons/approved.svg"), "Approved")
        self.filter_combo.setFixedWidth(150)
        self.filter_combo.setStyleSheet("""
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
        self.filter_combo.currentIndexChanged.connect(self.apply_filter)
        header_layout.addWidget(self.filter_combo)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "SN", "File No.", "Customer Name", "Village", "R.S.No./ Block No.",
            "New No.", "Old No.", "Plot No.", "Work Types", "Approve Work"
        ])
        
        # Enable word wrap for all items
        self.table.setWordWrap(True)
        
        # Set column widths
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # SN
        self.table.setColumnWidth(0, 40)
        
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)  # File No.
        self.table.setColumnWidth(1, 80)
        
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Customer Name
        
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)  # Village
        self.table.setColumnWidth(3, 130)
        
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)  # R.S.No./ Block No.
        self.table.setColumnWidth(4, 140)
        
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)  # New No.
        self.table.setColumnWidth(5, 90)
        
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)  # Old No.
        self.table.setColumnWidth(6, 100)
        
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)  # Plot No.
        self.table.setColumnWidth(7, 100)
        
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)  # Work Types
        self.table.setColumnWidth(8, 190)
        
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)  # Approve Work
        self.table.setColumnWidth(9, 160)
        
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
        """)
        # Set minimum row height and enable auto-resize
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

        # Load data initially
        self.load_approvals()

    def load_approvals(self):
        """Load approval data from data.json and populate the table."""
        if not os.path.exists(self.data_file):
            QMessageBox.warning(self, "No Data", "No approval data found.")
            self.approvals = []
            self.display_approvals(self.approvals)
            return

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.approvals = json.load(f)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to decode JSON. Please check the data.json file.")
            self.approvals = []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading approvals:\n{str(e)}")
            self.approvals = []

        for sale in self.approvals:
            if "Work Status" not in sale:
                sale["Work Status"] = "Pending"
            elif sale["Work Status"] not in ["Pending", "Approved"]:
                sale["Work Status"] = "Pending"

        self.display_approvals(self.approvals)

    def display_approvals(self, approvals):
        """Display approval data in the table."""
        self.table.setRowCount(0)
        for idx, sale in enumerate(approvals, start=1):
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            sn_item = QTableWidgetItem(str(idx))
            sn_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 0, sn_item)

            file_no_item = QTableWidgetItem(sale.get("File No.", ""))
            file_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 1, file_no_item)

            customer_name_item = QTableWidgetItem(sale.get("Customer Name", ""))
            customer_name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 2, customer_name_item)

            village_item = QTableWidgetItem(sale.get("Village", ""))
            village_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 3, village_item)

            rs_block_item = QTableWidgetItem(sale.get("R.S.No./ Block No.", ""))
            rs_block_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 4, rs_block_item)

            new_no_item = QTableWidgetItem(sale.get("New No.", ""))
            new_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 5, new_no_item)

            old_no_item = QTableWidgetItem(sale.get("Old No.", ""))
            old_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 6, old_no_item)

            plot_no_item = QTableWidgetItem(sale.get("Plot No.", ""))
            plot_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 7, plot_no_item)

            work_types_item = QTableWidgetItem(", ".join(sale.get("Work Types", [])))
            work_types_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 8, work_types_item)

            work_status = sale.get("Work Status", "Pending")
            
            if work_status == "Approved":
                approved_label = QLabel("Approved")
                approved_label.setAlignment(Qt.AlignCenter)
                approved_label.setStyleSheet("""
                    QLabel {
                        color: #4CAF50;
                        font-weight: bold;
                    }
                """)
                self.table.setCellWidget(row_position, 9, approved_label)
            else:
                approve_button = QPushButton("Approve")
                approve_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                approve_button.clicked.connect(partial(self.approve_work, sale))
                self.table.setCellWidget(row_position, 9, approve_button)



    def approve_work(self, sale):
        """Approve the work for a given sale."""
        work_status = sale.get("Work Status", "Pending")
        if work_status != "Pending":
            QMessageBox.information(
                self,
                "Already Approved",
                f"Work for File No. {sale.get('File No.', '')} is already approved."
            )
            return

        reply = QMessageBox.question(
            self, "Confirm Approval",
            f"Are you sure you want to approve the work for File No. {sale.get('File No.', '')}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            sale["Work Status"] = "Approved"
            self.save_approvals()
            self.load_approvals()
            QMessageBox.information(self, "Success", f"Work for File No. {sale.get('File No.', '')} has been approved.")


    def save_approvals(self):
        """Save the current approval data back to data.json."""
        try:
            # Save the updated data
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.approvals, f, indent=4, ensure_ascii=False)
            
            # Upload to Google Drive
            github_sync.sync_file(self.data_file)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while saving approvals:\n{str(e)}")

    def apply_filter(self):
        """Filter the table based on the selected filters and search query."""
        selected_month = self.month_filter_combo.currentText()
        selected_year = self.year_filter_combo.currentText()
        selected_status = self.filter_combo.currentText()
        search_query = self.search_box.text().strip().lower()

        for row in range(self.table.rowCount()):
            sale = self.approvals[row]

            status = sale.get("Work Status", "Pending")
            status_match = (selected_status == "All") or (status == selected_status)

            month_match = True
            if selected_month != "All":
                sale_date_str = sale.get("Date", "")
                try:
                    sale_date_obj = datetime.strptime(sale_date_str, "%d/%m/%Y")
                    sale_month = sale_date_obj.strftime("%B")
                    month_match = (sale_month.lower() == selected_month.lower())
                except:
                    month_match = False

            year_match = True
            if selected_year != "All":
                sale_date_str = sale.get("Date", "")
                try:
                    sale_date_obj = datetime.strptime(sale_date_str, "%d/%m/%Y")
                    sale_year = str(sale_date_obj.year)
                    year_match = (sale_year == selected_year)
                except:
                    year_match = False

            if search_query:
                file_no = sale.get("File No.", "").lower()
                customer_name = sale.get("Customer Name", "").lower()
                village = sale.get("Village", "").lower()
                rs_block = sale.get("R.S.No./ Block No.", "").lower()
                new_no = sale.get("New No.", "").lower()
                old_no = sale.get("Old No.", "").lower()
                plot_no = sale.get("Plot No.", "").lower()
                search_match = (
                    search_query in file_no or
                    search_query in customer_name or
                    search_query in village or
                    search_query in rs_block or
                    search_query in new_no or
                    search_query in old_no or
                    search_query in plot_no
                )
            else:
                search_match = True

            match = status_match and month_match and year_match and search_match
            self.table.setRowHidden(row, not match)

# -------------------- Main Execution Block --------------------
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ApprovalModule()
    window.setWindowTitle("Work Approval Module")
    window.show()
    sys.exit(app.exec_())
