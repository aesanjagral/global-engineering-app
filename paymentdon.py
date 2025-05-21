# paymentdon.py

from PyQt5.QtCore import Qt, QDate, QStringListModel
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QDialog, QFormLayout, QDialogButtonBox, QComboBox,
    QLineEdit, QHeaderView, QAbstractItemView, QDateEdit, QFrame, QSpacerItem,
    QSizePolicy, QStyledItemDelegate, QCompleter
)
from PyQt5.QtGui import QFont, QIcon
from github_sync import github_sync
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from functools import partial


class PaymentDoneModule(QWidget):
    def __init__(self):
        super().__init__()

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

        # Define the icons path
        self.icons_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Icons')

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header Layout
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)

        # Header Label
        header_label = QLabel("Payment Done Management")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setFont(QFont("Century Gothic", 20, QFont.Bold))
        header_label.setStyleSheet("color: #7e5d47;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Refresh Button
        self.refresh_button = QPushButton()
        refresh_icon_path = os.path.join(self.icons_folder, 'refresh.svg')
        if os.path.exists(refresh_icon_path):
            self.refresh_button.setIcon(QIcon(refresh_icon_path))
        self.refresh_button.setToolTip("Refresh Data")
        self.refresh_button.setFixedSize(30, 30)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #ffa33e;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ff8c00;
            }
        """)
        self.refresh_button.clicked.connect(self.load_payments)
        header_layout.addWidget(self.refresh_button)

        # Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by File No. or Date...")
        self.search_box.setFixedWidth(250)
        self.search_box.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                background-color: #fffcfa;
            }
        """)
        self.search_box.textChanged.connect(self.apply_filter)

        # Add completer for search
        self.search_completer = QCompleter()
        self.search_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_box.setCompleter(self.search_completer)
        self.search_box.textChanged.connect(self.update_search_completer)

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

        # Year Filter ComboBox
        self.year_filter_combo = QComboBox()
        self.year_filter_combo.addItem("All Years")
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

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(10)

        # Payment Done Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)  # Added Action column
        self.table.setHorizontalHeaderLabels([
            "SN", "File No.", "Customer Name", "Mobile No.", "R.S.No./ Block No.",
            "New No.", "Old No.", "Plot No.", "Work Type", "Payment Status", "Action"
        ])
        
        # Set column widths
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # SN
        self.table.setColumnWidth(0, 40)
        
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)  # File No.
        self.table.setColumnWidth(1, 90)
        
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Customer Name
        
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)  # Mobile No.
        self.table.setColumnWidth(3, 120)

        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)  # R.S.No./ Block No.
        self.table.setColumnWidth(4, 120)

        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)  # New No.
        self.table.setColumnWidth(5, 80)

        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)  # Old No.
        self.table.setColumnWidth(6, 80)

        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)  # Plot No.
        self.table.setColumnWidth(7, 80)
        
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)  # Work Type
        self.table.setColumnWidth(8, 200)
        
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)  # Payment Status
        self.table.setColumnWidth(9, 140)
        
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)  # Action
        self.table.setColumnWidth(10, 120)
        
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
        self.load_payments()

    def load_payments(self):
        if not os.path.exists(self.data_file):
            QMessageBox.warning(self, "No Data", "No payment data found.")
            self.payments = []
            self.display_payments(self.payments)
            return

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.payments = json.load(f)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to decode JSON. Please check the data.json file.")
            self.payments = []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading payments:\n{str(e)}")
            self.payments = []

        self.display_payments(self.payments)

    def display_payments(self, payments):
        self.table.setRowCount(0)
        filtered_payments = [
            payment for payment in payments
            if payment.get("Payment Status", "").lower() == "completed" and
               payment.get("Work Status", "").lower() == "approved" and
               payment.get("Payment Prrovel status", "").lower() != "done"
        ]

        for idx, payment in enumerate(filtered_payments, start=1):
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

            # Customer Name
            customer_name_item = QTableWidgetItem(payment.get("Customer Name", ""))
            customer_name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 2, customer_name_item)

            # Mobile No.
            mobile_no_item = QTableWidgetItem(payment.get("Mobile Number", ""))
            mobile_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 3, mobile_no_item)

            # R.S.No./ Block No.
            rs_block_item = QTableWidgetItem(payment.get("R.S.No./ Block No.", ""))
            rs_block_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 4, rs_block_item)

            # New No.
            new_no_item = QTableWidgetItem(payment.get("New No.", ""))
            new_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 5, new_no_item)

            # Old No.
            old_no_item = QTableWidgetItem(payment.get("Old No.", ""))
            old_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 6, old_no_item)

            # Plot No.
            plot_no_item = QTableWidgetItem(payment.get("Plot No.", ""))
            plot_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 7, plot_no_item)

            # Work Type
            work_types = payment.get("Work Types", [])
            work_types_str = ", ".join(work_types) if isinstance(work_types, list) else str(work_types)
            work_type_item = QTableWidgetItem(work_types_str)
            work_type_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 8, work_type_item)

            # Payment Status
            status_item = QTableWidgetItem(payment.get("Payment Status", ""))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 9, status_item)

            # Action Button
            action_button = QPushButton("Mark as Done")
            if payment.get("Payment Prrovel status", "").lower() == "done":
                action_button.setText("Done")
                action_button.setEnabled(False)  # Disable the button if already done
                action_button.setStyleSheet("""
                    QPushButton {
                        background-color: #808080; /* Grayed out color */
                        color: white;
                        border-radius: 5px;
                        font-size: 14px;
                    }
                """)
            else:
                action_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 5px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
            action_button.clicked.connect(partial(self.mark_as_done, payment))
            self.table.setCellWidget(row_position, 10, action_button)

    def mark_as_done(self, payment):
        if payment.get("Payment Prrovel status", "").lower() == "done":
            QMessageBox.information(
                self, "Already Done",
                f"Payment for File No. {payment.get('File No.', '')} is already marked as done."
            )
            return

        reply = QMessageBox.question(
            self, "Confirm Mark as Done",
            f"Are you sure you want to mark the payment for File No. {payment.get('File No.', '')} as Done?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            payment["Payment Prrovel status"] = "done"
            self.save_payments()
            self.load_payments()
            QMessageBox.information(self, "Success", f"Payment for File No. {payment.get('File No.', '')} has been marked as Done.")

    def save_payments(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.payments, f, indent=4, ensure_ascii=False)
            
            # Upload to GitHub
            github_sync.sync_file(self.data_file)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {str(e)}")
            return False

    def apply_filter(self):
        selected_month = self.month_filter_combo.currentText()
        selected_year = self.year_filter_combo.currentText()
        search_query = self.search_box.text().strip().lower()

        if not os.path.exists(self.data_file):
            self.payments = []
        else:
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.payments = json.load(f)
            except:
                self.payments = []

        filtered_payments = [
            payment for payment in self.payments
            if payment.get("Payment Status", "").lower() == "completed" and
               payment.get("Work Status", "").lower() == "approved" and
               payment.get("Payment Prrovel status", "").lower() != "done"
        ]

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
        """Get month name from date string"""
        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            return date_obj.strftime("%B")
        except ValueError:
            return ""

    def get_year(self, date_str):
        """Get year from date string"""
        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            return str(date_obj.year)
        except ValueError:
            return ""

    def update_search_completer(self, text):
        """Update search completer suggestions based on input text"""
        if not text:
            self.search_completer.setModel(None)
            return

        suggestions = []
        if hasattr(self, 'payments'):
            for entry in self.payments:
                fields = [
                    entry.get("File No.", ""),
                    entry.get("Customer Name", ""),
                    entry.get("Mobile Number", ""),
                    entry.get("Village", "")
                ]
                
                # Handle Work Types separately to avoid potential errors
                work_types = entry.get("Work Types", [])
                if isinstance(work_types, list):
                    fields.append(", ".join(work_types))
                else:
                    fields.append(str(work_types))
                
                # Add matching fields to suggestions
                for field in fields:
                    if text.lower() in str(field).lower():
                        suggestions.append(str(field))

        # Remove duplicates and sort
        unique_suggestions = sorted(list(set(suggestions)))
        model = QStringListModel(unique_suggestions)
        self.search_completer.setModel(model)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = PaymentDoneModule()
    window.setWindowTitle("Payment Done Management")
    window.resize(1200, 700)
    window.show()
    sys.exit(app.exec_())
