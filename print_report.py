import sys
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from github_sync import github_sync

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea, QSpacerItem, QSizePolicy,
    QFileDialog, QCompleter, QMessageBox, QDialog, QCheckBox
)
from PyQt5.QtCore import Qt, QSize, QRect, QSizeF, QStringListModel
from PyQt5.QtGui import QFont, QPainter, QPdfWriter, QColor, QPen, QTextOption


class CaseSelectionDialog(QDialog):
    def __init__(self, cases):
        super().__init__()
        self.cases = cases
        self.selected_indices = []
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Select Cases')
        self.setMinimumWidth(400)
        layout = QVBoxLayout()
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QFrame()
        scroll_content_layout = QVBoxLayout()
        
        # Add checkboxes for each case
        self.checkboxes = []
        for idx, case in enumerate(self.cases):
            file_no = case.get('File No.', f'Case {idx + 1}')  # Get File No. or use Case number as fallback
            checkbox = QCheckBox(file_no)
            checkbox.setFont(QFont("Century Gothic", 10))
            self.checkboxes.append(checkbox)
            scroll_content_layout.addWidget(checkbox)
        
        scroll_content.setLayout(scroll_content_layout)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QVBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.setFont(QFont("Century Gothic", 10))
        select_all_btn.clicked.connect(self.selectAll)
        btn_layout.addWidget(select_all_btn)
        
        generate_btn = QPushButton("Generate PDF")
        generate_btn.setFont(QFont("Century Gothic", 10))
        generate_btn.clicked.connect(self.accept)
        btn_layout.addWidget(generate_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def selectAll(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)
    
    def getSelectedIndices(self):
        return [i for i, cb in enumerate(self.checkboxes) if cb.isChecked()]

class PrintReportModule(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Print Report Module")
        self.setStyleSheet("background-color: #FFF6EE;")
        self.resize(1300, 750)

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

        self.data = []
        self.filtered_data = []
        self.current_selected_record = None  

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # SCROLL AREA
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)

        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
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
        main_layout.addWidget(scroll_area)

        # TOP AREA: Title + [Refresh, Print]
        top_area_layout = QHBoxLayout()
        top_area_layout.setSpacing(10)

        title_label = QLabel("Print Detail Report")
        title_label.setFont(QFont("Century Gothic", 20, QFont.Bold))
        title_label.setStyleSheet("color: #7e5d47;")
        top_area_layout.addWidget(title_label)
        top_area_layout.addStretch()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFCFA;
                border: 1px solid #FFE3CC;
                border-radius: 5px;
                padding: 5px 10px;
                font-family: 'Century Gothic';
            }
            QPushButton:hover {
                background-color: #FFEDE1;
            }
        """)
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        top_area_layout.addWidget(self.refresh_button)

        self.sync_button = QPushButton("Refresh to Sync")
        self.sync_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFCFA;
                border: 1px solid #FFE3CC;
                border-radius: 5px;
                padding: 5px 10px;
                font-family: 'Century Gothic';
            }
            QPushButton:hover {
                background-color: #FFEDE1;
            }
        """)
        self.sync_button.clicked.connect(self.refresh_data)
        top_area_layout.addWidget(self.sync_button)

        self.print_button = QPushButton("Print Generate")
        self.print_button.setStyleSheet("""
            QPushButton {
                background-color: #7b614f;
                border: none;
                color: white;
                font-size: 14px;
                border-radius: 5px;
                padding: 8px 16px;
                font-family: 'Century Gothic';
            }
            QPushButton:hover {
                background-color: #6d5442;
            }
        """)
        self.print_button.clicked.connect(self.showCaseSelection)
        top_area_layout.addWidget(self.print_button)
        
        self.batch_button = QPushButton("Batch Payment")
        self.batch_button.setStyleSheet("""
            QPushButton {
                background-color: #7b614f;
                border: none;
                color: white;
                font-size: 14px;
                border-radius: 5px;
                padding: 8px 16px;
                font-family: 'Century Gothic';
            }
            QPushButton:hover {
                background-color: #6d5442;
            }
        """)
        self.batch_button.clicked.connect(self.on_batch_payment)
        top_area_layout.addWidget(self.batch_button)

        content_layout.addLayout(top_area_layout)

        # SECOND ROW: Search + Filters
        filter_row_layout = QHBoxLayout()
        filter_row_layout.setSpacing(10)

        # Search boxes
        self.search_customer_input = QLineEdit()
        self.search_customer_input.setPlaceholderText("Search by Customer Name...")
        self.search_customer_input.setStyleSheet("""
            QLineEdit {
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                padding: 6px 10px;
                font-family: 'Century Gothic';
            }
        """)
        self.search_customer_input.textChanged.connect(self.on_filter_triggered)
        
        self.search_all_input = QLineEdit()
        self.search_all_input.setPlaceholderText("Search in all data...")
        self.search_all_input.setStyleSheet("""
            QLineEdit {
                background-color: #fffcfa;
                border: 1px solid #ffcea1;
                border-radius: 5px;
                padding: 6px 10px;
                font-family: 'Century Gothic';
            }
        """)
        self.search_all_input.textChanged.connect(self.on_filter_triggered)
        
        # Add completer for customer name search
        self.customer_completer = QCompleter()
        self.customer_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_customer_input.setCompleter(self.customer_completer)
        
        # Add completer for all data search
        self.all_completer = QCompleter()
        self.all_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_all_input.setCompleter(self.all_completer)

        # Connect text changed signals
        self.search_customer_input.textChanged.connect(self.update_customer_completer)
        self.search_all_input.textChanged.connect(self.update_all_completer)
        
        filter_row_layout.addWidget(self.search_customer_input, 2)
        filter_row_layout.addWidget(self.search_all_input, 2)

        filter_row_layout.addStretch()

        self.month_combo = QComboBox()
        self.month_combo.setStyleSheet("""
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
                image: url("./icons/dropdown_arrow.svg");
                width: 10px;
                height: 10px;
            }
        """)
        self.month_combo.setFixedWidth(130)
        self.month_combo.addItem("All")
        self.month_combo.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        filter_row_layout.addWidget(self.month_combo)

        self.year_combo = QComboBox()
        self.year_combo.setStyleSheet("""
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
        self.year_combo.setFixedWidth(100)
        self.year_combo.addItem("All")
        for y in range(2020, 2036):
            self.year_combo.addItem(str(y))
        filter_row_layout.addWidget(self.year_combo)

        self.filter_button = QPushButton("Filter")
        self.filter_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFCFA;
                border: 1px solid #FFE3CC;
                border-radius: 5px;
                padding: 5px 10px;
                font-family: 'Century Gothic';
            }
            QPushButton:hover {
                background-color: #FFEDE1;
            }
        """)
        self.filter_button.clicked.connect(self.on_filter_triggered)
        filter_row_layout.addWidget(self.filter_button)

        content_layout.addLayout(filter_row_layout)

        # TABLE
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(11)
        self.report_table.setHorizontalHeaderLabels([
            "File No.", "Date", "R.S.No./Block No.", "New No.", "Old No.", "Plot No.",
            "Work Type", "Village", "Final Amount", "Paid Amount", "View"
        ])
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.report_table.verticalHeader().setDefaultSectionSize(40)
        self.report_table.setAlternatingRowColors(False)
        self.report_table.verticalHeader().setVisible(False)
        self.report_table.setShowGrid(False)
        self.report_table.setStyleSheet("""
            QTableWidget {
                background-color: #fffefd;
                border: 0px solid #ffcea1;
                border-radius: 10px;                
                font-family: 'Century Gothic';
            }
            QHeaderView::section {
                background-color: #fffefd;
                color: #d17a24;
                padding: 10px;
                border: none solid #ffcea1;
                border-bottom: 2px solid #ffcea1;                
                font-size: 14px;
                font-weight: bold;
                font-family: 'Century Gothic';
            }
            QTableWidget::item {
                padding: 5px;
                font-size: 14px;
                border: none solid #ffcea1;
                border-bottom: 0.5px solid #ffe9d7;
                color: #564234;
            }
            QTableWidget::item:selected {
                background-color: #ffcea1;
                color: #ffffff;
            }
            QScrollBar:vertical {
                background: #FFF;
                width: 5px;
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
        self.report_table.setMinimumHeight(500)

        content_layout.addWidget(self.report_table)

        # EXPANDED VIEW FRAME
        self.expanded_frame = QFrame()
        self.expanded_frame.setStyleSheet("""
            QFrame {
                background-color: #ffe7d2;
                border-radius: 8px;
            }
        """)
        self.expanded_frame.setVisible(False)

        self.expanded_layout = QVBoxLayout(self.expanded_frame)
        self.expanded_layout.setContentsMargins(20, 20, 20, 20)
        self.expanded_layout.setSpacing(10)

        self.expanded_title = QLabel("Payment Details")
        self.expanded_title.setFont(QFont("Century Gothic", 16, QFont.Bold))
        self.expanded_title.setStyleSheet("color: #7e5d47;")

        self.expanded_details_label = QLabel("Payment steps will appear here.")
        self.expanded_details_label.setStyleSheet("color: #564234; font-size: 14px;")
        self.expanded_details_label.setWordWrap(True)

        self.expanded_layout.addWidget(self.expanded_title)
        self.expanded_layout.addWidget(self.expanded_details_label)

        content_layout.addWidget(self.expanded_frame)

        content_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        scroll_area.setWidget(content_widget)
        self.setLayout(main_layout)

        # Load data + populate
        self.load_data()
        self.apply_filters_and_populate_table()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                print("Error reading JSON:", e)
                self.data = []
        else:
            print("data.json file not found.")
            self.data = []

    def on_refresh_clicked(self):
        self.load_data()
        self.apply_filters_and_populate_table()

    def refresh_data(self):
        """Refresh data from GitHub"""
        try:
            # Try to download latest data from GitHub
            if github_sync.download_file('data.json', self.data_file):
                QMessageBox.information(self, "Success", "Data successfully synced")
            else:
                QMessageBox.warning(self, "Warning", "Failed to sync from GitHub, using local data")
            
            # Reload data
            self.load_data()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error refreshing data: {str(e)}")

    def on_batch_payment(self):
        if not self.filtered_data:
            QMessageBox.warning(self, "Warning", "No cases available for batch payment.")
            return
            
        # Show case selection dialog
        dialog = CaseSelectionDialog(self.filtered_data)
        if dialog.exec_() == QDialog.Accepted:
            selected_indices = dialog.getSelectedIndices()
            if selected_indices:
                # Get selected cases
                selected_cases = [self.filtered_data[i] for i in selected_indices]
                
                # Ask for save location
                pdf_filename, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Batch Payment PDF",
                    "batch_payment.pdf",
                    "PDF Files (*.pdf)"
                )
                if not pdf_filename:
                    return

                writer = QPdfWriter(pdf_filename)
                writer.setPageSizeMM(QSizeF(210, 297))  # A4 size
                writer.setResolution(72)

                painter_obj = QPainter()
                if not painter_obj.begin(writer):
                    QMessageBox.critical(self, "Error", "Failed to create PDF file.")
                    return

                try:
                    # Group selected cases by customer
                    customers = {}
                    for record in selected_cases:
                        customer = record.get('Customer Name', 'Unknown')
                        if customer not in customers:
                            customers[customer] = []
                        customers[customer].append(record)
                    
                    # Constants for page layout
                    PAGE_HEIGHT = 842  # A4 height in points
                    MARGIN_TOP = 50
                    MARGIN_BOTTOM = 50
                    current_y = MARGIN_TOP
                    page_number = 0
                    
                    for customer_idx, (customer, records) in enumerate(customers.items()):
                        # For first customer or if previous customer's content ended near bottom
                        if customer_idx > 0 and current_y > PAGE_HEIGHT - 200:  # Leave space for at least header
                            writer.newPage()
                            current_y = MARGIN_TOP
                            page_number += 1
                        
                        # Draw customer header
                        painter_obj.setFont(QFont("Century Gothic", 18, QFont.Bold))
                        painter_obj.drawText(40, current_y, f"Customer: {customer}")
                        current_y += 50
                        
                        # Process each case
                        for idx, record in enumerate(records):
                            # Calculate payment status
                            record_final_amount = float(record.get("Final Amount", 0))
                            record_paid_amount = sum(float(p.get("Amount Paid", 0)) for p in record.get("Payments", []))
                            payment_status = "Fully Paid" if record_paid_amount >= record_final_amount else "Partially Paid" if record_paid_amount > 0 else "Pending"
                            
                            # Prepare case details
                            details = [
                                ("File No.", record.get('File No.', '')),
                                ("Date", record.get('Date', '')),
                                ("Mobile Number", record.get('Mobile Number', '')),
                                ("Work Types", ", ".join(record.get('Work Types', [])) if isinstance(record.get('Work Types', []), list) else str(record.get('Work Types', ''))),
                                ("Work Done", ", ".join(record.get('Work Done', [])) if isinstance(record.get('Work Done', []), list) else str(record.get('Work Done', ''))),
                                ("District", record.get('District', '')),
                                ("Taluka", record.get('Taluka', '')),
                                ("Village", record.get('Village', '')),
                                ("R.S.No./ Block No.", record.get('R.S.No./ Block No.', '')),
                                ("New No.", record.get('New No.', '')),
                                ("Old No.", record.get('Old No.', '')),
                                ("Plot No.", record.get('Plot No.', '')),
                                ("Final Amount", f"₹{record_final_amount:,.2f}"),
                                ("Payment Status", payment_status),
                                ("Remark", record.get('Remark', ''))
                            ]
                            
                            # Calculate case details height
                            case_height = self.calculate_case_height(painter_obj, details)
                            
                            # Check if we need a new page for case details
                            if current_y + case_height > PAGE_HEIGHT - MARGIN_BOTTOM:
                                writer.newPage()
                                page_number += 1
                                current_y = MARGIN_TOP
                                # Redraw customer header on new page
                                painter_obj.setFont(QFont("Century Gothic", 18, QFont.Bold))
                                painter_obj.drawText(40, current_y, f"Customer: {customer} (Continued)")
                                current_y += 50
                            
                            # Draw case details
                            case_height = self.draw_case_details(painter_obj, current_y, details, idx + 1)
                            current_y += case_height + 20
                        
                        # Collect payment information
                        combined_payments = []
                        total_paid = 0
                        total_final_amount = 0
                        
                        for record in records:
                            payments = record.get("Payments", [])
                            for payment in payments:
                                combined_payments.append(payment)
                                total_paid += float(payment.get("Amount Paid", 0))
                            total_final_amount += float(record.get("Final Amount", 0))
                        
                        # Calculate payment section height
                        payment_section_height = 30  # Header
                        payment_section_height += (len(combined_payments) + 1) * 25  # Table rows
                        payment_section_height += 130  # Summary box and spacing
                        
                        # Check if payment section fits on current page
                        if current_y + payment_section_height > PAGE_HEIGHT - MARGIN_BOTTOM:
                            writer.newPage()
                            page_number += 1
                            current_y = MARGIN_TOP
                            painter_obj.setFont(QFont("Century Gothic", 18, QFont.Bold))
                            painter_obj.drawText(40, current_y, f"Customer: {customer} (Payment Details)")
                            current_y += 50
                        
                        # Draw payment details header
                        painter_obj.setFont(QFont("Century Gothic", 14, QFont.Bold))
                        painter_obj.drawText(40, current_y, "Combined Payment Details:")
                        current_y += 30
                        
                        # Payment table setup
                        headers = ["Amount Paid", "Pay Date", "Method", "Cheque No.", "Cheque Date", "Narration"]
                        col_widths = [85, 80, 70, 85, 80, 100]  # Reduced column widths to fit within page
                        row_height = 25
                        table_width = sum(col_widths)
                        table_x = 40
                        table_y = current_y
                        
                        # Draw payment table
                        painter_obj.setPen(QPen(QColor("#000000"), 1))
                        painter_obj.setBrush(QColor("#FFFFFF"))
                        painter_obj.drawRect(table_x, table_y, table_width, (len(combined_payments) + 1) * row_height)
                        
                        # Draw header row
                        painter_obj.setBrush(QColor("#F5F5F5"))
                        painter_obj.drawRect(table_x, table_y, table_width, row_height)
                        
                        # Draw column headers
                        painter_obj.setFont(QFont("Century Gothic", 11, QFont.Bold))
                        x = table_x
                        for idx, (header, width) in enumerate(zip(headers, col_widths)):
                            painter_obj.drawText(x + 5, table_y, width, row_height, Qt.AlignVCenter, header)
                            x += width
                            if idx < len(headers) - 1:
                                painter_obj.drawLine(x, table_y, x, table_y + (len(combined_payments) + 1) * row_height)
                        
                        # Draw payment rows
                        painter_obj.setFont(QFont("Century Gothic", 10))  # Reduced font size for better fit
                        max_rows_count = len(combined_payments)
                        expanded_row_heights = [row_height] * max_rows_count

                        # First pass: calculate expanded heights for rows with long narrations
                        for row, payment in enumerate(combined_payments):
                            narration = payment.get("Narration", "")
                            if narration and len(narration) > 15:  # If narration is long
                                # Calculate how many lines it would need
                                font_metrics = painter_obj.fontMetrics()
                                text_width = col_widths[5] - 10  # Narration column width minus padding

                                # Roughly estimate lines needed based on average char width
                                chars_per_line = max(1, int(text_width / font_metrics.averageCharWidth()))
                                lines_needed = max(1, (len(narration) + chars_per_line - 1) // chars_per_line) # Ceiling division

                                if lines_needed > 1:
                                    expanded_row_heights[row] = row_height * lines_needed

                        # Recalculate table height based on expanded rows
                        total_table_height = row_height + sum(expanded_row_heights)  # Header + all rows

                        # Redraw table with new height
                        painter_obj.setPen(QPen(QColor("#000000"), 1))
                        painter_obj.setBrush(QColor("#FFFFFF"))
                        painter_obj.drawRect(table_x, table_y, table_width, total_table_height)

                        # Redraw header row
                        painter_obj.setBrush(QColor("#F5F5F5"))
                        painter_obj.drawRect(table_x, table_y, table_width, row_height)

                        # Redraw column headers
                        painter_obj.setFont(QFont("Century Gothic", 10, QFont.Bold)) # Use smaller bold font for header
                        x = table_x
                        for idx, (header, width) in enumerate(zip(headers, col_widths)):
                            painter_obj.drawText(x + 5, table_y, width, row_height, Qt.AlignVCenter, header)
                            x += width
                            if idx < len(headers) - 1:
                                painter_obj.drawLine(x, table_y, x, table_y + total_table_height) # Draw vertical lines to full table height

                        # Draw data rows with variable heights
                        current_y_offset = table_y + row_height  # Start after header
                        painter_obj.setFont(QFont("Century Gothic", 10)) # Reset font for data rows

                        for row, payment in enumerate(combined_payments):
                            row_height_current = expanded_row_heights[row]

                            # Draw horizontal line below this row
                            painter_obj.drawLine(table_x, current_y_offset + row_height_current,
                                                 table_x + table_width, current_y_offset + row_height_current)

                            # Prepare row data
                            row_data = [
                                f"₹{float(payment.get('Amount Paid', '0')):,.2f}",
                                payment.get("Payment Date", ""),
                                ", ".join(payment.get("Payment Method", [])) if isinstance(payment.get("Payment Method", []), list) else str(payment.get("Payment Method", "")),
                                payment.get("Cheque No.", ""),
                                payment.get("Cheque Date", ""),
                                payment.get("Narration", "")
                            ]

                            # Draw all columns except Narration
                            x_offset = table_x
                            for col, (value, width) in enumerate(zip(row_data[:-1], col_widths[:-1])):
                                # Draw text vertically centered within the potentially taller row
                                painter_obj.drawText(x_offset + 5, current_y_offset, width - 10, row_height_current,
                                                     Qt.AlignVCenter, str(value))
                                x_offset += width

                            # Draw Narration with manual word wrapping
                            narration_text = row_data[-1]
                            narration_col_width = col_widths[-1]
                            text_x_padding = 5
                            available_width = narration_col_width - (2 * text_x_padding)
                            
                            font_metrics = painter_obj.fontMetrics()
                            words = narration_text.split()
                            lines = []
                            current_line = ""
                            
                            for word in words:
                                test_line = current_line + (" " if current_line else "") + word
                                if font_metrics.width(test_line) <= available_width:
                                    current_line = test_line
                                else:
                                    if current_line:
                                        lines.append(current_line)
                                    # Handle word longer than available width (basic split)
                                    if font_metrics.width(word) > available_width:
                                        # Simple split - might break words mid-way
                                        chars_per_line = max(1, available_width // font_metrics.averageCharWidth())
                                        lines.append(word[:chars_per_line])
                                        current_line = word[chars_per_line:] # Continue with the rest
                                        # TODO: Add logic to handle very long words splitting over multiple lines
                                    else:
                                         current_line = word # Start new line with this word
                            
                            if current_line:
                                lines.append(current_line)
                            
                            # Draw each calculated line
                            line_height = font_metrics.height()
                            for i, line in enumerate(lines):
                                # Ensure we don't draw outside the allocated row height
                                if (i + 1) * line_height <= row_height_current:
                                    line_y = current_y_offset + (i * line_height)
                                    painter_obj.drawText(x_offset + text_x_padding, line_y, 
                                                         available_width, line_height, 
                                                         Qt.AlignVCenter, line)
                                else:
                                    # Optional: Draw ellipsis or indicate truncation if text exceeds allocated height
                                    # For now, just stop drawing
                                    break 

                            current_y_offset += row_height_current # Move to the start of the next row

                        current_y = current_y_offset + 20 # Update current_y after the table
                        
                        # Draw payment summary box
                        summary_width = 250
                        summary_height = 90
                        summary_x = table_x + table_width - summary_width
                        summary_y = current_y
                        
                        painter_obj.setBrush(QColor("#FFFFFF"))
                        painter_obj.drawRect(summary_x, summary_y, summary_width, summary_height)
                        
                        # Draw summary text
                        painter_obj.setFont(QFont("Century Gothic", 12, QFont.Bold))
                        text_x = summary_x + 10
                        text_y = summary_y + 25
                        
                        painter_obj.drawText(text_x, text_y, f"Total Amount Due: ₹{total_final_amount:,.2f}")
                        text_y += 25
                        painter_obj.drawText(text_x, text_y, f"Total Amount Paid: ₹{total_paid:,.2f}")
                        text_y += 25
                        painter_obj.drawText(text_x, text_y, f"Remaining Balance: ₹{total_final_amount - total_paid:,.2f}")
                        
                        # Update current_y for next customer
                        current_y = summary_y + summary_height + 50
                    
                    QMessageBox.information(self, "Success", f"Batch payment PDF generated successfully: {pdf_filename}")
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error generating batch payment PDF: {str(e)}")
                finally:
                    painter_obj.end()

    def showCaseSelection(self):
        if not self.filtered_data:
            QMessageBox.warning(self, "Warning", "No cases available to print.")
            return

        pdf_filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Report",
            "report.pdf",
            "PDF Files (*.pdf)"
        )
        if not pdf_filename:
            return
            
        # Generate PDF for all filtered cases
        writer = QPdfWriter(pdf_filename)
        writer.setPageSizeMM(QSizeF(210, 297))  # A4 size
        writer.setResolution(72)

        painter_obj = QPainter()
        if not painter_obj.begin(writer):
            QMessageBox.critical(self, "Error", "Failed to create PDF file.")
            return

        try:
            # Group cases by customer
            customers = {}
            for record in self.filtered_data:
                customer = record.get('Customer Name', 'Unknown')
                if customer not in customers:
                    customers[customer] = []
                customers[customer].append(record)
            
            # Print each customer's cases
            page_index = 1
            for customer, records in customers.items():
                # Start new page for each customer
                if page_index > 1:
                    writer.newPage()
                
                current_y = 50  # Starting Y position
                
                # Draw customer header
                painter_obj.setFont(QFont("Century Gothic", 18, QFont.Bold))
                painter_obj.drawText(40, current_y, f"Customer: {customer}")
                current_y += 50
                
                # Print each case
                for idx, record in enumerate(records):
                    # Calculate payment status
                    record_final_amount = float(record.get("Final Amount", 0))
                    record_paid_amount = sum(float(p.get("Amount Paid", 0)) for p in record.get("Payments", []))
                    payment_status = "Fully Paid" if record_paid_amount >= record_final_amount else "Partially Paid" if record_paid_amount > 0 else "Pending"
                    
                    # Format work types
                    work_types = record.get('Work Types', [])
                    if isinstance(work_types, list):
                        work_types_str = ", ".join(work_types)
                    else:
                        work_types_str = str(work_types)
                    
                    # Format work done
                    work_done = record.get('Work Done', [])
                    if isinstance(work_done, list):
                        work_done_str = ", ".join(work_done)
                    else:
                        work_done_str = str(work_done)
                    
                    # Case details
                    details = [
                        ("File No.", record.get('File No.', '')),
                        ("Date", record.get('Date', '')),
                        ("Mobile Number", record.get('Mobile Number', '')),
                        ("Work Types", work_types_str),
                        ("Work Done", work_done_str),
                        ("District", record.get('District', '')),
                        ("Taluka", record.get('Taluka', '')),
                        ("Village", record.get('Village', '')),
                        ("R.S.No./ Block No.", record.get('R.S.No./ Block No.', '')),
                        ("New No.", record.get('New No.', '')),
                        ("Old No.", record.get('Old No.', '')),
                        ("Plot No.", record.get('Plot No.', '')),
                        ("Final Amount", f"₹{record_final_amount:,.2f}"),
                        ("Payment Status", payment_status),
                        ("Remark", record.get('Remark', ''))
                    ]
                    
                    # Calculate heights and check for page break
                    content_height = self.calculate_case_height(painter_obj, details)
                    if (current_y + content_height + 20) > 800:  # A4 height minus margins
                        writer.newPage()
                        current_y = 50
                        painter_obj.setFont(QFont("Century Gothic", 18, QFont.Bold))
                        painter_obj.drawText(40, current_y, f"Customer: {customer} (Continued)")
                        current_y += 50
                    
                    # Draw case box
                    self.draw_case_details(painter_obj, current_y, details, idx + 1)
                    current_y += content_height + 20
                
                page_index += 1
            
            QMessageBox.information(self, "Success", f"PDF generated successfully: {pdf_filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating PDF: {str(e)}")
        finally:
            painter_obj.end()
    
    def draw_case_details(self, painter, y_pos, details, case_number):
        """Draw a single case's details box with synced row heights for both columns and dynamic box height for long remarks."""
        # Constants
        BOX_WIDTH = 515
        HEADER_HEIGHT = 30
        ROW_HEIGHT = 20
        PADDING = 15
        LABEL_WIDTH = 100
        TEXT_WIDTH = 180  # Width for text content
        
        # Split details into two columns
        items_per_column = (len(details) + 1) // 2
        left_details = details[:items_per_column]
        right_details = details[items_per_column:]
        
        # Calculate required lines for each row in both columns
        painter.setFont(QFont("Century Gothic", 11))
        metrics = painter.fontMetrics()
        left_lines = []
        right_lines = []
        for label, value in left_details:
            if label in ["Work Types", "Work Done", "Remark"]:
                lines = self.wrap_text(str(value), metrics, TEXT_WIDTH - 10)
                left_lines.append(len(lines))
            else:
                left_lines.append(1)
        for label, value in right_details:
            if label in ["Work Types", "Work Done", "Remark"]:
                lines = self.wrap_text(str(value), metrics, TEXT_WIDTH - 10)
                right_lines.append(len(lines))
            else:
                right_lines.append(1)
        # Pad right_lines if needed
        while len(right_lines) < len(left_lines):
            right_lines.append(1)
        while len(left_lines) < len(right_lines):
            left_lines.append(1)
        # Calculate row heights (max of left/right)
        row_heights = [max(l, r) * ROW_HEIGHT for l, r in zip(left_lines, right_lines)]
        total_content_height = sum(row_heights)
        total_height = HEADER_HEIGHT + (2 * PADDING) + total_content_height
        
        # --- FINAL FIX: Ensure box is always tall enough for last row's content ---
        # Check if last row (usually Remark) has extra lines, and add to total_height if needed
        if row_heights:
            last_row_idx = len(row_heights) - 1
            last_left = left_lines[last_row_idx]
            last_right = right_lines[last_row_idx]
            last_row_lines = max(last_left, last_right)
            min_last_row_height = last_row_lines * ROW_HEIGHT
            # If last row's content is taller than what we calculated, adjust total_height
            actual_last_row_height = row_heights[last_row_idx]
            if min_last_row_height > actual_last_row_height:
                total_height += (min_last_row_height - actual_last_row_height)
                row_heights[last_row_idx] = min_last_row_height
        # -------------------------------------------------------------------------
        
        # Draw main box
        painter.setPen(QPen(QColor("#000000"), 1))
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRect(40, y_pos, BOX_WIDTH, total_height)
        
        # Draw header with gray background
        painter.setBrush(QColor("#F5F5F5"))
        painter.drawRect(40, y_pos, BOX_WIDTH, HEADER_HEIGHT)
        
        # Draw case number
        painter.setFont(QFont("Century Gothic", 14, QFont.Bold))
        painter.drawText(50, y_pos + 20, f"Case {case_number} Details:")
        
        # Draw details in two columns, row by row
        y_pos += HEADER_HEIGHT + PADDING
        left_x = 60
        right_x = 320
        painter.setFont(QFont("Century Gothic", 11))
        for i in range(len(row_heights)):
            # Left column
            if i < len(left_details):
                label, value = left_details[i]
                painter.setFont(QFont("Century Gothic", 11, QFont.Bold))
                label_rect = QRect(left_x, y_pos, LABEL_WIDTH, row_heights[i])
                painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignTop, f"{label}:")
                painter.setFont(QFont("Century Gothic", 11))
                if label in ["Work Types", "Work Done", "Remark"]:
                    lines = self.wrap_text(str(value), painter.fontMetrics(), TEXT_WIDTH - 10)
                    for line_idx, line in enumerate(lines):
                        text_rect = QRect(left_x + LABEL_WIDTH + 5, y_pos + (line_idx * ROW_HEIGHT), TEXT_WIDTH - 10, ROW_HEIGHT)
                        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, line)
                else:
                    text_rect = QRect(left_x + LABEL_WIDTH + 5, y_pos, TEXT_WIDTH - 10, ROW_HEIGHT)
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, str(value))
            # Right column
            if i < len(right_details):
                label, value = right_details[i]
                painter.setFont(QFont("Century Gothic", 11, QFont.Bold))
                label_rect = QRect(right_x, y_pos, LABEL_WIDTH, row_heights[i])
                painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignTop, f"{label}:")
                painter.setFont(QFont("Century Gothic", 11))
                if label in ["Work Types", "Work Done", "Remark"]:
                    lines = self.wrap_text(str(value), painter.fontMetrics(), TEXT_WIDTH - 10)
                    for line_idx, line in enumerate(lines):
                        text_rect = QRect(right_x + LABEL_WIDTH + 5, y_pos + (line_idx * ROW_HEIGHT), TEXT_WIDTH - 10, ROW_HEIGHT)
                        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, line)
                else:
                    text_rect = QRect(right_x + LABEL_WIDTH + 5, y_pos, TEXT_WIDTH - 10, ROW_HEIGHT)
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, str(value))
            y_pos += row_heights[i]
        return total_height

    def calculate_case_height(self, painter, details):
        """Calculate the total height needed for a case"""
        ROW_HEIGHT = 20
        HEADER_HEIGHT = 30
        PADDING = 15
        
        # Set font for text measurement
        painter.setFont(QFont("Century Gothic", 11))
        metrics = painter.fontMetrics()
        available_width = 180  # Reduced width for better wrapping
        
        total_height = HEADER_HEIGHT + (2 * PADDING)
        extra_height = 0
        
        for label, value in details:
            if label in ["Work Types", "Work Done", "Remark"]:
                # Calculate wrapped text height
                lines = len(self.wrap_text(str(value), metrics, available_width))
                extra_height += (lines - 1) * ROW_HEIGHT
            
        return total_height + (len(details) // 2 + 1) * ROW_HEIGHT + extra_height
    
    def wrap_text(self, text, metrics, max_width):
        """Split text into lines that fit within max_width"""
        if not text:
            return []
            
        # Split by commas and spaces
        items = []
        for item in text.split(','):
            item = item.strip()
            if ' ' in item:
                items.extend(item.split())
            else:
                items.append(item)
        
        lines = []
        current_line = []
        current_width = 0
        
        for item in items:
            if not item:
                continue
                
            # Add comma if not the last item
            item_with_comma = item + (", " if item != items[-1] else "")
            item_width = metrics.width(item_with_comma)
            
            if current_width + item_width <= max_width:
                # Item fits on current line
                current_line.append(item)
                current_width += item_width
            else:
                # Item doesn't fit, start new line
                if current_line:
                    lines.append(", ".join(current_line))
                current_line = [item]
                current_width = item_width
        
        # Add remaining items
        if current_line:
            lines.append(", ".join(current_line))
            
        return lines

    def on_filter_triggered(self):
        self.apply_filters_and_populate_table()

    def apply_filters_and_populate_table(self):
        filtered = self.filter_by_month_year(self.data)

        cust_query = self.search_customer_input.text().strip().lower()
        if cust_query:
            filtered = [
                r for r in filtered
                if cust_query in r.get("Customer Name", "").lower()
            ]

        all_query = self.search_all_input.text().strip().lower()
        if all_query:
            new_filtered = []
            for r in filtered:
                record_str = json.dumps(r).lower()
                if all_query in record_str:
                    new_filtered.append(r)
            filtered = new_filtered

        self.filtered_data = filtered
        self.populate_table()

    def filter_by_month_year(self, records):
        selected_month = self.month_combo.currentText()
        selected_year = self.year_combo.currentText()

        if selected_month == "All" and selected_year == "All":
            return records

        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        filtered = []
        for rec in records:
            date_str = rec.get("Date", "")
            try:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            except:
                continue

            if selected_month != "All":
                month_idx = months.index(selected_month) + 1
                if date_obj.month != month_idx:
                    continue

            if selected_year != "All":
                if date_obj.year != int(selected_year):
                    continue

            filtered.append(rec)

        return filtered

    def populate_table(self):
        self.report_table.setRowCount(len(self.filtered_data))

        for row_idx, record in enumerate(self.filtered_data):
            file_no = record.get("File No.", "")
            date_str = record.get("Date", "")
            rs_block = record.get("R.S.No./ Block No.", "")
            new_no = record.get("New No.", "")
            old_no = record.get("Old No.", "")
            plot_no = record.get("Plot No.", "")
            work_types = record.get("Work Types", [])
            work_type_str = ", ".join(work_types) if isinstance(work_types, list) else str(work_types)
            village = record.get("Village", "")
            final_amt_str = record.get("Final Amount", "0")

            paid_amount = 0.0
            for p in record.get("Payments", []):
                try:
                    paid_amount += float(p.get('Amount Paid', '0'))
                except:
                    pass

            try:
                final_amt_val = float(final_amt_str)
            except:
                final_amt_val = 0.0

            final_display = f"₹ {final_amt_val:,.2f}"
            paid_display = f"₹ {paid_amount:,.2f}"

            file_item = QTableWidgetItem(file_no)
            file_item.setTextAlignment(Qt.AlignCenter)

            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)

            rs_block_item = QTableWidgetItem(rs_block)
            rs_block_item.setTextAlignment(Qt.AlignCenter)

            new_no_item = QTableWidgetItem(new_no)
            new_no_item.setTextAlignment(Qt.AlignCenter)

            old_no_item = QTableWidgetItem(old_no)
            old_no_item.setTextAlignment(Qt.AlignCenter)

            plot_item = QTableWidgetItem(plot_no)
            plot_item.setTextAlignment(Qt.AlignCenter)

            work_item = QTableWidgetItem(work_type_str)
            work_item.setTextAlignment(Qt.AlignCenter)

            village_item = QTableWidgetItem(village)
            village_item.setTextAlignment(Qt.AlignCenter)

            final_item = QTableWidgetItem(final_display)
            final_item.setTextAlignment(Qt.AlignCenter)

            paid_item = QTableWidgetItem(paid_display)
            paid_item.setTextAlignment(Qt.AlignCenter)

            view_button = QPushButton("View")
            view_button.setStyleSheet("""
                QPushButton {
                    background-color: #FFA33E;
                    border: none;
                    color: white;
                    font-size: 12px;
                    border-radius: 5px;
                    padding: 4px 8px;
                    font-family: 'Century Gothic';
                }
                QPushButton:hover {
                    background-color: #ff8c00;
                }
            """)
            view_button.clicked.connect(lambda _, r=record: self.on_view_clicked(r))

            self.report_table.setItem(row_idx, 0, file_item)
            self.report_table.setItem(row_idx, 1, date_item)
            self.report_table.setItem(row_idx, 2, rs_block_item)
            self.report_table.setItem(row_idx, 3, new_no_item)
            self.report_table.setItem(row_idx, 4, old_no_item)
            self.report_table.setItem(row_idx, 5, plot_item)
            self.report_table.setItem(row_idx, 6, work_item)
            self.report_table.setItem(row_idx, 7, village_item)
            self.report_table.setItem(row_idx, 8, final_item)
            self.report_table.setItem(row_idx, 9, paid_item)
            self.report_table.setCellWidget(row_idx, 10, view_button)

    def update_customer_completer(self, text):
        """Update customer name completer suggestions"""
        if not text:
            self.customer_completer.setModel(None)
            return

        suggestions = []
        for entry in self.data:
            customer_name = entry.get("Customer Name", "")
            if text.lower() in customer_name.lower():
                suggestions.append(customer_name)

        # Remove duplicates and sort
        unique_suggestions = sorted(list(set(suggestions)))
        model = QStringListModel(unique_suggestions)
        self.customer_completer.setModel(model)

    def update_all_completer(self, text):
        """Update all data completer suggestions"""
        if not text:
            self.all_completer.setModel(None)
            return

        suggestions = []
        for entry in self.data:
            fields = [
                entry.get("File No.", ""),
                entry.get("Customer Name", ""),
                entry.get("Mobile Number", ""),
                entry.get("Village", ""),
                entry.get("District", ""),
                entry.get("Taluka", ""),
                ", ".join(entry.get("Work Types", [])),
                entry.get("Plot No.", "")
            ]
            
            for field in fields:
                if text.lower() in str(field).lower():
                    suggestions.append(str(field))

        # Remove duplicates and sort
        unique_suggestions = sorted(list(set(suggestions)))
        model = QStringListModel(unique_suggestions)
        self.all_completer.setModel(model)

    def on_view_clicked(self, record):
        self.current_selected_record = record

        payments = record.get("Payments", [])
        lines = []
        for i, p in enumerate(payments, start=1):
            amt = p.get("Amount Paid", "0")
            pay_date = p.get("Payment Date", "")
            method = p.get("Payment Method", "")
            chq_no = p.get("Cheque No.", "")
            chq_date = p.get("Cheque Date", "")
            status = p.get("Status", "")
            line = (f"{i}) Amount: ₹{amt}, Date: {pay_date}, "
                    f"Method: {method}, Cheque#: {chq_no}, "
                    f"Cheque Date: {chq_date}, Status: {status}")
            lines.append(line)

        content = "\n".join(lines) if lines else "No payment details available."
        self.expanded_details_label.setText(content)
        self.expanded_frame.setVisible(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PrintReportModule()
    window.show()
    sys.exit(app.exec_())
