# related_cases.py

from PyQt5.QtCore import Qt, QDate, QStringListModel
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QDialog, QFormLayout, QDialogButtonBox, QComboBox,
    QLineEdit, QHeaderView, QAbstractItemView, QDateEdit, QFrame, QSpacerItem,
    QSizePolicy, QStyledItemDelegate, QCompleter, QGroupBox, QRadioButton,
    QCheckBox
)
from PyQt5.QtGui import QIcon, QDoubleValidator, QFont, QColor, QPixmap
import json
import os
from functools import partial

class RelatedCasesPaymentDialog(QDialog):
    """Dialog for managing payments across multiple related cases of the same party."""
    def __init__(self, all_cases, current_case, parent=None):
        super().__init__(parent)
        self.all_cases = all_cases  # All cases in the system
        self.current_case = current_case  # The case that was selected
        self.related_cases = []  # Will hold cases related to the current case
        
        self.setWindowTitle("Related Cases Payment Distribution")
        self.setGeometry(300, 300, 1000, 650)
        self.setStyleSheet("""
            QDialog {
                background-color: #fff6ee;
                border-radius: 15px;
            }
            QLabel {
                font-size: 16px;
                color: #564234;
            }
            QPushButton {
                font-size: 16px;
                padding: 8px 16px;
                border: none;
                border-radius: 8px;
                color: white;
                background-color: #ffa33e;
            }
            QPushButton:hover {
                background-color: #ff8c00;
            }
            QLineEdit, QDateEdit, QComboBox {
                font-size: 16px;
                padding: 6px;
                border: 1px solid #ffcea1;
                border-radius: 8px;
                background-color: #fffcfa;
            }
            QTableWidget {
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
            }
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #564234;
                border: 1px solid #ffcea1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        # Find related cases (same customer name and mobile number)
        self.find_related_cases()
        
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Related Cases Payment Distribution")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Search Bar with Auto-complete
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search Customer Name...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 1px solid #ffcea1;
                border-radius: 8px;
                background-color: #fffcfa;
            }
        """)
        
        # Setup auto-complete
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_box.setCompleter(self.completer)
        
        # Update completer model with customer names
        customer_names = list(set(case.get("Customer Name", "") for case in self.all_cases))
        self.completer.setModel(QStringListModel(customer_names))
        
        self.search_box.textChanged.connect(self.filter_cases)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        # Add search icon
        search_icon = QPushButton()
        search_icon.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "search_icon.svg")))
        search_icon.setFixedSize(30, 30)
        search_icon.setStyleSheet("""
            QPushButton {
                background-color: #ffa33e;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ff8c00;
            }
        """)
        search_layout.addWidget(search_icon)

        # Description
        description_label = QLabel("Manage payments across multiple cases for the same party")
        description_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(description_label)
        
        layout.addSpacing(10)

        # Party Information
        party_info_group = QGroupBox("Party Information")
        party_info_layout = QFormLayout()
        
        customer_name = self.current_case.get("Customer Name", "Unknown")
        mobile_number = self.current_case.get("Mobile Number", "Unknown")
        
        party_info_layout.addRow(QLabel(f"<b>Customer Name:</b> {customer_name}"))
        party_info_layout.addRow(QLabel(f"<b>Mobile Number:</b> {mobile_number}"))
        party_info_layout.addRow(QLabel(f"<b>Related Cases Found:</b> {len(self.related_cases)}"))
        
        party_info_group.setLayout(party_info_layout)
        layout.addWidget(party_info_group)

        # Cases Table
        cases_group = QGroupBox("Select Cases for Payment")
        cases_layout = QVBoxLayout()
        
        # Select All Checkbox
        self.select_all_checkbox = QCheckBox("Select All Cases")
        self.select_all_checkbox.toggled.connect(self.toggle_all_cases)
        cases_layout.addWidget(self.select_all_checkbox)
        
        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(7)
        self.cases_table.setHorizontalHeaderLabels(["Select", "File No.", "Customer Name", "Village", "Work Type", "Total Amount", "Remaining"])
        self.cases_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_cases_table()
        cases_layout.addWidget(self.cases_table)
        
        cases_group.setLayout(cases_layout)
        layout.addWidget(cases_group)

        # Payment Details Group
        payment_group = QGroupBox("Payment Details")
        payment_layout = QFormLayout()

        self.total_amount_edit = QLineEdit()
        self.total_amount_edit.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
        self.total_amount_edit.setPlaceholderText("Enter total payment amount")
        payment_layout.addRow("Total Amount:", self.total_amount_edit)

        self.payment_date_edit = QDateEdit()
        self.payment_date_edit.setCalendarPopup(True)
        self.payment_date_edit.setDate(QDate.currentDate())
        payment_layout.addRow("Payment Date:", self.payment_date_edit)

        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "UPI", "NEFT", "RTGS", "IMPS", "Cheque"])
        self.payment_method_combo.currentIndexChanged.connect(self.toggle_cheque_fields)
        payment_layout.addRow("Payment Method:", self.payment_method_combo)

        self.cheque_no_edit = QLineEdit()
        self.cheque_no_edit.setPlaceholderText("Cheque Number")
        self.cheque_no_edit.setVisible(False)
        payment_layout.addRow("Cheque No.:", self.cheque_no_edit)

        self.cheque_date_edit = QDateEdit()
        self.cheque_date_edit.setCalendarPopup(True)
        self.cheque_date_edit.setDate(QDate.currentDate())
        self.cheque_date_edit.setVisible(False)
        payment_layout.addRow("Cheque Date:", self.cheque_date_edit)

        payment_group.setLayout(payment_layout)
        layout.addWidget(payment_group)

        # Distribution Method
        distribution_group = QGroupBox("Distribution Method")
        distribution_layout = QVBoxLayout()

        self.proportional_radio = QRadioButton("Proportional to remaining amounts")
        self.proportional_radio.setChecked(True)
        distribution_layout.addWidget(self.proportional_radio)

        self.equal_radio = QRadioButton("Equal distribution")
        distribution_layout.addWidget(self.equal_radio)

        self.manual_radio = QRadioButton("Manual distribution")
        self.manual_radio.toggled.connect(self.enable_manual_distribution)
        distribution_layout.addWidget(self.manual_radio)

        distribution_group.setLayout(distribution_layout)
        layout.addWidget(distribution_group)

        # Buttons
        button_layout = QHBoxLayout()
        distribute_button = QPushButton("Distribute Payment")
        distribute_button.clicked.connect(self.distribute_payment)
        button_layout.addWidget(distribute_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def filter_cases(self):
        search_text = self.search_box.text().lower()
        for row in range(self.cases_table.rowCount()):
            file_no = self.cases_table.item(row, 1).text().lower()
            customer_name = self.cases_table.item(row, 2).text().lower()
            village = self.cases_table.item(row, 3).text().lower()
            work_type = self.cases_table.item(row, 4).text().lower()
            
            # Improved search logic with priority to customer name
            show_row = False
            if search_text in customer_name:  # First priority: Customer Name
                show_row = True
            elif search_text in file_no:  # Second priority: File No
                show_row = True
            elif search_text in village:  # Third priority: Village
                show_row = True
            elif search_text in work_type:  # Fourth priority: Work Type
                show_row = True
                
            self.cases_table.setRowHidden(row, not show_row)

    def find_related_cases(self):
        """Find cases with the same customer name and mobile number."""
        customer_name = self.current_case.get("Customer Name", "").strip().lower()
        mobile_number = self.current_case.get("Mobile Number", "").strip()
        
        # Always include the current case
        self.related_cases.append(self.current_case)
        
        for case in self.all_cases:
            case_name = case.get("Customer Name", "").strip().lower()
            case_mobile = case.get("Mobile Number", "").strip()
            
            if case.get("File No.") != self.current_case.get("File No.") and \
               ((customer_name and case_name == customer_name) or \
               (mobile_number and case_mobile == mobile_number)):
                self.related_cases.append(case)
        
        # Initialize filtered cases with all related cases
        self.filtered_cases = self.related_cases.copy()

    def filter_cases(self, text):
        """Filter cases based on search text."""
        search_text = text.lower().strip()
        if not search_text:
            self.filtered_cases = self.related_cases.copy()
        else:
            self.filtered_cases = [case for case in self.related_cases if
                search_text in case.get("Customer Name", "").lower() or
                search_text in case.get("File No.", "").lower() or
                search_text in case.get("Village", "").lower()]
        self.load_cases_table()

    def load_cases_table(self):
        """Populate the cases table with related cases."""
        self.cases_table.setRowCount(len(self.filtered_cases))
        
        for row, case in enumerate(self.filtered_cases):
            # Checkbox for selection
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Checked if case == self.current_case else Qt.Unchecked)
            self.cases_table.setItem(row, 0, checkbox)

            # Case details
            self.cases_table.setItem(row, 1, QTableWidgetItem(case.get("File No.", "")))
            self.cases_table.setItem(row, 2, QTableWidgetItem(case.get("Customer Name", "")))
            self.cases_table.setItem(row, 3, QTableWidgetItem(case.get("Village", "")))
            
            # Work Types (join with comma)
            work_types = ", ".join(case.get("Work Types", []))
            self.cases_table.setItem(row, 4, QTableWidgetItem(work_types))
            
            # Total Amount
            total_amount = float(case.get("Final Amount", 0.0))
            self.cases_table.setItem(row, 5, QTableWidgetItem(f"₹{total_amount:.2f}"))
            
            # Remaining Amount
            total_paid = sum(float(p["Amount Paid"]) for p in case.get("Payments", []))
            remaining = total_amount - total_paid
            self.cases_table.setItem(row, 6, QTableWidgetItem(f"₹{remaining:.2f}"))

    def toggle_all_cases(self, checked):
        """Toggle selection of all cases."""
        for row in range(self.cases_table.rowCount()):
            self.cases_table.item(row, 0).setCheckState(Qt.Checked if checked else Qt.Unchecked)

    def toggle_cheque_fields(self):
        """Show/hide cheque fields based on payment method."""
        is_cheque = self.payment_method_combo.currentText() == "Cheque"
        self.cheque_no_edit.setVisible(is_cheque)
        self.cheque_date_edit.setVisible(is_cheque)

    def enable_manual_distribution(self, enabled):
        """Add or remove the distribution amount column for manual distribution."""
        if enabled:
            # Add amount column for manual distribution
            if self.cases_table.columnCount() == 6:
                self.cases_table.insertColumn(6)
                self.cases_table.setHorizontalHeaderLabels(
                    ["Select", "File No.", "Village", "Work Type", "Total Amount", "Remaining", "Distribution Amount"])
                for row in range(self.cases_table.rowCount()):
                    amount_edit = QLineEdit()
                    amount_edit.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
                    self.cases_table.setCellWidget(row, 6, amount_edit)
        else:
            # Remove amount column if exists
            if self.cases_table.columnCount() == 7:
                self.cases_table.removeColumn(6)

    def distribute_payment(self):
        """Distribute the payment among selected cases."""
        total_amount = float(self.total_amount_edit.text() or 0)
        if total_amount <= 0:
            QMessageBox.warning(self, "Error", "Please enter a valid payment amount.")
            return

        selected_cases = []
        selected_rows = []
        total_remaining = 0

        for row in range(self.cases_table.rowCount()):
            if self.cases_table.item(row, 0).checkState() == Qt.Checked:
                remaining = float(self.cases_table.item(row, 5).text().replace('₹', ''))
                selected_cases.append(self.related_cases[row])
                selected_rows.append(row)
                total_remaining += remaining

        if not selected_cases:
            QMessageBox.warning(self, "Error", "Please select at least one case.")
            return

        distributions = {}

        if self.manual_radio.isChecked():
            # Manual distribution
            total_distributed = 0
            for row in selected_rows:
                amount_widget = self.cases_table.cellWidget(row, 6)
                if amount_widget:
                    try:
                        amount = float(amount_widget.text() or 0)
                        distributions[row] = amount
                        total_distributed += amount
                    except ValueError:
                        continue

            if abs(total_distributed - total_amount) > 0.01:
                QMessageBox.warning(self, "Error", "The sum of distributed amounts must equal the total payment amount.")
                return

        elif self.equal_radio.isChecked():
            # Equal distribution
            amount_per_case = total_amount / len(selected_cases)
            for row in selected_rows:
                distributions[row] = amount_per_case

        else:
            # Proportional distribution based on total amounts
            total_selected_amount = sum(float(self.cases_table.item(row, 4).text().replace('₹', '')) for row in selected_rows)
            total_distribution = 0
            for row in selected_rows:
                total_case_amount = float(self.cases_table.item(row, 4).text().replace('₹', ''))
                # Calculate proportion based on total amount
                proportion = total_case_amount / total_selected_amount if total_selected_amount > 0 else 0
                # Calculate distribution amount
                distribution_amount = total_amount * proportion
                distributions[row] = distribution_amount
                total_distribution += distribution_amount
            
            # If there's any remaining amount due to rounding
            remaining_amount = total_amount - total_distribution
            if remaining_amount > 0.01:  # If there's more than 1 paisa remaining
                for row in selected_rows:
                    if remaining_amount <= 0:
                        break
                    distributions[row] += remaining_amount / len(selected_rows)
                    remaining_amount = 0
                        
            # Display distribution details to user
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Payment Distribution Details")
            msg_text = "Payment distributed proportionally:\n\n"
            for row, amount in distributions.items():
                case = self.related_cases[row]
                total_case_amount = float(self.cases_table.item(row, 4).text().replace('₹', ''))
                msg_text += f"File No. {case.get('File No.', '')}: ₹{amount:.2f} ({amount/total_case_amount*100:.1f}% of total)\n"
            msg.setText(msg_text)
            msg.exec_()
                        
            # Display distribution details to user
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Payment Distribution Details")
            msg_text = "Payment distributed proportionally:\n\n"
            for row, amount in distributions.items():
                case = self.related_cases[row]
                msg_text += f"File No. {case.get('File No.', '')}: ₹{amount:.2f} ({amount/float(self.cases_table.item(row, 5).text().replace('₹', ''))*100:.1f}% of remaining)\n"
            msg.setText(msg_text)
            msg.exec_()

        # Create payment records
        payment_date = self.payment_date_edit.date().toString("dd/MM/yyyy")
        payment_method = self.payment_method_combo.currentText()
        cheque_no = self.cheque_no_edit.text() if payment_method == "Cheque" else ""
        cheque_date = self.cheque_date_edit.date().toString("dd/MM/yyyy") if payment_method == "Cheque" else ""

        # Generate a unique relationship ID for this batch of payments
        relationship_id = f"rel_{payment_date.replace('/', '')}_{payment_method}"
        
        # Update payments for each case
        for row, amount in distributions.items():
            payment = {
                "Amount Paid": f"{amount:.2f}",
                "Payment Date": payment_date,
                "Payment Method": payment_method,
                "Cheque No.": cheque_no,
                "Cheque Date": cheque_date,
                "Relationship ID": relationship_id,  # Add relationship ID to track related payments
                "Related Payment": True  # Flag to identify related payments
            }
            self.related_cases[row].setdefault("Payments", []).append(payment)

        self.accept()