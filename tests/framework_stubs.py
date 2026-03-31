# Minimal stubs for Ableton _Framework classes needed by tests
# These allow unit tests to run outside the Live environment

class TrackStub:
    def __init__(self, solo=False, mute=False):
        self.solo = solo
        self.mute = mute


class SongStub:
    def __init__(self):
        self._master_track = TrackStub()
        self.tracks = []
        self.return_tracks = []

    def master_track(self):
        return self._master_track


class ButtonStub:
    def __init__(self):
        self._state = 0

    def turn_on(self):
        self._state = 1

    def turn_off(self):
        self._state = 0

    def is_momentary(self):
        return True


class SpecialChanStripStub:
    """Minimal stub to allow ToggleMomentaryChannelStripComponent to be instantiated."""

    def __init__(self):
        self._track = None
        self._solo_button = None
        self._mute_button = None
        self._shift_pressed = False
        self._enabled = True
        self._ticks_delay = -1  # fold-delay (SpecialChanStripComponent)
        self._song = SongStub()

    def is_enabled(self):
        return self._enabled

    def song(self):
        return self._song

    def set_solo_button(self, button):
        self._solo_button = button

    def set_mute_button(self, button):
        self._mute_button = button

    def disconnect(self):
        pass

    def _on_timer(self):
        # Minimal: handle fold-delay (mirrors SpecialChanStripComponent._on_timer)
        if self._ticks_delay > -1:
            if self._ticks_delay == 0:
                pass  # threshold action (fold track) -- not needed in tests
            self._ticks_delay -= 1


class ParameterStub:
    """Minimal device parameter stub."""

    def __init__(self, name='param', value=0.5):
        self.name = name
        self.value = value
        self._connected_to = None


class EncoderStub:
    """Minimal encoder stub — tracks connect_to / release_parameter calls."""

    def __init__(self):
        self._parameter = None

    def connect_to(self, parameter):
        self._parameter = parameter

    def release_parameter(self):
        self._parameter = None


class DeviceStub:
    """Minimal Live.Device stub with a configurable parameter list."""

    def __init__(self, num_params=16):
        # Index 0 is always the device on/off parameter (ignored by bank mapping)
        self.parameters = [ParameterStub(f'param_{i}', 0.5) for i in range(num_params + 1)]
        self.class_name = 'InstrumentRack'
        self.name = 'TestDevice'
