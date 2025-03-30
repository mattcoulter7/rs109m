import logging
from typing import Optional

from rs109m.driver import RS109mDriver
from rs109m.driver.constants import DEFAULT_PASSWORD
from rs109m.driver.device_io import SerialDeviceIO, MockDeviceIO

from .models import RS109mConfig, RS109mReadConfigRequest, RS109mWriteConfigRequest
from .config_util import apply_rs109m_config_to_driver_config, driver_config_to_rs109m_config

logger = logging.getLogger(__name__)


class RS109mConfigurationService:
    def _get_driver(
        self,
        device: Optional[str],
        mock: bool
    ) -> RS109mDriver:
        """Get the driver for communicating with the rs109m device"""
        if not mock and not device:
            raise ValueError("Must specify device if not using mock")
        device_io = MockDeviceIO() if mock else SerialDeviceIO(device)
        return RS109mDriver(device_io)

    def read_config(
        self,
        request: RS109mReadConfigRequest,
    ) -> RS109mConfig:
        """
        Read the configuration from the device.
        """
        driver = self._get_driver(request.device, request.mock)

        # Re-read the configuration to confirm the new configuration has been applied
        config = driver.read_config(
            password=request.password,
            extended=request.extended,
        )

        # Print the current configuration (the hexadecimal dump is built inside DeviceConfigIO)
        logger.info(
            f"Read configuration:\n{config.get_config_str(request.extended)}"
        )

        return driver_config_to_rs109m_config(config)

    def write_config(
        self,
        request: RS109mWriteConfigRequest,
    ) -> RS109mConfig:
        """
        Write the configuration to the device.
        Returns:
            Latest configuration read from the device
        """
        driver = self._get_driver(request.device, request.mock)

        # read the current configuration from the device into config
        config = driver.read_config(
            password=request.password,
            extended=request.extended,
        )

        # Print the current configuration (the hexadecimal dump is built inside DeviceConfigIO)
        logger.info(
            f"Old configuration:\n{config.get_config_str(request.extended)}"
        )

        # apply request config values to the existing driver configuration
        apply_rs109m_config_to_driver_config(
            request.config, config,
        )

        # Print the current configuration (the hexadecimal dump is built inside DeviceConfigIO)
        logger.info(
            f"Desired configuration:\n{config.get_config_str(request.extended)}"
        )

        # Write the configuration back to the device if requested.
        driver.write_config(
            config,
            password=request.password,
            extended=request.extended,
        )

        # Re-read the configuration to confirm the new configuration has been applied
        updated_config = driver.read_config(
            password=request.password,
            extended=request.extended,
        )

        # Print the current configuration (the hexadecimal dump is built inside DeviceConfigIO)
        logger.info(
            f"Written configuration:\n{updated_config.get_config_str(request.extended)}"
        )

        return driver_config_to_rs109m_config(updated_config)
