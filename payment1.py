# payment.py

from PyQt5.QtCore import Qt, QDate, QStringListModel
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QDialog, QFormLayout, QDialogButtonBox, QComboBox,
    QLineEdit, QHeaderView, QAbstractItemView, QDateEdit, QFrame, QSpacerItem,
    QSizePolicy, QStyledItemDelegate, QCompleter, QGroupBox, QRadioButton
)
from PyQt5.QtGui import QIcon, QDoubleValidator, QFont, QColor, QPixmap
import json
import os
from functools import partial
from datetime import datetime
import sys
import shutil
from pathlib import Path
from github_sync import github_sync
from related_cases import RelatedCasesPaymentDialog
from activity_tracker import ActivityTracker

class PaymentStatusPopup(QDialog):
    """Popup dialog to manage payment status and multiple payments."""
    def __init__(self, sale, parent=None):
        super().__init__(parent)
        self.activity_tracker = ActivityTracker()
        self.sale = sale  # The sale record being modified
        self.setWindowTitle("Manage Payment Status")
        self.setGeometry(300, 300, 900, 500)
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
                background-color:rgb(77, 235, 195);
            }
            QPushButton:hover {
                background-color:rgb(69, 160, 114);
            }
            QLineEdit, QDateEdit, QComboBox {
                font-size: 16px;
                padding: 6px;
                border: 1px solid #ffcea1;
                border-radius: 8px;
                background-color: #fffcfa;
            }
            QTableWidget {
                background-color: #cccccc;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #ffa33e;
                color: white;
                font-size: 16px;
                padding: 4px;
            }
        """)

        self.total_amount = float(self.sale.get('Final Amount', 0.0))
        self.payments = self.sale.get("Payments", [])
        self.sale['related_cases'] = self.sale.get('related_cases', [])  # Initialize related cases

        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Payment Status Management")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(10)

        # Summary Section
        summary_layout = QHBoxLayout()

        self.total_amount_label = QLabel(f"Total Amount Due: ₹{self.total_amount:.2f}")
        self.total_amount_label.setFont(QFont("Arial", 14))
        summary_layout.addWidget(self.total_amount_label)

        self.total_paid_label = QLabel(f"Total Paid: ₹{self.get_total_paid():.2f}")
        self.total_paid_label.setFont(QFont("Arial", 14))
        summary_layout.addWidget(self.total_paid_label)

        self.remaining_amount_label = QLabel(f"Remaining: ₹{self.get_remaining_amount():.2f}")
        self.remaining_amount_label.setFont(QFont("Arial", 14))
        summary_layout.addWidget(self.remaining_amount_label)

        layout.addLayout(summary_layout)

        layout.addSpacing(10)

        # Payments Table
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(7)
        self.payments_table.setHorizontalHeaderLabels([
            "Amount Paid", "Payment Date", "Payment Method", "Narration", "Cheque No.", "Cheque Date", "Actions"
        ])
        
        # Set column widths
        self.payments_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # Amount Paid
        self.payments_table.setColumnWidth(0, 100)
        
        self.payments_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)  # Payment Date
        self.payments_table.setColumnWidth(1, 100)
        
        self.payments_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)  # Payment Method
        self.payments_table.setColumnWidth(2, 120)
        
        self.payments_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)  # Narration
        self.payments_table.setColumnWidth(3, 200)  # Increased width for Narration
        
        self.payments_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)  # Cheque No.
        self.payments_table.setColumnWidth(4, 100)
        
        self.payments_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)  # Cheque Date
        self.payments_table.setColumnWidth(5, 100)
        
        self.payments_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)  # Actions
        self.payments_table.setColumnWidth(6, 120)
        
        self.payments_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.payments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.payments_table.verticalHeader().setVisible(False)  # Hide vertical header        
        self.payments_table.setShowGrid(False)  # Hide all grid lines
        self.payments_table.setStyleSheet("""
            QTableWidget {
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #ffe9d7;
                color: #d17a24;
                padding: 4px;
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
                text-align: center; /* Center-align text */
            }
            QTableWidget::item:selected {
                background-color: #ffcea1;
                color: #ffffff;
            }
        """)

        # Set the default row height here
        self.payments_table.verticalHeader().setDefaultSectionSize(40)  # Row height set to 40 pixels
        self.load_payments_table()
        layout.addWidget(self.payments_table)

        layout.addSpacing(10)

        # Add Payment Section
        add_payment_group = QFrame()
        add_payment_group.setStyleSheet("""
            QFrame {
                background-color: #fff6ee;
                border-radius: 10px;
            }
        """)
        add_payment_layout = QHBoxLayout()

        self.new_payment_amount_edit = QLineEdit()
        self.new_payment_amount_edit.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
        self.new_payment_amount_edit.setPlaceholderText("Amount Paid (₹)")
        self.new_payment_amount_edit.setToolTip("Enter the amount paid by the customer.")
        add_payment_layout.addWidget(self.new_payment_amount_edit)

        self.new_payment_date_edit = QDateEdit()
        self.new_payment_date_edit.setCalendarPopup(True)
        self.new_payment_date_edit.setDate(QDate.currentDate())
        self.new_payment_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.new_payment_date_edit.setToolTip("Select the payment date.")
        add_payment_layout.addWidget(self.new_payment_date_edit)

        # Payment Method ComboBox
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "UPI", "NEFT", "RTGS", "IMPS", "Cheque"])
        self.payment_method_combo.setToolTip("Select the payment method.")
        self.payment_method_combo.currentIndexChanged.connect(self.toggle_cheque_fields)
        add_payment_layout.addWidget(self.payment_method_combo)

        # Narration Input
        self.narration_edit = QLineEdit()
        self.narration_edit.setPlaceholderText("Narration")
        self.narration_edit.setToolTip("Enter payment narration/description.")
        add_payment_layout.addWidget(self.narration_edit)

        # Cheque No. Input
        self.cheque_no_edit = QLineEdit()
        self.cheque_no_edit.setPlaceholderText("Cheque No.")
        self.cheque_no_edit.setToolTip("Enter the Cheque Number if applicable.")
        self.cheque_no_edit.setVisible(False)
        add_payment_layout.addWidget(self.cheque_no_edit)

        # Cheque Date Input
        self.cheque_date_edit = QDateEdit()
        self.cheque_date_edit.setCalendarPopup(True)
        self.cheque_date_edit.setDate(QDate.currentDate())
        self.cheque_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.cheque_date_edit.setToolTip("Select the Cheque Date.")
        self.cheque_date_edit.setVisible(False)
        add_payment_layout.addWidget(self.cheque_date_edit)

        add_payment_button = QPushButton("Add Payment")
        add_payment_button.setStyleSheet("""
            QPushButton {
                background-color: #ffa33e;
            }
            QPushButton:hover {
                background-color: #ff8c00;
            }
        """)
        add_payment_button.clicked.connect(self.add_payment)
        add_payment_layout.addWidget(add_payment_button)

        add_payment_group.setLayout(add_payment_layout)
        layout.addWidget(add_payment_group)

        layout.addSpacing(10)

        # Action Buttons
        action_buttons_layout = QHBoxLayout()
        
        # Add Related Cases Payment button
        related_cases_button = QPushButton("Related Cases Payment")
        related_cases_button.setStyleSheet("""
            QPushButton {
                background-color: #FFA33E;
            }
            QPushButton:hover {
                background-color: #FF8C00;
            }
        """)
        related_cases_button.clicked.connect(self.open_related_cases_payment)
        action_buttons_layout.addWidget(related_cases_button)
        
        action_buttons_layout.addStretch()

        save_button = QPushButton("Save")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #44C694;
            }
            QPushButton:hover {
                background-color: #35AA7B;
            }
        """)
        save_button.clicked.connect(self.save_and_close)
        action_buttons_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        action_buttons_layout.addWidget(cancel_button)

        layout.addLayout(action_buttons_layout)

        self.setLayout(layout)

    def get_total_paid(self):
        return sum(float(payment["Amount Paid"]) for payment in self.payments)

    def get_remaining_amount(self):
        return self.total_amount - self.get_total_paid()

    def load_payments_table(self):
        """Populate the payments table with current payments."""
        self.payments_table.setRowCount(len(self.payments))
        for row, payment in enumerate(self.payments):
            amount_item = QTableWidgetItem(f"₹{float(payment['Amount Paid']):.2f}")
            amount_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 0, amount_item)

            date_item = QTableWidgetItem(payment['Payment Date'])
            date_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 1, date_item)

            method_item = QTableWidgetItem(payment.get('Payment Method', 'Other'))
            method_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 2, method_item)

            # Narration
            narration_item = QTableWidgetItem(payment.get('Narration', ''))
            narration_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 3, narration_item)

            # Cheque No.
            cheque_no = payment.get('Cheque No.', '')
            cheque_no_item = QTableWidgetItem(cheque_no if cheque_no else "-")
            cheque_no_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 4, cheque_no_item)

            # Cheque Date
            cheque_date = payment.get('Cheque Date', '')
            cheque_date_item = QTableWidgetItem(cheque_date if cheque_date else "-")
            cheque_date_item.setTextAlignment(Qt.AlignCenter)
            self.payments_table.setItem(row, 5, cheque_date_item)

            # Actions (Edit and Delete)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setAlignment(Qt.AlignCenter)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            edit_button = QPushButton("Edit")
            edit_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff9800;
                    color: white;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #e68900;
                }
            """)
            edit_button.clicked.connect(lambda checked, row=row: self.edit_payment(row))
            actions_layout.addWidget(edit_button)

            delete_button = QPushButton("Delete")
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            delete_button.clicked.connect(lambda checked, row=row: self.delete_payment(row))
            actions_layout.addWidget(delete_button)

            actions_widget.setLayout(actions_layout)
            self.payments_table.setCellWidget(row, 6, actions_widget)  # Action column

        # Update the summary labels in the popup
        self.update_summary_labels()

    def toggle_cheque_fields(self, index):
        method = self.payment_method_combo.currentText()
        if method == "Cheque":
            self.cheque_no_edit.setVisible(True)
            self.cheque_date_edit.setVisible(True)
        else:
            self.cheque_no_edit.setVisible(False)
            self.cheque_date_edit.setVisible(False)

    def add_payment(self):
        """Add a new payment entry"""
        try:
            # Validate input fields
            amount_text = self.new_payment_amount_edit.text().strip()
            payment_date = self.new_payment_date_edit.date().toString("dd/MM/yyyy")
            payment_method = self.payment_method_combo.currentText()
            narration = self.narration_edit.text().strip()
            cheque_no = self.cheque_no_edit.text().strip()
            cheque_date = self.cheque_date_edit.date().toString("dd/MM/yyyy") if payment_method == "Cheque" else ""

            # Input validation
            if not amount_text:
                QMessageBox.warning(self, "Input Error", "Please enter the amount paid.")
                return False

            if payment_method == "Cheque":
                if not cheque_no:
                    QMessageBox.warning(self, "Input Error", "Please enter the Cheque No.")
                    return False
                if not cheque_date:
                    QMessageBox.warning(self, "Input Error", "Please enter the Cheque Date.")
                    return False

            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Please enter a valid positive amount.")
                return False

            # Check if payment date is not in future
            current_date = QDate.currentDate()
            payment_date_obj = QDate.fromString(payment_date, "dd/MM/yyyy")
            if payment_date_obj > current_date:
                QMessageBox.warning(self, "Input Error", "Payment date cannot be in the future.")
                return False

            # Check if total payment exceeds final amount
            total_paid = self.get_total_paid()
            if total_paid + amount > self.total_amount:
                reply = QMessageBox.question(
                    self, 
                    "Overpayment Warning",
                    f"This payment will exceed the total amount of ₹{self.total_amount:.2f}. Do you want to continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return False

            # Create new payment record
            new_payment = {
                "Amount Paid": f"{amount:.2f}",
                "Payment Date": payment_date,
                "Payment Method": payment_method,
                "Narration": narration,
                "Cheque No.": cheque_no if payment_method == "Cheque" else "",
                "Cheque Date": cheque_date if payment_method == "Cheque" else "",
                "Status": "Completed"
            }

            # Append the new payment
            self.payments.append(new_payment)

            # Handle related cases
            if 'related_cases' in self.sale:
                relationship_id = f"rel_{payment_date.replace('/', '')}_{payment_method}"
                new_payment['Relationship ID'] = relationship_id
                
                parent = self.parent()
                for file_no in self.sale['related_cases']:
                    for case in parent.payments:
                        if case.get('File No.') == file_no:
                            case.setdefault('Payments', []).append(new_payment.copy())
                            break

            # Update UI
            self.load_payments_table()
            self.clear_input_fields()
            self.update_summary_labels()

            # Log activity
            payment_details = f"Added payment of ₹{amount:.2f} via {payment_method} for {self.sale.get('Customer Name', 'Unknown')}"
            self.activity_tracker.log_activity("Payment", "Added", payment_details)
            
            # Refresh dashboard
            main_window = self.window()
            if hasattr(main_window, 'dashboard'):
                main_window.dashboard.load_activities()

            # Save changes using parent's save_payments method
            parent = self.parent()
            parent.save_payments()
            
            QMessageBox.information(self, "Success", "Payment added successfully!")
            return True

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
            return False

    def edit_payment(self, row):
        """Edit an existing payment"""
        try:
            payment = self.payments[row]
            dialog = EditPaymentDialog(payment, self)
            if dialog.exec_() == QDialog.Accepted:
                self.payments[row] = dialog.payment
                self.load_payments_table()

                # Update summary labels
                self.update_summary_labels()

                # Log the activity
                payment_details = f"Modified payment of ₹{float(payment['Amount Paid']):.2f} via {payment['Payment Method']} for {self.sale.get('Customer Name', 'Unknown')}"
                self.activity_tracker.log_activity("Payment", "Modified", payment_details)
                
                # Refresh the dashboard if it exists
                main_window = self.window()
                if hasattr(main_window, 'dashboard'):
                    main_window.dashboard.load_activities()
                
                return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit payment: {str(e)}")
            return False

    def delete_payment(self, row):
        """Delete a payment from the list."""
        if row < 0 or row >= len(self.payments):
            QMessageBox.warning(self, "Error", "Invalid payment row selected.")
            return

        payment = self.payments[row]
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the payment of ₹{float(payment.get('Amount Paid', 0)):.2f}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Get payment details before deleting
            payment_details = f"Deleted payment of ₹{float(payment.get('Amount Paid', 0)):.2f} for {self.sale.get('Customer Name', 'Unknown')}"
            
            # Delete the payment
            del self.payments[row]
            
            # Update the table
            self.load_payments_table()
            
            # Update summary labels
            self.update_summary_labels()
            
            # Log the activity
            self.activity_tracker.log_activity("Payment", "Delete", payment_details)
            
            QMessageBox.information(self, "Success", "Payment deleted successfully.")

    def open_related_cases_payment(self):
        dialog = RelatedCasesPaymentDialog(self.parent().payments, self.sale, self.parent())
        if dialog.exec_() == QDialog.Accepted:
            self.load_payments_table()
            self.parent().load_payments()

    def save_and_close(self):
        self.accept()

    def update_summary_labels(self):
        """Update the summary labels with the computed totals."""
        self.total_amount_label.setText(f"Total Amount Due: ₹{self.total_amount:.2f}")
        self.total_paid_label.setText(f"Total Paid: ₹{self.get_total_paid():.2f}")
        self.remaining_amount_label.setText(f"Remaining: ₹{self.get_remaining_amount():.2f}")

    def clear_input_fields(self):
        """Clear all input fields after successful payment addition"""
        self.new_payment_amount_edit.clear()
        self.new_payment_date_edit.setDate(QDate.currentDate())
        self.payment_method_combo.setCurrentIndex(0)
        self.narration_edit.clear()
        self.cheque_no_edit.clear()
        self.cheque_no_edit.setVisible(False)
        self.cheque_date_edit.setDate(QDate.currentDate())
        self.cheque_date_edit.setVisible(False)

class EditPaymentDialog(QDialog):
    """Dialog to edit an existing payment."""
    def __init__(self, payment, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Payment")
        self.payment = payment.copy()  # Create a copy to modify
        self.setGeometry(350, 350, 500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #fff;
                border-radius: 15px;
            }
            QLabel {
                font-size: 16px;
                color: #333333;
            }
            QPushButton {
                font-size: 16px;
                padding: 8px 16px;
                border: none;
                border-radius: 8px;
                color: white;
                background-color: #4CAF50;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit, QDateEdit, QComboBox {
                font-size: 16px;
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
        """)

        layout = QFormLayout()

        # Amount Paid
        self.amount_edit = QLineEdit()
        self.amount_edit.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
        self.amount_edit.setText(self.payment.get("Amount Paid", ""))
        layout.addRow("Amount Paid (₹):", self.amount_edit)

        # Payment Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        try:
            date_obj = datetime.strptime(self.payment.get("Payment Date", "01/01/2000"), "%d/%m/%Y")
            self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
        except ValueError:
            self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        layout.addRow("Payment Date:", self.date_edit)

        # Payment Method
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "UPI", "NEFT", "RTGS", "IMPS", "Cheque"])
        current_method = self.payment.get("Payment Method", "Cash")
        index = self.payment_method_combo.findText(current_method)
        if index != -1:
            self.payment_method_combo.setCurrentIndex(index)
        self.payment_method_combo.currentIndexChanged.connect(self.toggle_cheque_fields)
        layout.addRow("Payment Method:", self.payment_method_combo)

        # Narration
        self.narration_edit = QLineEdit()
        self.narration_edit.setPlaceholderText("Narration")
        self.narration_edit.setText(self.payment.get("Narration", ""))
        layout.addRow("Narration:", self.narration_edit)

        # Cheque No.
        self.cheque_no_edit = QLineEdit()
        self.cheque_no_edit.setPlaceholderText("Cheque No.")
        self.cheque_no_edit.setText(self.payment.get("Cheque No.", ""))
        if self.payment.get("Payment Method", "") == "Cheque":
            self.cheque_no_edit.setVisible(True)
        else:
            self.cheque_no_edit.setVisible(False)
        layout.addRow("Cheque No.:", self.cheque_no_edit)

        # Cheque Date
        self.cheque_date_edit = QDateEdit()
        self.cheque_date_edit.setCalendarPopup(True)
        try:
            date_obj = datetime.strptime(self.payment.get("Cheque Date", "01/01/2000"), "%d/%m/%Y")
            self.cheque_date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
        except ValueError:
            self.cheque_date_edit.setDate(QDate.currentDate())
        self.cheque_date_edit.setDisplayFormat("dd/MM/yyyy")
        if self.payment.get("Payment Method", "") == "Cheque":
            self.cheque_date_edit.setVisible(True)
        else:
            self.cheque_date_edit.setVisible(False)
        layout.addRow("Cheque Date:", self.cheque_date_edit)

        # Dialog Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_changes)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def toggle_cheque_fields(self, index):
        method = self.payment_method_combo.currentText()
        if method == "Cheque":
            self.cheque_no_edit.setVisible(True)
            self.cheque_date_edit.setVisible(True)
        else:
            self.cheque_no_edit.setVisible(False)
            self.cheque_date_edit.setVisible(False)

    def save_changes(self):
        amount_text = self.amount_edit.text().strip()
        payment_date = self.date_edit.date().toString("dd/MM/yyyy")
        payment_method = self.payment_method_combo.currentText()
        narration = self.narration_edit.text().strip()
        cheque_no = self.cheque_no_edit.text().strip()
        cheque_date = self.cheque_date_edit.date().toString("dd/MM/yyyy") if payment_method == "Cheque" else ""

        if not amount_text:
            QMessageBox.warning(self, "Input Error", "Please enter the amount paid.")
            return

        if payment_method == "Cheque":
            if not cheque_no:
                QMessageBox.warning(self, "Input Error", "Please enter the Cheque No.")
                return
            if not cheque_date:
                QMessageBox.warning(self, "Input Error", "Please enter the Cheque Date.")
                return

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid positive amount.")
            return

        # Update payment details
        self.payment["Amount Paid"] = f"{amount:.2f}"
        self.payment["Payment Date"] = payment_date
        self.payment["Payment Method"] = payment_method
        self.payment["Narration"] = narration
        self.payment["Cheque No."] = cheque_no if payment_method == "Cheque" else ""
        self.payment["Cheque Date"] = cheque_date if payment_method == "Cheque" else ""
        # Removed the following line to ensure "Work Status" is not modified
        # self.payment["Status"] = "Completed" if payment_method else "Pending"

        self.accept()

