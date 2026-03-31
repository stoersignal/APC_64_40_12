# http://remotescripts.blogspot.com

# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-

from _Framework.DeviceComponent import DeviceComponent


class Pan16DeviceComponent(DeviceComponent):
    """DeviceComponent that maps a sequential slice of device parameters.

    Used in Pan mode to map two encoder rows to device params 1-8 and 9-16.
    Overrides _parameter_banks() to return sequential 8-param chunks instead
    of the Framework's column-major interleaving (zip_longest pattern).
    """

    def __init__(self, bank_index):
        # No-arg call gives each instance its own fresh DeviceBankRegistry.
        DeviceComponent.__init__(self)
        self._fixed_bank_index = bank_index

    def set_device(self, device):
        # Parent resets _bank_index to 0 via get_device_bank() for unseen devices.
        # Re-assert our fixed bank after the parent call.
        DeviceComponent.set_device(self, device)
        if self._device is not None:
            self._bank_index = self._fixed_bank_index
            self.update()

    def _parameter_banks(self):
        # Override: sequential 8-param chunks instead of column-major interleaving.
        # Bank 0 = params[1:9], Bank 1 = params[9:17], Bank 2 = params[17:25], etc.
        if self._device is not None:
            params = list(self._device.parameters[1:])  # skip param 0 (device on/off)
            banks = []
            for i in range(0, len(params), 8):
                bank = params[i:i + 8]
                # Pad to 8 with None if fewer params remain
                bank += [None] * (8 - len(bank))
                banks.append(tuple(bank))
            return banks
        return []

    def _parameter_bank_names(self):
        if self._device is not None:
            count = self._number_of_parameter_banks()
            return ['Bank ' + str(i + 1) for i in range(count)]
        return []

    def _number_of_parameter_banks(self):
        if self._device is not None:
            params = list(self._device.parameters[1:])
            return max(1, (len(params) + 7) // 8)
        return 0

# local variables:
# tab-width: 4
