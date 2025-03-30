import sys
import time
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFormLayout, QCheckBox, QComboBox,
    QMessageBox, QGroupBox
)

from rs109m.driver_service.service import RS109mConfigurationService
from rs109m.driver_service.models import (
    RS109mConfig,
    RS109mReadConfigRequest,
    RS109mWriteConfigRequest
)
from rs109m.driver_service.ship_type import ShipType


class DeviceMonitor(QThread):
    """
    A background thread that attempts to read the device config
    every few seconds, to detect when the device is online.
    """
    device_connected = pyqtSignal(object)   # emits an RS109mConfig object when connected
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
      - Lets user specify device, password, mock, extended
      - Clicks "Connect" to start monitoring the device
      - Displays AIS fields (mmsi, name, etc.) once connected
      - Allows user to write updated config
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RS109m AIS Configuration")

        # The stateless service
        self.config_service = RS109mConfigurationService()

        # We'll store the currently-running monitor, if any
        self.monitor: Optional[DeviceMonitor] = None

        # The last known config from the device
        self.current_config: Optional[RS109mConfig] = None

        # Build the UI (including a Connect button)
        self._init_ui()

        # We do NOT automatically start the monitor here—
        # the user must click "Connect" to start.

    def closeEvent(self, event) -> None:
        """
        When the window is closed, stop the monitor thread cleanly (if running).
        """
        self._stop_monitor()
        super().closeEvent(event)

    def _stop_monitor(self) -> None:
        """
        If there's an active monitor, stop it and wait for it to finish.
        """
        if self.monitor and self.monitor.isRunning():
            self.monitor.stop()
            self.monitor.wait()
            self.monitor = None

    def _init_ui(self) -> None:
        """
        Create all widgets and apply a "clean and sexy" dark theme.
        """
        # === Overall container ===
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # === Device/connection group ===
        connection_group = QGroupBox("Device Connection")
        connection_layout = QHBoxLayout()
        connection_group.setLayout(connection_layout)

        self.device_edit = QLineEdit()
        self.device_edit.setPlaceholderText("/dev/ttyUSB0")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password (optional)")

        self.mock_checkbox = QCheckBox("Mock")
        self.extended_checkbox = QCheckBox("Extended")

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.on_connect_clicked)

        connection_layout.addWidget(QLabel("Device:"))
        connection_layout.addWidget(self.device_edit)
        connection_layout.addWidget(QLabel("Password:"))
        connection_layout.addWidget(self.password_edit)
        connection_layout.addWidget(self.mock_checkbox)
        connection_layout.addWidget(self.extended_checkbox)
        connection_layout.addWidget(self.connect_button)

        self.status_label = QLabel("Status: Disconnected")

        main_layout.addWidget(connection_group)
        main_layout.addWidget(self.status_label)

        # === AIS Configuration form ===
        config_group = QGroupBox("AIS Configuration")
        config_form = QFormLayout()
        config_group.setLayout(config_form)

        # Create inputs for each config field
        self.mmsi_input = QLineEdit()
        self.name_input = QLineEdit()
        self.interval_input = QLineEdit()

        self.ship_type_combo = QComboBox()
        # Populate combo with all valid ShipType members
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

        config_form.addRow("MMSI:", self.mmsi_input)
        config_form.addRow("Ship Name:", self.name_input)
        config_form.addRow("Interval (30..600):", self.interval_input)
        config_form.addRow("Ship Type:", self.ship_type_combo)
        config_form.addRow("Callsign:", self.callsign_input)
        config_form.addRow("Vendor ID:", self.vendorid_input)
        config_form.addRow("Unit Model:", self.unitmodel_input)
        config_form.addRow("Serial Number:", self.sernum_input)
        config_form.addRow("Ref A:", self.refa_input)
        config_form.addRow("Ref B:", self.refb_input)
        config_form.addRow("Ref C:", self.refc_input)
        config_form.addRow("Ref D:", self.refd_input)

        main_layout.addWidget(config_group)

        # === Write button ===
        self.write_button = QPushButton("Write Configuration")
        self.write_button.clicked.connect(self.on_write_clicked)
        self.write_button.setEnabled(False)  # disabled until connected
        main_layout.addWidget(self.write_button)

        # === Apply a nice dark theme ===
        self._apply_dark_theme()

    def _apply_dark_theme(self) -> None:
        """
        Apply a minimal "sexy" dark theme for a modern look.
        """
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #f0f0f0;
                font-size: 10pt;
                font-family: Arial, Helvetica, sans-serif;
            }
            QGroupBox {
                margin-top: 10px;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 10px;
            }
            QLineEdit, QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555;
                padding: 4px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #888;
            }
            QPushButton {
                background-color: #444;
                border: 1px solid #666;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)

    def on_connect_clicked(self) -> None:
        """
        Called when user clicks 'Connect'. We stop any existing monitor,
        then create a new one with the current device/password/mock/extended values,
        and start it. The monitor will emit signals as it connects/disconnects.
        """
        # Stop the old monitor if it's still running
        self._stop_monitor()

        device = self.device_edit.text().strip()
        password = self.password_edit.text().strip() or None
        mock = self.mock_checkbox.isChecked()
        extended = self.extended_checkbox.isChecked()

        if not device:
            QMessageBox.warning(self, "No Device Specified", "Please enter a device path (e.g. /dev/ttyUSB0).")
            return

        # Create a new monitor and start it
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

        self.status_label.setText("Status: Connecting...")

    def on_device_connected(self, config: RS109mConfig) -> None:
        """
        Called by background thread when a config read is successful.
        """
        self.status_label.setText("Status: Connected")
        self.write_button.setEnabled(True)
        self.current_config = config
        self.populate_form(config)

    def on_device_disconnected(self) -> None:
        """
        Called by background thread when device was connected but is now lost.
        """
        self.status_label.setText("Status: Disconnected")
        self.write_button.setEnabled(False)
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
            # ship_type could be an int or a ShipType; ensure we get the ShipType
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
        """
        def safe_int(text: str) -> Optional[int]:
            text = text.strip()
            return int(text) if text else None

        selected_shiptype = self.ship_type_combo.currentData()
        return RS109mConfig(
            mmsi=safe_int(self.mmsi_input.text()),
            name=self.name_input.text().strip() or None,
            interval=safe_int(self.interval_input.text()),
            ship_type=selected_shiptype,  # already a ShipType
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
        if not self.current_config:
            QMessageBox.warning(self, "Not Connected", "No device connection yet.")
            return

        new_config = self.build_config_from_form()

        if not self.monitor:
            QMessageBox.warning(self, "No Monitor", "Please connect first.")
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
        except Exception as e:
            QMessageBox.critical(self, "Write Failed", str(e))


def app() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    app()