class BatchPaymentDialog(QDialog):
    def __init__(self, cases, parent=None):
        super().__init__(parent)
        self.cases = cases
        self.setWindowTitle("Batch Payment Distribution")
        self.setGeometry(300, 300, 1000, 600)
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
        """)

        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Batch Payment Distribution")
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
        customer_names = list(set(case.get("Customer Name", "") for case in self.cases))
        self.completer.setModel(QStringListModel(customer_names))
        
        self.search_box.textChanged.connect(self.filter_cases)
        search_layout.addWidget(self.search_box)

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
        layout.addLayout(search_layout)

        # Summary Labels
        summary_layout = QHBoxLayout()
        self.total_due_label = QLabel("Total Amount Due: ₹0")
        self.total_paid_label = QLabel("Total Paid: ₹0")
        self.total_remaining_label = QLabel("Total Remaining: ₹0")
        summary_layout.addWidget(self.total_due_label)
        summary_layout.addWidget(self.total_paid_label)
        summary_layout.addWidget(self.total_remaining_label)
        layout.addLayout(summary_layout)

        # Cases Table
        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(5)
        self.cases_table.setHorizontalHeaderLabels(["Select", "File No.", "Customer Name", "Total Amount", "Remaining"])
        self.cases_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_cases_table()
        layout.addWidget(self.cases_table)

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
        payment_layout.addRow("Payment Method:", self.payment_method_combo)

        # Narration Input
        self.narration_edit = QLineEdit()
        self.narration_edit.setPlaceholderText("Enter payment narration")
        payment_layout.addRow("Narration:", self.narration_edit)

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

        # Connect signals
        self.payment_method_combo.currentIndexChanged.connect(self.toggle_cheque_fields)
        self.manual_radio.toggled.connect(self.enable_manual_distribution)

    def load_cases_table(self):
        self.cases_table.setRowCount(len(self.cases))
        for row, case in enumerate(self.cases):
            # Checkbox for selection
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Unchecked)
            self.cases_table.setItem(row, 0, checkbox)

            # Case details
            self.cases_table.setItem(row, 1, QTableWidgetItem(case.get("File No.", "")))
            self.cases_table.setItem(row, 2, QTableWidgetItem(case.get("Customer Name", "")))
            
            total_amount = float(case.get("Final Amount", 0.0))
            self.cases_table.setItem(row, 3, QTableWidgetItem(f"₹{total_amount:.2f}"))
            
            total_paid = sum(float(p["Amount Paid"]) for p in case.get("Payments", []))
            remaining = total_amount - total_paid
            self.cases_table.setItem(row, 4, QTableWidgetItem(f"₹{remaining:.2f}"))
            
        # Connect itemChanged signal to update summary
        self.cases_table.itemChanged.connect(self.update_summary)
        # Initial summary update
        self.update_summary()
        
    def update_summary(self, item=None):
        total_due = 0
        total_paid = 0
        total_remaining = 0

        for row in range(self.cases_table.rowCount()):
            checkbox_item = self.cases_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                # Get total amount
                total_amount_str = self.cases_table.item(row, 3).text().replace('₹', '')
                total_amount = float(total_amount_str)
                total_due += total_amount

                # Get remaining amount
                remaining_str = self.cases_table.item(row, 4).text().replace('₹', '')
                remaining = float(remaining_str)
                total_remaining += remaining

        # Calculate total paid
        total_paid = total_due - total_remaining

        # Update labels
        self.total_due_label.setText(f"Total Amount Due: ₹{total_due:,.2f}")
        self.total_paid_label.setText(f"Total Paid: ₹{total_paid:,.2f}")
        self.total_remaining_label.setText(f"Total Remaining: ₹{total_remaining:,.2f}")

    def toggle_cheque_fields(self):
        is_cheque = self.payment_method_combo.currentText() == "Cheque"
        self.cheque_no_edit.setVisible(is_cheque)
        self.cheque_date_edit.setVisible(is_cheque)

    def enable_manual_distribution(self, enabled):
        if enabled:
            # Add amount column for manual distribution
            if self.cases_table.columnCount() == 5:
                self.cases_table.insertColumn(5)
                self.cases_table.setHorizontalHeaderLabels(
                    ["Select", "File No.", "Customer Name", "Total Amount", "Remaining", "Distribution Amount"])
                for row in range(self.cases_table.rowCount()):
                    amount_edit = QLineEdit()
                    amount_edit.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
                    self.cases_table.setCellWidget(row, 5, amount_edit)
        else:
            # Remove amount column if exists
            if self.cases_table.columnCount() == 6:
                self.cases_table.removeColumn(5)

    def filter_cases(self):
        """Filter cases based on search text."""
        search_text = self.search_box.text().lower()
        for row in range(self.cases_table.rowCount()):
            file_no = self.cases_table.item(row, 1).text().lower()
            customer_name = self.cases_table.item(row, 2).text().lower()
            
            # Show row if search text matches file number or customer name
            show_row = search_text in file_no or search_text in customer_name
            self.cases_table.setRowHidden(row, not show_row)

    def distribute_payment(self):
        total_amount = float(self.total_amount_edit.text() or 0)
        if total_amount <= 0:
            QMessageBox.warning(self, "Error", "Please enter a valid payment amount.")
            return

        selected_cases = []
        selected_rows = []
        total_remaining = 0

        for row in range(self.cases_table.rowCount()):
            if self.cases_table.item(row, 0).checkState() == Qt.Checked:
                remaining = float(self.cases_table.item(row, 4).text().replace('₹', ''))
                selected_cases.append(self.cases[row])
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
                amount_widget = self.cases_table.cellWidget(row, 5)
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
            # Proportional distribution
            for row in selected_rows:
                remaining = float(self.cases_table.item(row, 4).text().replace('₹', ''))
                proportion = remaining / total_remaining
                distributions[row] = total_amount * proportion

        # Create payment records
        payment_date = self.payment_date_edit.date().toString("dd/MM/yyyy")
        payment_method = self.payment_method_combo.currentText()
        narration = self.narration_edit.text().strip()
        cheque_no = self.cheque_no_edit.text() if payment_method == "Cheque" else ""
        cheque_date = self.cheque_date_edit.date().toString("dd/MM/yyyy") if payment_method == "Cheque" else ""

        # Update payments for each case
        for row, amount in distributions.items():
            payment = {
                "Amount Paid": f"{amount:.2f}",
                "Payment Date": payment_date,
                "Payment Method": payment_method,
                "Narration": narration,
                "Cheque No.": cheque_no,
                "Cheque Date": cheque_date,
                "Batch Payment": True  # Flag to identify batch payments
            }
            self.cases[row].setdefault("Payments", []).append(payment)

        self.accept()

class PaymentModule(QWidget):
    def __init__(self):
        super().__init__()
        self.activity_tracker = ActivityTracker()
        
        # Define the icons path
        self.icons_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Icons')

        # Initialize Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Payment Management")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFA33E;")
        header_layout.addWidget(header_label)

        # Spacer to push the filters to the right
        header_layout.addStretch()

        # Load Payments Button
        load_button = QPushButton("Load Payments")
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
        load_button.clicked.connect(self.load_payments)
        header_layout.addWidget(load_button)

        # Add Batch Payment button
        batch_payment_button = QPushButton("Batch Payment")
        batch_payment_button.setFixedSize(150, 40)
        batch_payment_button.setStyleSheet("""
            QPushButton {
                background-color: #44C694;
                border: none;
                color: white;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #35AA7B;
            }
        """)
        batch_payment_button.clicked.connect(self.open_batch_payment)
        header_layout.addWidget(batch_payment_button)

        # Search Box
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

        # Add completer for search
        self.search_completer = QCompleter()
        self.search_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_box.setCompleter(self.search_completer)
        self.search_box.textChanged.connect(self.update_search_completer)

        header_layout.addWidget(self.search_box)

        # Month Filter ComboBox
        self.month_filter_combo = QComboBox()
        self.month_filter_combo.addItem("All")
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

        # Year Filter ComboBox (Fixed from 2020 to 2040)
        self.year_filter_combo = QComboBox()
        self.year_filter_combo.addItem("All")
        self.year_filter_combo.addItems([str(year) for year in range(2020, 2041)])  # 2020 to 2040 inclusive
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

        # Payment Status Filter ComboBox
        self.filter_combo = QComboBox()
        self.filter_combo.addItem(QIcon(os.path.join(self.icons_folder, 'filter.svg')), "All")
        self.filter_combo.addItem(QIcon(os.path.join(self.icons_folder, 'pending.svg')), "Pending")
        self.filter_combo.addItem(QIcon(os.path.join(self.icons_folder, 'half_paid.svg')), "Half Paid")
        self.filter_combo.addItem(QIcon(os.path.join(self.icons_folder, 'completed.svg')), "Completed")
        self.filter_combo.addItem(QIcon(os.path.join(self.icons_folder, 'overpayment.svg')), "Overpayment")
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

        # Payments Table
        self.table = QTableWidget()
        self.table.setColumnCount(15)  # SN, File No., Date, Customer Name, Work Type, Village, R.S.No./ Block No., New No., Old No., Plot No., Total Amount, Paid Payment, Remaining Amount, Payment Status, Action
        self.table.setHorizontalHeaderLabels([
            "SN", "File No.", "Date", "Customer Name", "Work Type", "Village",
            "R.S.No./ Block No.", "New No.", "Old No.", "Plot No.", "Total Amount",
            "Paid Payment", "Remaining", "Payment Status", "Action"
        ])
        
        # Enable word wrap for all items
        self.table.setWordWrap(True)
        
        # Set column widths
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # SN
        self.table.setColumnWidth(0, 40)
        
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)  # File No.
        self.table.setColumnWidth(1, 80)
        
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)  # Date
        self.table.setColumnWidth(2, 90)
        
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # Customer Name
        
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)  # Work Type
        self.table.setColumnWidth(4, 140)
        
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)  # Village
        self.table.setColumnWidth(5, 80)
        
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)  # R.S.No./ Block No.
        self.table.setColumnWidth(6, 140)
        
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)  # New No.
        self.table.setColumnWidth(7, 85)
        
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)  # Old No.
        self.table.setColumnWidth(8, 85)
        
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)  # Plot No.
        self.table.setColumnWidth(9, 85)
        
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)  # Total Amount
        self.table.setColumnWidth(10, 100)
        
        self.table.horizontalHeader().setSectionResizeMode(11, QHeaderView.Fixed)  # Paid Payment
        self.table.setColumnWidth(11, 100)
        
        self.table.horizontalHeader().setSectionResizeMode(12, QHeaderView.Fixed)  # Remaining Amount
        self.table.setColumnWidth(12, 90)
        
        self.table.horizontalHeader().setSectionResizeMode(13, QHeaderView.Fixed)  # Payment Status
        self.table.setColumnWidth(13, 100)
        
        self.table.horizontalHeader().setSectionResizeMode(14, QHeaderView.Fixed)  # Action
        self.table.setColumnWidth(14, 130)
        
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)  # Hide vertical header
        self.table.setShowGrid(False)  # Hide all grid lines
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
                padding: 3px;
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
        # Set minimum row height
        self.table.verticalHeader().setDefaultSectionSize(40)
        main_layout.addWidget(self.table)

        # -------------------- Added Summary Section Start --------------------
        main_layout.addSpacing(2)  # Add spacing before the summary

        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #fff6ee;
                border-radius: 10px;
            }
        """)
        summary_layout = QVBoxLayout()

        # Top Horizontal Line
        line_top = QFrame()
        line_top.setFrameShape(QFrame.HLine)
        line_top.setFrameShadow(QFrame.Sunken)
        summary_layout.addWidget(line_top)

        # Summary Content
        summary_content = QHBoxLayout()
        summary_content.setSpacing(5)

        # Total Pending
        pending_layout = QVBoxLayout()
        pending_label = QLabel("Total Pending")
        pending_label.setFont(QFont("Arial", 10,))
        pending_label.setAlignment(Qt.AlignCenter)
        pending_label.setStyleSheet("color: #ffa33e;")  # Title color
        self.total_pending_label = QLabel("₹0.00")
        self.total_pending_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_pending_label.setAlignment(Qt.AlignCenter)
        self.total_pending_label.setStyleSheet("color: #d17a24;")  # Value color
        pending_layout.addWidget(pending_label)
        pending_layout.addWidget(self.total_pending_label)
        summary_content.addLayout(pending_layout)

        # Vertical Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        summary_content.addWidget(separator1)

        # Total Halfpaid
        halfpaid_layout = QVBoxLayout()
        halfpaid_label = QLabel("Total Halfpaid")
        halfpaid_label.setFont(QFont("Arial", 10))
        halfpaid_label.setAlignment(Qt.AlignCenter)
        halfpaid_label.setStyleSheet("color: #ffa33e;")  # Title color
        self.total_halfpaid_label = QLabel("₹0.00")
        self.total_halfpaid_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_halfpaid_label.setAlignment(Qt.AlignCenter)
        self.total_halfpaid_label.setStyleSheet("color: #d17a24;")  # Value color
        halfpaid_layout.addWidget(halfpaid_label)
        halfpaid_layout.addWidget(self.total_halfpaid_label)
        summary_content.addLayout(halfpaid_layout)

        # Vertical Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        summary_content.addWidget(separator2)

        # Total Completed
        completed_layout = QVBoxLayout()
        completed_label = QLabel("Total Completed")
        completed_label.setFont(QFont("Arial", 10, QFont.Bold))
        completed_label.setAlignment(Qt.AlignCenter)
        completed_label.setStyleSheet("color: #ffa33e;")  # Title color
        self.total_completed_label = QLabel("₹0.00")
        self.total_completed_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_completed_label.setAlignment(Qt.AlignCenter)
        self.total_completed_label.setStyleSheet("color: #d17a24;")  # Value color
        completed_layout.addWidget(completed_label)
        completed_layout.addWidget(self.total_completed_label)
        summary_content.addLayout(completed_layout)

        # Vertical Separator
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.VLine)
        separator3.setFrameShadow(QFrame.Sunken)
        summary_content.addWidget(separator3)

        # Total Amount
        amount_layout = QVBoxLayout()
        amount_label = QLabel("Total Amount")
        amount_label.setFont(QFont("Arial", 10))
        amount_label.setAlignment(Qt.AlignCenter)
        amount_label.setStyleSheet("color: #ffa33e;")  # Title color
        self.total_amount_label_bottom = QLabel("₹0.00")
        self.total_amount_label_bottom.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_amount_label_bottom.setAlignment(Qt.AlignCenter)
        self.total_amount_label_bottom.setStyleSheet("color: #d17a24;")  # Value color
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.total_amount_label_bottom)
        summary_content.addLayout(amount_layout)

        # Vertical Separator
        separator4 = QFrame()
        separator4.setFrameShape(QFrame.VLine)
        separator4.setFrameShadow(QFrame.Sunken)
        summary_content.addWidget(separator4)

        # Total Remaining Payment
        remaining_layout = QVBoxLayout()
        remaining_label = QLabel("Total Remaining Payment")
        remaining_label.setFont(QFont("Arial", 10))
        remaining_label.setAlignment(Qt.AlignCenter)
        remaining_label.setStyleSheet("color: #ffa33e;")  # Title color
        self.total_remaining_label = QLabel("₹0.00")
        self.total_remaining_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_remaining_label.setAlignment(Qt.AlignCenter)
        self.total_remaining_label.setStyleSheet("color: #d17a24;")  # Value color
        remaining_layout.addWidget(remaining_label)
        remaining_layout.addWidget(self.total_remaining_label)
        summary_content.addLayout(remaining_layout)

        summary_layout.addLayout(summary_content)

        # Bottom Horizontal Line
        line_bottom = QFrame()
        line_bottom.setFrameShape(QFrame.HLine)
        line_bottom.setFrameShadow(QFrame.Sunken)
        summary_layout.addWidget(line_bottom)

        summary_frame.setLayout(summary_layout)
        main_layout.addWidget(summary_frame)
        # -------------------- Added Summary Section End --------------------

        self.setLayout(main_layout)

        # Define the default data folder and file path
        self.user_data_folder = os.path.join(str(Path.home()), '.my_app_data')
        self.data_file = os.path.join(self.user_data_folder, 'data.json')

        # Create user data folder if it doesn't exist
        os.makedirs(self.user_data_folder, exist_ok=True)

        # If running from PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Download files from Drive if they don't exist
            if not os.path.exists(self.data_file):
                github_sync.download_file('data.json', self.data_file)

        # Load data initially
        self.load_payments()

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

        # Ensure Payment Status is updated based on payments
        # Initialize related cases for relationship tracking
        for sale in self.payments:
            sale.setdefault('related_cases', [])

        self.update_all_payment_statuses()

        self.display_payments(self.payments)
        self.update_summary()  # Update the summary after loading payments

    def update_all_payment_statuses(self):
        """Update Payment Status for all sales based on their payments."""
        for sale in self.payments:
            total_paid = sum(float(p["Amount Paid"]) for p in sale.get("Payments", []))
            final_amount = sale.get("Final Amount", "0.0")
            if not final_amount or final_amount.strip() == '' or final_amount.strip() == '-':
                final_amount = "0.0"
            try:
                total_amount = float(final_amount)
            except ValueError:
                total_amount = 0.0
            if total_paid == 0:
                sale["Payment Status"] = "Pending"
            elif 0 < total_paid < total_amount:
                sale["Payment Status"] = "Half Paid"
            elif total_paid > total_amount:
                sale["Payment Status"] = "Overpayment"
            else:
                sale["Payment Status"] = "Completed"

    def display_payments(self, payments):
        """Display payment data in the table."""
        self.table.setRowCount(0)  # Clear existing data

        for idx, sale in enumerate(payments, start=1):
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            # SN
            sn_item = QTableWidgetItem(str(idx))
            sn_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 0, sn_item)

            # File No.
            file_no_item = QTableWidgetItem(sale.get("File No.", ""))
            file_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 1, file_no_item)

            # Date (Using sale's "Date" field)
            sale_date = sale.get("Date", "N/A")
            date_item = QTableWidgetItem(sale_date)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 2, date_item)

            # Customer Name
            customer_name_item = QTableWidgetItem(sale.get("Customer Name", ""))
            customer_name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 3, customer_name_item)

            # Work Type
            work_type_item = QTableWidgetItem(", ".join(sale.get("Work Types", [])))
            work_type_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 4, work_type_item)

            # Village
            village_item = QTableWidgetItem(sale.get("Village", ""))
            village_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 5, village_item)

            # R.S.No./ Block No.
            rs_block_item = QTableWidgetItem(sale.get("R.S.No./ Block No.", ""))
            rs_block_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 6, rs_block_item)

            # New No.
            new_no_item = QTableWidgetItem(sale.get("New No.", ""))
            new_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 7, new_no_item)

            # Old No.
            old_no_item = QTableWidgetItem(sale.get("Old No.", ""))
            old_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 8, old_no_item)

            # Plot No.
            plot_no_item = QTableWidgetItem(sale.get("Plot No.", ""))
            plot_no_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 9, plot_no_item)

            # Total Amount
            final_amount = sale.get('Final Amount', "0.0")
            if not final_amount or final_amount.strip() == '' or final_amount.strip() == '-':
                final_amount = "0.0"
            try:
                total_amount = float(final_amount)
            except ValueError:
                total_amount = 0.0
            total_amount_item = QTableWidgetItem(f"₹{total_amount:,.2f}")
            total_amount_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 10, total_amount_item)

            # Paid Payment
            paid_payment = sum(float(p["Amount Paid"]) for p in sale.get("Payments", []))
            paid_payment_item = QTableWidgetItem(f"₹{paid_payment:,.2f}")
            paid_payment_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 11, paid_payment_item)

            # Remaining Amount
            remaining_amount = total_amount - paid_payment
            remaining_amount_item = QTableWidgetItem(f"₹{remaining_amount:,.2f}")
            remaining_amount_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_position, 12, remaining_amount_item)

            # Payment Status with color coding
            status = sale.get("Payment Status", "Pending")
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            
            if status == "Pending":
                color = QColor("#FF0000")  # Red
            elif status == "Half Paid":
                color = QColor("#FF9800")  # Orange
            elif status == "Overpayment":
                color = QColor("#FF0000")  # Red
            else:
                color = QColor("#4CAF50")  # Green
                
            status_item.setBackground(color)
            status_item.setForeground(QColor("#FFFFFF"))  # White text
            self.table.setItem(row_position, 13, status_item)

            # Action Buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setAlignment(Qt.AlignCenter)
            action_layout.setContentsMargins(0, 0, 0, 0)

            # Manage Payment Button
            manage_payment_btn = QPushButton("Manage Payment")
            manage_payment_btn.setFixedSize(140, 30)
            manage_payment_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFA33E;
                    border: none;
                    color: white;
                    font-size: 12px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #FF8C00;
                }
            """)
            manage_payment_btn.clicked.connect(partial(self.open_payment_status_popup, sale))
            action_layout.addWidget(manage_payment_btn)

            action_widget.setLayout(action_layout)
            self.table.setCellWidget(row_position, 14, action_widget)  # Action column

            # Adjust row height based on content
            self.table.resizeRowToContents(row_position)

        # Update the summary labels in the popup
        self.update_summary_labels()

    def open_payment_status_popup(self, sale):
        """Open the PaymentStatusPopup dialog for the given sale."""
        dialog = PaymentStatusPopup(sale, self)
        if dialog.exec_() == QDialog.Accepted:
            # Update the sale's payments
            self.update_sale_payments(sale, dialog.payments)
            self.save_payments()
            self.load_payments()
            QMessageBox.information(self, "Success", "Payment details have been updated successfully.")

    def update_sale_payments(self, sale, updated_payments):
        """Update the payments for a specific sale."""
        sale['Payments'] = updated_payments
        # Update Payment Status based on updated payments
        total_paid = sum(float(p["Amount Paid"]) for p in updated_payments)
        total_amount = float(sale.get("Final Amount", 0.0))
        if total_paid == 0:
            sale["Payment Status"] = "Pending"
        elif 0 < total_paid < total_amount:
            sale["Payment Status"] = "Half Paid"
        elif total_paid > total_amount:
            sale["Payment Status"] = "Overpayment"
        else:
            sale["Payment Status"] = "Completed"
        # Ensure "Work Status" is not modified

    def save_payments(self):
        """Save the current payment data back to data.json."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.payments, f, indent=4, ensure_ascii=False)
            
            # Sync with GitHub
            github_sync.sync_file(self.data_file)
            return True
        except Exception as e:
            print(f"Error saving data: {str(e)}")
            return False

    def update_search_completer(self, text):
        """Update search completer suggestions"""
        if not text:
            self.search_completer.setModel(None)
            return

        suggestions = []
        for sale in self.payments:
            fields = [
                sale.get("File No.", ""),
                sale.get("Customer Name", ""),
                sale.get("Mobile Number", ""),
                sale.get("Village", ""),
                ", ".join(sale.get("Work Types", [])).lower()
            ]
            
            for field in fields:
                if text.lower() in str(field).lower():
                    suggestions.append(str(field))

        # Remove duplicates and sort
        unique_suggestions = sorted(list(set(suggestions)))
        model = QStringListModel(unique_suggestions)
        self.search_completer.setModel(model)

    def apply_filter(self):
        """Filter the table based on the selected filters and search query."""
        selected_month = self.month_filter_combo.currentText()
        selected_year = self.year_filter_combo.currentText()
        selected_status = self.filter_combo.currentText()
        search_query = self.search_box.text().strip().lower()

        for row in range(self.table.rowCount()):
            # Get sale data from the loaded payments
            sale = self.payments[row]

            # Filter by Payment Status
            status = sale.get("Payment Status", "Pending")
            status_match = (selected_status == "All") or (status == selected_status)

            # Filter by Month
            month_match = True
            if selected_month != "All":
                # Use sale's "Date" field
                sale_date_str = sale.get("Date", "")
                try:
                    sale_date_obj = datetime.strptime(sale_date_str, "%d/%m/%Y")
                    sale_month = sale_date_obj.strftime("%B")
                    if sale_month.lower() == selected_month.lower():
                        month_match = True
                    else:
                        month_match = False
                except:
                    month_match = False

            # Filter by Year
            year_match = True
            if selected_year != "All":
                # Use sale's "Date" field
                sale_date_str = sale.get("Date", "")
                try:
                    sale_date_obj = datetime.strptime(sale_date_str, "%d/%m/%Y")
                    sale_year = str(sale_date_obj.year)
                    if sale_year == selected_year:
                        year_match = True
                    else:
                        year_match = False
                except:
                    year_match = False

            # Filter by Search Query
            if search_query:
                # Search in File No., Customer Name, Mobile No., Village, Work Type
                file_no = sale.get("File No.", "").lower()
                customer_name = sale.get("Customer Name", "").lower()
                mobile_no = sale.get("Mobile Number", "").lower()
                village = sale.get("Village", "").lower()
                work_types = ", ".join(sale.get("Work Types", [])).lower()
                # Date is already considered in month/year filters
                search_match = (
                    search_query in file_no or
                    search_query in customer_name or
                    search_query in mobile_no or
                    search_query in village or
                    search_query in work_types
                )
            else:
                search_match = True

            # Determine if the row should be shown
            match = status_match and month_match and year_match and search_match
            self.table.setRowHidden(row, not match)

        # Update the summary based on filtered data
        self.update_summary()

    # -------------------- Added Summary Methods Start --------------------
    def compute_totals(self):
        """Compute the total pending, halfpaid, completed amounts and total amount based on visible rows."""
        total_pending = 0.0
        total_halfpaid = 0.0
        total_completed = 0.0
        total_amount = 0.0
        total_remaining_payment = 0.0

        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            sale = self.payments[row]
            final_amount = sale.get('Final Amount', "0.0")
            if not final_amount or final_amount.strip() == '' or final_amount.strip() == '-':
                final_amount = "0.0"
            try:
                final_amount = float(final_amount)
            except ValueError:
                final_amount = 0.0
            total_amount += final_amount
            payment_status = sale.get('Payment Status', 'Pending')
            paid_payment = sum(float(p["Amount Paid"]) for p in sale.get("Payments", []))
            remaining = final_amount - paid_payment

            if payment_status == "Pending":
                total_pending += remaining
                total_remaining_payment += remaining
            elif payment_status == "Half Paid":
                total_halfpaid += paid_payment  # Show only the paid amount for Half Paid
                total_remaining_payment += remaining
            elif payment_status == "Completed":
                total_completed += final_amount

        return total_pending, total_halfpaid, total_completed, total_amount, total_remaining_payment

    def format_currency(self, amount):
        """Format the amount with comma separators and two decimal places."""
        return f"₹{amount:,.2f}"

    def update_summary_labels(self):
        """Update the summary labels with the computed totals."""
        total_pending, total_halfpaid, total_completed, total_amount, total_remaining_payment = self.compute_totals()
        self.total_pending_label.setText(self.format_currency(total_pending))
        self.total_halfpaid_label.setText(self.format_currency(total_halfpaid))
        self.total_completed_label.setText(self.format_currency(total_completed))
        self.total_amount_label_bottom.setText(self.format_currency(total_amount))
        self.total_remaining_label.setText(self.format_currency(total_remaining_payment))

    def update_summary(self):
        """Update the summary labels with the computed totals."""
        self.update_summary_labels()
    # -------------------- Added Summary Methods End --------------------

    def toggle_cheque_fields(self, index):
        """Show or hide cheque fields based on the payment method."""
        method = self.payment_method_combo.currentText()
        if method == "Cheque":
            self.cheque_no_edit.setVisible(True)
            self.cheque_date_edit.setVisible(True)
        else:
            self.cheque_no_edit.setVisible(False)
            self.cheque_date_edit.setVisible(False)

    def add_payment(self):
        """Add a new payment entry"""
        try:
            # Validate input fields
            amount_text = self.new_payment_amount_edit.text().strip()
            payment_date = self.new_payment_date_edit.date().toString("dd/MM/yyyy")
            payment_method = self.payment_method_combo.currentText()
            narration = self.narration_edit.text().strip()
            cheque_no = self.cheque_no_edit.text().strip()
            cheque_date = self.cheque_date_edit.date().toString("dd/MM/yyyy") if payment_method == "Cheque" else ""

            # Input validation
            if not amount_text:
                QMessageBox.warning(self, "Input Error", "Please enter the amount paid.")
                return False

            if payment_method == "Cheque":
                if not cheque_no:
                    QMessageBox.warning(self, "Input Error", "Please enter the Cheque No.")
                    return False
                if not cheque_date:
                    QMessageBox.warning(self, "Input Error", "Please enter the Cheque Date.")
                    return False

            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Please enter a valid positive amount.")
                return False

            # Check if payment date is not in future
            current_date = QDate.currentDate()
            payment_date_obj = QDate.fromString(payment_date, "dd/MM/yyyy")
            if payment_date_obj > current_date:
                QMessageBox.warning(self, "Input Error", "Payment date cannot be in the future.")
                return False

            # Check if total payment exceeds final amount
            total_paid = self.get_total_paid()
            if total_paid + amount > self.total_amount:
                reply = QMessageBox.question(
                    self, 
                    "Overpayment Warning",
                    f"This payment will exceed the total amount of ₹{self.total_amount:.2f}. Do you want to continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return False

            # Create new payment record
            new_payment = {
                "Amount Paid": f"{amount:.2f}",
                "Payment Date": payment_date,
                "Payment Method": payment_method,
                "Narration": narration,
                "Cheque No.": cheque_no if payment_method == "Cheque" else "",
                "Cheque Date": cheque_date if payment_method == "Cheque" else "",
                "Status": "Completed"
            }

            # Append the new payment
            self.payments.append(new_payment)

            # Handle related cases
            if 'related_cases' in self.sale:
                relationship_id = f"rel_{payment_date.replace('/', '')}_{payment_method}"
                new_payment['Relationship ID'] = relationship_id
                
                parent = self.parent()
                for file_no in self.sale['related_cases']:
                    for case in parent.payments:
                        if case.get('File No.') == file_no:
                            case.setdefault('Payments', []).append(new_payment.copy())
                            break

            # Update UI
            self.load_payments_table()
            self.clear_input_fields()
            self.update_summary_labels()

            # Log activity
            payment_details = f"Added payment of ₹{amount:.2f} via {payment_method} for {self.sale.get('Customer Name', 'Unknown')}"
            self.activity_tracker.log_activity("Payment", "Added", payment_details)
            
            # Refresh dashboard
            main_window = self.window()
            if hasattr(main_window, 'dashboard'):
                main_window.dashboard.load_activities()

            # Save changes using parent's save_payments method
            parent = self.parent()
            parent.save_payments()
            
            QMessageBox.information(self, "Success", "Payment added successfully!")
            return True

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
            return False

    def clear_input_fields(self):
        """Clear all input fields after successful payment addition"""
        self.new_payment_amount_edit.clear()
        self.new_payment_date_edit.setDate(QDate.currentDate())
        self.payment_method_combo.setCurrentIndex(0)
        self.narration_edit.clear()
        self.cheque_no_edit.clear()
        self.cheque_no_edit.setVisible(False)
        self.cheque_date_edit.setDate(QDate.currentDate())
        self.cheque_date_edit.setVisible(False)

    def delete_payment(self, row):
        """Delete a payment from the list."""
        if row < 0 or row >= len(self.payments):
            QMessageBox.warning(self, "Error", "Invalid payment row selected.")
            return

        payment = self.payments[row]
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the payment of ₹{float(payment.get('Amount Paid', 0)):.2f}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Get payment details before deleting
            payment_details = f"Deleted payment of ₹{float(payment.get('Amount Paid', 0)):.2f} for {self.sale.get('Customer Name', 'Unknown')}"
            
            # Delete the payment
            del self.payments[row]
            
            # Update the table
            self.load_payments_table()
            
            # Update summary labels
            self.update_summary_labels()
            
            # Log the activity
            self.activity_tracker.log_activity("Payment", "Delete", payment_details)
            
            QMessageBox.information(self, "Success", "Payment deleted successfully.")

    def get_total_paid(self):
        """Get total amount paid for the current sale."""
        if hasattr(self, 'sale'):
            return sum(float(payment["Amount Paid"]) for payment in self.sale.get("Payments", []))
        return 0.0

    def update_payment_status(self):
        """Update the Payment Status of the sale based on total payments."""
        total_paid = self.get_total_paid()
        if hasattr(self, 'sale') and hasattr(self, 'total_amount'):
            if total_paid == 0:
                self.sale["Payment Status"] = "Pending"
            elif 0 < total_paid < self.total_amount:
                self.sale["Payment Status"] = "Half Paid"
            elif total_paid > self.total_amount:
                self.sale["Payment Status"] = "Overpayment"
            else:
                self.sale["Payment Status"] = "Completed"

    def save_and_close(self):
        """Save the changes and close the dialog."""
        self.accept()

    def open_batch_payment(self):
        # Create and show the batch payment dialog directly with all payments
        dialog = BatchPaymentDialog(self.payments, self)
        if dialog.exec_() == QDialog.Accepted:
            # Save the updated payments
            self.save_payments()
            # Reload the payments to refresh the display
            self.load_payments()
            QMessageBox.information(self, "Success", "Batch payment has been processed successfully.")
