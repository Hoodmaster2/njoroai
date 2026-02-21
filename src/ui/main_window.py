import json
import hashlib
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QListWidget, QListWidgetItem, QLabel, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSlot

from src.persistence.database import db
from src.agent.loop import AgentThread
from src.ui.theme import CyberTheme

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NJORO AI - Autonomous Desktop Operator")
        self.resize(1200, 800)
        
        self.agent_thread = AgentThread()
        self.setup_ui()
        self.connect_signals()
        
        # Load existing state
        self.refresh_journal()
        self.refresh_confirmations()

    def setup_ui(self):
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # --- LEFT PANEL: Goal & Controls ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel("Current Goal:"))
        self.goal_input = QTextEdit()
        self.goal_input.setPlaceholderText("Enter your objective here...")
        left_layout.addWidget(self.goal_input)
        
        self.start_btn = QPushButton("Start / Resume Agent")
        self.start_btn.clicked.connect(self.handle_start)
        left_layout.addWidget(self.start_btn)
        
        splitter.addWidget(left_panel)

        # --- CENTER PANEL: Journal ---
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        center_layout.addWidget(QLabel("Execution Journal:"))
        self.journal_table = QTableWidget()
        self.journal_table.setColumnCount(5)
        self.journal_table.setHorizontalHeaderLabels(["Time", "Action", "Tool", "Result", "Status"])
        self.journal_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        center_layout.addWidget(self.journal_table)
        
        splitter.addWidget(center_panel)

        # --- RIGHT PANEL: Confirmations ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        right_layout.addWidget(QLabel("Pending Confirmations:"))
        self.confirmations_list = QListWidget()
        right_layout.addWidget(self.confirmations_list)
        
        btn_layout = QHBoxLayout()
        self.approve_btn = QPushButton("Approve")
        self.approve_btn.clicked.connect(self.handle_approve)
        self.reject_btn = QPushButton("Reject")
        self.reject_btn.clicked.connect(self.handle_reject)
        
        btn_layout.addWidget(self.approve_btn)
        btn_layout.addWidget(self.reject_btn)
        right_layout.addLayout(btn_layout)
        
        splitter.addWidget(right_panel)

        # Set splitter sizes (20%, 50%, 30%)
        splitter.setSizes([240, 600, 360])

        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("System Ready")

    def connect_signals(self):
        self.agent_thread.signals.log_updated.connect(self.add_journal_entry)
        self.agent_thread.signals.status_changed.connect(self.update_status)
        self.agent_thread.signals.confirmation_required.connect(self.add_confirmation)
        self.agent_thread.signals.goal_updated.connect(self.handle_goal_update)

    @pyqtSlot()
    def handle_start(self):
        if self.agent_thread.isRunning():
            self.status_bar.showMessage("Agent is already running...")
            return

        goal_text = self.goal_input.toPlainText().strip()
        if not goal_text:
            QMessageBox.warning(self, "Input Error", "Please enter a goal.")
            return

        # Check for existing active goal or create new
        existing_goal = db.fetch_one("SELECT * FROM goals WHERE status = 'active'")
        if not existing_goal:
            db.execute_query("INSERT INTO goals (description, status) VALUES (?, ?)", (goal_text, "active"))
            self.status_bar.showMessage("New Goal Started")
        else:
             # Optionally update description if changed? 
             # For now, we assume resuming the active goal.
             pass

        self.agent_thread.start()

    @pyqtSlot(dict)
    def add_journal_entry(self, entry):
        row = self.journal_table.rowCount()
        self.journal_table.insertRow(row)
        self.journal_table.setItem(row, 0, QTableWidgetItem(entry['timestamp']))
        self.journal_table.setItem(row, 1, QTableWidgetItem(entry['action']))
        self.journal_table.setItem(row, 2, QTableWidgetItem(entry['tool']))
        self.journal_table.setItem(row, 3, QTableWidgetItem(entry['result']))
        self.journal_table.setItem(row, 4, QTableWidgetItem(entry['status']))
        self.journal_table.scrollToBottom()

    @pyqtSlot(str)
    def update_status(self, message):
        self.status_bar.showMessage(message)

    @pyqtSlot(dict)
    def add_confirmation(self, details):
        item_text = f"""Tool: {details['tool_name']}
Reason: {details['reasoning']}
Args: {json.dumps(details['tool_args'], indent=2)}"""
        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, details) # Store full details
        self.confirmations_list.addItem(item)
        self.update_status("Confirmation Required!")

    @pyqtSlot()
    def handle_approve(self):
        item = self.confirmations_list.currentItem()
        if not item:
            return
        
        details = item.data(Qt.ItemDataRole.UserRole)
        action_desc = f"{details['tool_name']}:{json.dumps(details['tool_args'], sort_keys=True)}"
        action_hash = hashlib.sha256(action_desc.encode()).hexdigest()
        
        # Store in DB
        db.execute_query(
            "INSERT OR REPLACE INTO confirmations (action_hash, goal_id, action_description, approved, expiry) VALUES (?, ?, ?, ?, ?)",
            (action_hash, details['goal_id'], action_desc, True, None) # No expiry for now
        )
        
        # Remove from list
        self.confirmations_list.takeItem(self.confirmations_list.row(item))
        self.status_bar.showMessage("Action Approved. Click 'Start/Resume' to continue.")

    @pyqtSlot()
    def handle_reject(self):
        item = self.confirmations_list.currentItem()
        if not item:
            return
        
        details = item.data(Qt.ItemDataRole.UserRole)
        action_desc = f"{details['tool_name']}:{json.dumps(details['tool_args'], sort_keys=True)}"
        action_hash = hashlib.sha256(action_desc.encode()).hexdigest()
        
        # Store in DB
        db.execute_query(
            "INSERT OR REPLACE INTO confirmations (action_hash, goal_id, action_description, approved, expiry) VALUES (?, ?, ?, ?, ?)",
            (action_hash, details['goal_id'], action_desc, False, None)
        )

        # Log to Journal so LLM knows
        db.execute_query(
            "INSERT INTO journal (goal_id, action, tool_used, result, status) VALUES (?, ?, ?, ?, ?)",
            (details['goal_id'], "User Rejected Action", details['tool_name'], "Action explicitly rejected by user", "failed")
        )
        
        # Update UI Journal
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "action": "User Rejected Action",
            "tool": details['tool_name'],
            "result": "Action explicitly rejected by user",
            "status": "failed"
        }
        self.add_journal_entry(entry)
        
        # Remove from list
        self.confirmations_list.takeItem(self.confirmations_list.row(item))
        self.status_bar.showMessage("Action Rejected.")

    @pyqtSlot(dict)
    def handle_goal_update(self, data):
        if data['status'] == 'completed':
            QMessageBox.information(self, "Success", "Goal Completed Successfully!")
            self.goal_input.clear()
        elif data['status'] == 'failed':
            QMessageBox.critical(self, "Failure", "Goal Failed.")

    def refresh_journal(self):
        # Load last 50 entries
        entries = db.fetch_all("SELECT * FROM journal ORDER BY timestamp DESC LIMIT 50")
        self.journal_table.setRowCount(0)
        for entry in reversed(entries): # Show oldest to newest
            row = self.journal_table.rowCount()
            self.journal_table.insertRow(row)
            self.journal_table.setItem(row, 0, QTableWidgetItem(str(entry['timestamp'])))
            self.journal_table.setItem(row, 1, QTableWidgetItem(entry['action']))
            self.journal_table.setItem(row, 2, QTableWidgetItem(entry['tool_used']))
            self.journal_table.setItem(row, 3, QTableWidgetItem(entry['result'][:100]))
            self.journal_table.setItem(row, 4, QTableWidgetItem(entry['status']))

    def refresh_confirmations(self):
        # We don't persist pending confirmations in a "queue" table, 
        # so this is mostly for valid session restore if we added that. 
        # For now, list is empty on restart until agent hits them again.
        pass

    def closeEvent(self, event):
        self.agent_thread.stop()
        self.agent_thread.wait()
        event.accept()
