"""
Discord webhook settings dialog for JellyMacro
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QCheckBox, QDialogButtonBox, QPushButton, QLabel,
    QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

from src.config import CONFIG
from src.discord_webhook import DISCORD_WEBHOOK


class DiscordSettingsDialog(QDialog):
    webhook_updated = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Discord Webhook Settings")
        self.resize(500, 350)
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Webhook URL
        webhook_group = QFormLayout()
        
        self.webhook_url = QLineEdit()
        self.webhook_url.setPlaceholderText("https://discord.com/api/webhooks/...")
        self.webhook_url.setToolTip("Discord webhook URL for sending status updates")
        webhook_group.addRow("Webhook URL:", self.webhook_url)
        
        self.enabled_check = QCheckBox("Enable Discord webhook")
        self.enabled_check.setToolTip("Toggle sending status updates to Discord")
        webhook_group.addRow("", self.enabled_check)
        
        self.interval = QSpinBox()
        self.interval.setRange(5, 1440)
        self.interval.setSuffix(" minutes")
        self.interval.setToolTip("How often to send automatic status updates")
        webhook_group.addRow("Update Interval:", self.interval)
        
        self.include_screenshot = QCheckBox("Include screenshot in updates")
        self.include_screenshot.setToolTip("Attach a screenshot to Discord updates")
        webhook_group.addRow("", self.include_screenshot)
        
        self.custom_message = QLineEdit()
        self.custom_message.setPlaceholderText("Enter custom status message")
        self.custom_message.setToolTip("Custom message for Discord embeds")
        webhook_group.addRow("Custom Message:", self.custom_message)
        
        self.include_counters = QCheckBox("Include counter values")
        webhook_group.addRow(self.include_counters)
        
        self.include_variables = QCheckBox("Include variable values")
        webhook_group.addRow(self.include_variables)
        
        layout.addLayout(webhook_group)
        
        # Test button
        button_layout = QHBoxLayout()
        self.test_btn = QPushButton("Test Webhook")
        self.test_btn.setToolTip("Send a test message to verify the webhook")
        button_layout.addWidget(self.test_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.test_btn.clicked.connect(self._test_webhook)
    
    def _load_settings(self):
        config = CONFIG.get()
        self.webhook_url.setText(config.discord.webhook_url)
        self.enabled_check.setChecked(config.discord.enabled)
        self.interval.setValue(config.discord.interval_minutes)
        self.include_screenshot.setChecked(config.discord.send_screenshot)
        self.custom_message.setText("JellyMacro Status Update")
    
    def accept(self):
        self._save_settings()
        super().accept()
    
    def _save_settings(self):
        config = CONFIG.get()
        config.discord.webhook_url = self.webhook_url.text()
        config.discord.enabled = self.enabled_check.isChecked()
        config.discord.interval_minutes = self.interval.value()
        config.discord.send_screenshot = self.include_screenshot.isChecked()
        CONFIG.save()
        
        if config.discord.enabled and config.discord.webhook_url:
            DISCORD_WEBHOOK.configure(
                webhook_url=config.discord.webhook_url,
                enabled=config.discord.enabled,
                interval_minutes=config.discord.interval_minutes,
                send_screenshot=config.discord.send_screenshot,
                custom_message=self.custom_message.text(),
                include_counters=self.include_counters.isChecked(),
                include_variables=self.include_variables.isChecked()
            )
            DISCORD_WEBHOOK.start()
        
        self.webhook_updated.emit()
    
    def _test_webhook(self):
        if not self.webhook_url.text():
            QMessageBox.warning(self, "No URL", "Please enter a webhook URL")
            return
        
        self._save_settings()
        success = DISCORD_WEBHOOK.send_status(force=True)
        if success:
            QMessageBox.information(self, "Success", "Test message sent successfully!")
        else:
            QMessageBox.critical(self, "Failed", "Failed to send test message")