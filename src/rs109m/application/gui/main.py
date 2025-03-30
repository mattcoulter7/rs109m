import sys
import time
from enum import Enum, auto
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFormLayout, QCheckBox, QComboBox,
    QMessageBox, QGroupBox
)

from pydantic import ValidationError

from rs109m.driver_service.service import RS109mConfigurationService
from rs109m.driver_service.models import (
    RS109mConfig,
    RS109mReadConfigRequest,
    RS109mWriteConfigRequest
)
from rs109m.driver_service.ship_type import ShipType


class DeviceState(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    DISCONNECTING = auto()


class DeviceMonitor(QThread):
    """
    A background thread that attempts to read the device config
    every few seconds, to detect when the device is online.
    """
    device_connected = pyqtSignal(object)  # emits an RS109mConfig object when connected
    device_disconnected = pyqtSignal()

    def __init__(
        self,
        service: RS109mConfigurationService,
        device: str,
        password: Optional[str],
        mock: bool,
        extended: bool,
        interval: float = 2.0,
        parent=None
    ) -> None:
        super().__init__(parent)
        self.service = service
        self.device = device
        self.password = password
        self.mock = mock
        self.extended = extended
        self.interval = interval

        self.running = True
        self._was_connected = False

    def run(self) -> None:
        """
        Loop until stopped, trying to read config.
        If it succeeds and we weren't connected before, emit device_connected.
        If it fails and we were connected before, emit device_disconnected.
        """
        while self.running:
            try:
                req = RS109mReadConfigRequest(
                    device=self.device,
                    password=self.password,
                    mock=self.mock,
                    extended=self.extended
                )
                config = self.service.read_config(req)
                if not self._was_connected:
                    self._was_connected = True
                    self.device_connected.emit(config)
            except Exception:
                if self._was_connected:
                    self._was_connected = False
                    self.device_disconnected.emit()
            time.sleep(self.interval)

    def stop(self) -> None:
        self.running = False


class MainWindow(QMainWindow):
    """
    A single-window PyQt6 application that:
      - Uses a 4-state connection model (Disconnected/Connecting/Connected/Disconnecting)
      - The button changes to "Connect", "Disconnect", or "Cancel" based on state
      - Disables device fields when connected or connecting
      - Disables config fields & write button until connected
      - Catches Pydantic ValidationError for config writes
      - Shows a custom window icon from assets/icon.ico
      - Visibly grays out disabled fields
    """

    def __init__(self) -> None:
        super().__init__()

        # Set window properties
        self.setWindowTitle("RS109m AIS Configuration")
        # Load your icon from relative path
        self.setWindowIcon(QIcon("assets/icon.ico"))

        # The stateless service
        self.config_service = RS109mConfigurationService()

        # We'll store the currently-running monitor, if any
        self.monitor: Optional[DeviceMonitor] = None

        # The last known config from the device
        self.current_config: Optional[RS109mConfig] = None

        # Current device state
        self.device_state = DeviceState.DISCONNECTED

        # Build the UI
        self._init_ui()

        # Start in DISCONNECTED state
        self._set_device_state(DeviceState.DISCONNECTED)

    def closeEvent(self, event) -> None:
        """
        When the window is closed, stop the monitor thread cleanly (if running).
        """
        self._stop_monitor()
        super().closeEvent(event)

    def _stop_monitor(self) -> None:
        """
        If there's an active monitor, stop it and wait for it to finish.
        (Used for both Disconnecting and Cancel.)
        """
        if self.monitor and self.monitor.isRunning():
            self.monitor.stop()
            self.monitor.wait()
            self.monitor = None

    def _init_ui(self) -> None:
        """
        Create all widgets.
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)  # extra spacing between sections
        central_widget.setLayout(main_layout)

        # === Device Connection Group ===
        connection_group = QGroupBox("Device Connection")
        connection_group_layout = QHBoxLayout()
        connection_group_layout.setSpacing(10)
        connection_group.setLayout(connection_group_layout)

        self.device_edit = QLineEdit()
        self.device_edit.setPlaceholderText("/dev/ttyUSB0")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password (optional)")

        self.mock_checkbox = QCheckBox("Mock")
        self.extended_checkbox = QCheckBox("Extended")

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.on_connect_button_clicked)

        connection_group_layout.addWidget(QLabel("Device:"))
        connection_group_layout.addWidget(self.device_edit)
        connection_group_layout.addWidget(QLabel("Password:"))
        connection_group_layout.addWidget(self.password_edit)
        connection_group_layout.addWidget(self.mock_checkbox)
        connection_group_layout.addWidget(self.extended_checkbox)
        connection_group_layout.addWidget(self.connect_button)

        # Status label below the connection group
        self.status_label = QLabel("Status: Disconnected")

        main_layout.addWidget(connection_group)
        main_layout.addWidget(self.status_label)

        # === AIS Configuration Group ===
        config_group = QGroupBox("AIS Configuration")
        self.config_form = QFormLayout()
        self.config_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.config_form.setHorizontalSpacing(12)
        self.config_form.setVerticalSpacing(8)
        config_group.setLayout(self.config_form)

        self.mmsi_input = QLineEdit()
        self.name_input = QLineEdit()
        self.interval_input = QLineEdit()
        self.ship_type_combo = QComboBox()
        for st in ShipType:
            self.ship_type_combo.addItem(f"{st.value} - {st.name}", st)

        self.callsign_input = QLineEdit()
        self.vendorid_input = QLineEdit()
        self.unitmodel_input = QLineEdit()
        self.sernum_input = QLineEdit()
        self.refa_input = QLineEdit()
        self.refb_input = QLineEdit()
        self.refc_input = QLineEdit()
        self.refd_input = QLineEdit()

        self.config_form.addRow("MMSI:", self.mmsi_input)
        self.config_form.addRow("Ship Name:", self.name_input)
        self.config_form.addRow("Interval (30..600):", self.interval_input)
        self.config_form.addRow("Ship Type:", self.ship_type_combo)
        self.config_form.addRow("Callsign:", self.callsign_input)
        self.config_form.addRow("Vendor ID:", self.vendorid_input)
        self.config_form.addRow("Unit Model:", self.unitmodel_input)
        self.config_form.addRow("Serial Number:", self.sernum_input)
        self.config_form.addRow("Ref A:", self.refa_input)
        self.config_form.addRow("Ref B:", self.refb_input)
        self.config_form.addRow("Ref C:", self.refc_input)
        self.config_form.addRow("Ref D:", self.refd_input)

        main_layout.addWidget(config_group)

        # === Write Button (Centered) ===
        self.write_button = QPushButton("Write Configuration")
        self.write_button.clicked.connect(self.on_write_clicked)

        write_button_layout = QHBoxLayout()
        write_button_layout.addStretch(1)
        write_button_layout.addWidget(self.write_button)
        write_button_layout.addStretch(1)
        main_layout.addLayout(write_button_layout)

        # Apply modern dark theme (including a disabled style)
        self._apply_modern_dark_theme()

    def _apply_modern_dark_theme(self) -> None:
        """
        A sleek modern stylesheet with :disabled states for
        a visually obvious disabled color scheme.
        """
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
                color: #eeeeee;
                background-color: #202124;
            }
            QGroupBox {
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                margin-top: 20px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
                font-weight: bold;
                font-size: 12pt;
                color: #bbbbbb;
            }
            QLabel {
                font-weight: 500;
                color: #cccccc;
            }
            /* Normal fields */
            QLineEdit, QComboBox {
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
                background-color: #2a2a2a;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #7aaaff;
            }
            /* Disabled fields (grayed out) */
            QLineEdit:disabled, QComboBox:disabled {
                color: #999999;
                background-color: #343434;
                border: 1px solid #555;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #eeeeee;
                border-radius: 6px;
                border: 1px solid #666;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #222222;
            }
            QPushButton:disabled {
                color: #7f7f7f;
                background-color: #2f2f2f;
                border: 1px solid #444;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #888;
                background-color: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                background-color: #7aaaff;
                border: 1px solid #7aaaff;
            }
            QCheckBox:disabled {
                color: #777777;
            }
            QCheckBox::indicator:disabled {
                background-color: #444;
                border: 1px solid #555;
            }
        """)

    def _set_device_state(self, new_state: DeviceState) -> None:
        """
        Updates self.device_state and adjusts UI elements accordingly:
         - connect_button text & enabled state
         - device/password fields
         - config fields
         - status_label
        """
        self.device_state = new_state

        if new_state == DeviceState.DISCONNECTED:
            self.status_label.setText("🔴 Status: Disconnected")
            # enable device/password fields
            self.device_edit.setEnabled(True)
            self.password_edit.setEnabled(True)
            self.mock_checkbox.setEnabled(True)
            self.extended_checkbox.setEnabled(True)

            self.connect_button.setText("Connect")
            self.connect_button.setEnabled(True)

            # disable config fields & write button
            self.set_config_fields_enabled(False)

        elif new_state == DeviceState.CONNECTING:
            self.status_label.setText("🟡 Status: Connecting...")
            # disable device/password fields
            self.device_edit.setEnabled(False)
            self.password_edit.setEnabled(False)
            self.mock_checkbox.setEnabled(False)
            self.extended_checkbox.setEnabled(False)

            self.connect_button.setText("Cancel")
            self.connect_button.setEnabled(True)

            # still no config access
            self.set_config_fields_enabled(False)

        elif new_state == DeviceState.CONNECTED:
            self.status_label.setText("🟢 Status: Connected")
            # disable device/password fields (can't change port while connected)
            self.device_edit.setEnabled(False)
            self.password_edit.setEnabled(False)
            self.mock_checkbox.setEnabled(False)
            self.extended_checkbox.setEnabled(False)

            self.connect_button.setText("Disconnect")
            self.connect_button.setEnabled(True)

            # now we can edit config fields
            self.set_config_fields_enabled(True)

        elif new_state == DeviceState.DISCONNECTING:
            self.status_label.setText("🟡 Status: Disconnecting...")
            # disable everything
            self.device_edit.setEnabled(False)
            self.password_edit.setEnabled(False)
            self.mock_checkbox.setEnabled(False)
            self.extended_checkbox.setEnabled(False)
            self.connect_button.setText("Cancel")
            self.connect_button.setEnabled(True)
            self.set_config_fields_enabled(False)

    def set_config_fields_enabled(self, enabled: bool) -> None:
        """
        Enable/disable all config inputs + write button.
        """
        widgets = [
            self.mmsi_input, self.name_input, self.interval_input,
            self.ship_type_combo, self.callsign_input,
            self.vendorid_input, self.unitmodel_input, self.sernum_input,
            self.refa_input, self.refb_input, self.refc_input, self.refd_input,
        ]
        for w in widgets:
            w.setEnabled(enabled)
        self.write_button.setEnabled(enabled)

    def on_connect_button_clicked(self) -> None:
        """
        Single button handling:
          - If DISCONNECTED -> go CONNECTING (start monitor)
          - If CONNECTING -> Cancel (stop monitor, go DISCONNECTED)
          - If CONNECTED -> Disconnect (go DISCONNECTING)
          - If DISCONNECTING -> Cancel (immediately go DISCONNECTED)
        """
        if self.device_state == DeviceState.DISCONNECTED:
            # Start connecting
            device = self.device_edit.text().strip()
            password = self.password_edit.text().strip() or None
            mock = self.mock_checkbox.isChecked()
            extended = self.extended_checkbox.isChecked()

            if not device:
                QMessageBox.warning(
                    self,
                    "No Device Specified",
                    "Please enter a device path (e.g. /dev/ttyUSB0)."
                )
                return

            self._set_device_state(DeviceState.CONNECTING)
            # start monitor
            self.monitor = DeviceMonitor(
                service=self.config_service,
                device=device,
                password=password,
                mock=mock,
                extended=extended,
                interval=2.0
            )
            self.monitor.device_connected.connect(self.on_device_connected)
            self.monitor.device_disconnected.connect(self.on_device_disconnected)
            self.monitor.start()

        elif self.device_state == DeviceState.CONNECTING:
            # Cancel connecting
            self._stop_monitor()
            self._set_device_state(DeviceState.DISCONNECTED)

        elif self.device_state == DeviceState.CONNECTED:
            # Attempt to disconnect
            self._set_device_state(DeviceState.DISCONNECTING)
            self._stop_monitor()  # blocks until done
            self._set_device_state(DeviceState.DISCONNECTED)

        elif self.device_state == DeviceState.DISCONNECTING:
            # Cancel disconnect => forcibly become DISCONNECTED
            self._stop_monitor()
            self._set_device_state(DeviceState.DISCONNECTED)

    def on_device_connected(self, config: RS109mConfig) -> None:
        """
        Called by background thread when a config read is successful.
        If we were in CONNECTING state, we move to CONNECTED.
        """
        if self.device_state == DeviceState.CONNECTING:
            self._set_device_state(DeviceState.CONNECTED)
            self.current_config = config
            self.populate_form(config)

    def on_device_disconnected(self) -> None:
        """
        Called by background thread when device was connected but is now lost.
        If we were in CONNECTING or CONNECTED, we go to DISCONNECTED.
        """
        if self.device_state in (DeviceState.CONNECTING, DeviceState.CONNECTED):
            self._set_device_state(DeviceState.DISCONNECTED)
            self.current_config = None

    def populate_form(self, config: RS109mConfig) -> None:
        """
        Fill the form fields with the data from the config object.
        """
        def set_text_or_clear(lineedit: QLineEdit, val: Optional[int | str]) -> None:
            if val is not None:
                lineedit.setText(str(val))
            else:
                lineedit.clear()

        set_text_or_clear(self.mmsi_input, config.mmsi)
        self.name_input.setText(config.name or "")
        set_text_or_clear(self.interval_input, config.interval)

        if config.ship_type is not None:
            st_val = config.ship_type.value if isinstance(config.ship_type, ShipType) else config.ship_type
            idx = self.ship_type_combo.findData(ShipType(st_val))
            if idx >= 0:
                self.ship_type_combo.setCurrentIndex(idx)

        self.callsign_input.setText(config.callsign or "")
        self.vendorid_input.setText(config.vendorid or "")
        set_text_or_clear(self.unitmodel_input, config.unitmodel)
        set_text_or_clear(self.sernum_input, config.sernum)
        set_text_or_clear(self.refa_input, config.refa)
        set_text_or_clear(self.refb_input, config.refb)
        set_text_or_clear(self.refc_input, config.refc)
        set_text_or_clear(self.refd_input, config.refd)

    def build_config_from_form(self) -> RS109mConfig:
        """
        Create an RS109mConfig object from the current form fields.
        May raise pydantic.ValidationError if data is invalid.
        """
        def safe_int(text: str) -> Optional[int]:
            text = text.strip()
            return int(text) if text else None

        selected_shiptype = self.ship_type_combo.currentData()
        return RS109mConfig(
            mmsi=safe_int(self.mmsi_input.text()),
            name=self.name_input.text().strip() or None,
            interval=safe_int(self.interval_input.text()),
            ship_type=selected_shiptype,
            callsign=self.callsign_input.text().strip() or None,
            vendorid=self.vendorid_input.text().strip() or None,
            unitmodel=safe_int(self.unitmodel_input.text()),
            sernum=safe_int(self.sernum_input.text()),
            refa=safe_int(self.refa_input.text()),
            refb=safe_int(self.refb_input.text()),
            refc=safe_int(self.refc_input.text()),
            refd=safe_int(self.refd_input.text()),
        )

    def on_write_clicked(self) -> None:
        """
        Called when the user clicks "Write Configuration."
        """
        if self.device_state != DeviceState.CONNECTED:
            QMessageBox.warning(self, "Not Connected", "Please connect first.")
            return

        try:
            new_config = self.build_config_from_form()
        except ValidationError as e:
            QMessageBox.critical(
                self,
                "Validation Error",
                f"Invalid input:\n{e}"
            )
            return

        if not self.monitor:
            QMessageBox.warning(self, "No Monitor", "Monitor not running.")
            return

        req = RS109mWriteConfigRequest(
            config=new_config,
            device=self.monitor.device,
            password=self.monitor.password,
            mock=self.monitor.mock,
            extended=self.monitor.extended,
        )

        try:
            written_config = self.config_service.write_config(req)
            QMessageBox.information(
                self,
                "Success",
                f"Configuration written successfully!\n\n"
                f"Current config:\n{written_config.get_config_str()}"
            )
        except Exception as ex:
            QMessageBox.critical(self, "Write Failed", str(ex))


def app() -> None:
    application = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    app()
