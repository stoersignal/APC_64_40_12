# http://remotescripts.blogspot.com

# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-

from _Framework.DeviceComponent import DeviceComponent


class Pan16DeviceComponent(DeviceComponent):
    """DeviceComponent fixed to a specific bank index.

    Used in Pan mode to map two encoder rows to device params 1-8 (bank 0)
    and params 9-16 (bank 1) simultaneously, with independent bank registries
    preventing cross-notification between instances.
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

# local variables:
# tab-width: 4
