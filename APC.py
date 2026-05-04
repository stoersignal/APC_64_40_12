# http://remotescripts.blogspot.com


import Live
import random
from _Framework.ControlSurface import ControlSurface
MANUFACTURER_ID = 71
ABLETON_MODE = 65
DO_COMBINE = False
if hasattr(Live.Application, 'combine_apcs'):
    try:
        DO_COMBINE = Live.Application.combine_apcs()
    except:
        pass


class APC(ControlSurface):
    """ Script for Akai's line of APC Controllers """
    _active_instances = []

    def _combine_active_instances():
        support_devices = False
        for instance in APC._active_instances:
            support_devices |= instance._device_component != None

        track_offset = 0
        for instance in APC._active_instances:
            instance._activate_combination_mode(track_offset, support_devices)
            track_offset += instance._session.width()

    _combine_active_instances = staticmethod(_combine_active_instances)

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self._suppress_session_highlight = True
            self._suppress_send_midi = True
            self._suggested_input_port = 'Akai ' + self.__class__.__name__
            self._suggested_output_port = 'Akai ' + self.__class__.__name__
            self._shift_button = None
            self._matrix = None
            self._session = None
            self._session_zoom = None
            self._mixer = None
            self._setup_session_control()
            self._setup_mixer_control()
            self._session.set_mixer(self._mixer)
            self._shift_button.name = 'Shift_Button'
            self._setup_custom_components()
            self.set_highlighting_session_component(self._session)
            for component in self.components:
                component.set_enabled(False)

        self._device_id = 0
        self._common_channel = 0
        self._dongle_challenge = (random.randint(0, 2000000), random.randint(2000001, 4000000))

    def disconnect(self):
        self._do_uncombine()
        self._shift_button = None
        self._matrix = None
        self._session = None
        self._session_zoom = None
        self._mixer = None
        ControlSurface.disconnect(self)

    def refresh_state(self):
        ControlSurface.refresh_state(self)
        self.schedule_message(5, self._update_hardware)

    def handle_sysex(self, midi_bytes):
        self._suppress_send_midi = False
        if midi_bytes[3] == 6 and midi_bytes[4] == 2:
            self._on_identity_response(midi_bytes)
        elif midi_bytes[4] == 81:
            self._on_dongle_response(midi_bytes)

    def _on_identity_response(self, midi_bytes):
        if midi_bytes[5] == MANUFACTURER_ID and midi_bytes[6] == self._product_model_id_byte():
            version_bytes = midi_bytes[9:13]
            self._device_id = midi_bytes[13]
            self._send_introduction_message()
            message = self.__class__.__name__ + ': Got response from controller, version ' + str((version_bytes[0] << 4) + version_bytes[1]) + '.' + str((version_bytes[2] << 4) + version_bytes[3])
            self.log_message(message)
            # Bypass dongle challenge - enable components directly
            self._on_handshake_successful()

    def _on_dongle_response(self, midi_bytes):
        if midi_bytes[1] == MANUFACTURER_ID and midi_bytes[3] == self._product_model_id_byte() and midi_bytes[2] == self._device_id and midi_bytes[5] == 0:
            if midi_bytes[6] == 16:
                # Bypass the deprecated encrypt_challenge verification and enable directly
                self._on_handshake_successful()

    def _on_handshake_successful(self):
        self._suppress_session_highlight = False
        for component in self.components:
            component.set_enabled(True)

        self._on_selected_track_changed()
        self._do_combine()

    def _update_hardware(self):
        self._suppress_send_midi = True
        self._suppress_session_highlight = True
        with self.component_guard():
            for component in self.components:
                component.set_enabled(False)

        self._suppress_send_midi = False
        self._do_uncombine()
        self._send_midi((240, 126, 0, 6, 1, 247))

    def _set_session_highlight(self, track_offset, scene_offset, width, height, include_return_tracks):
        if not self._suppress_session_highlight or (track_offset,
         scene_offset,
         width,
         height) == (-1, -1, -1, -1):
            ControlSurface._set_session_highlight(self, track_offset, scene_offset, width, height, include_return_tracks)

    def _send_midi(self, midi_bytes, optimized = None):
        sent_successfully = False
        if not self._suppress_send_midi:
            sent_successfully = ControlSurface._send_midi(self, midi_bytes, optimized=optimized)
        return sent_successfully

    def _send_introduction_message(self, mode_byte = ABLETON_MODE):
        # Try to get version info, fallback to defaults if deprecated API
        try:
            major = self.application().get_major_version()
            minor = self.application().get_minor_version()
            bugfix = self.application().get_bugfix_version()
        except AttributeError:
            # Fallback for Live 12+ where these methods are deprecated
            major = 12
            minor = 0
            bugfix = 0
        self._send_midi((240,
         MANUFACTURER_ID,
         self._device_id,
         self._product_model_id_byte(),
         96,
         0,
         4,
         mode_byte,
         major,
         minor,
         bugfix,
         247))

    def _activate_combination_mode(self, track_offset, support_devices):
        self._session.link_with_track_offset(track_offset)

    def _do_combine(self):
        if DO_COMBINE and self not in APC._active_instances:
            APC._active_instances.append(self)
            APC._combine_active_instances()

    def _do_uncombine(self):
        if self in APC._active_instances:
            APC._active_instances.remove(self)
            self._session.unlink()
            APC._combine_active_instances()

    def _setup_session_control(self):
        raise AssertionError('Function _setup_session_control must be overridden by subclass')




    def _setup_mixer_control(self):
        raise AssertionError('Function _setup_mixer_control must be overridden by subclass')




    def _setup_custom_components(self):
        raise AssertionError('Function _setup_custom_components must be overridden by subclass')




    def _product_model_id_byte(self):
        raise AssertionError('Function _product_model_id_byte must be overridden by subclass')