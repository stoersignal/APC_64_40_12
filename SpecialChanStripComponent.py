# http://remotescripts.blogspot.com

# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-

from _Framework.ChannelStripComponent import ChannelStripComponent
from _Framework.EncoderElement import EncoderElement # added
TRACK_FOLD_DELAY = 5
class SpecialChanStripComponent(ChannelStripComponent):
    ' Subclass of channel strip component using select button for (un)folding tracks '
    __module__ = __name__

    def __init__(self):
        ChannelStripComponent.__init__(self)
        self._toggle_fold_ticks_delay = -1
        # Status-bar messenger + hardware-listener bookkeeping
        # (quick-260505-sb9). Wired post-construction via set_messenger
        # from APC_64_40_9 once SpecialMixerComponent has built all 8 strips.
        # Each entry of _param_message_listeners: (control, callback).
        self._messenger = None
        self._param_message_listeners = []
        self._register_timer_callback(self._on_timer)

    def set_messenger(self, m):
        """Inject the StatusBarMessenger after construction. Called from
        APC_64_40_9 once per strip after SpecialMixerComponent setup."""
        self._messenger = m
        # If update() already ran (it does on construction), attach listeners
        # against the currently-bound controls now.
        if self._messenger is not None:
            self._refresh_param_message_listeners()

    def _teardown_param_message_listeners(self):
        for ctrl, cb in self._param_message_listeners:
            try:
                ctrl.remove_value_listener(cb)
            except Exception:
                pass
        self._param_message_listeners = []

    def _gather_owned_controls(self):
        """Return the slider + encoder controls currently owned by this
        strip. _send_controls is a tuple of EncoderElement (or None
        entries when the mode-selector wired only specific slots);
        guard each before yielding."""
        out = []
        out.append(getattr(self, '_volume_control', None))
        out.append(getattr(self, '_pan_control', None))
        sends = getattr(self, '_send_controls', None)
        if isinstance(sends, tuple):
            for s in sends:
                out.append(s)
        return out

    def _refresh_param_message_listeners(self):
        """Tear down + re-attach hardware-side message listeners on every
        currently-owned control. Called after the framework rebuilds
        bindings via update(), and on set_messenger."""
        self._teardown_param_message_listeners()
        if self._messenger is None:
            return
        for ctrl in self._gather_owned_controls():
            if ctrl is None:
                continue
            try:
                # Provider reads the bound parameter at fire-time (parameter()
                # is the framework's public accessor for _parameter_to_map_to).
                # Returns None if currently unbound -- the messenger callback
                # handles that case.
                cb = self._messenger.make_hardware_value_callback(
                    lambda c=ctrl: (c.parameter() if hasattr(c, 'parameter') else None))
                ctrl.add_value_listener(cb)
                self._param_message_listeners.append((ctrl, cb))
            except Exception:
                pass

    def update(self):
        # The framework's update() walks self._volume_control / _pan_control /
        # _send_controls and connect_to's the appropriate track param. Tear
        # down our parallel hardware-side listeners FIRST so the rebuild
        # below re-attaches against the new bindings; otherwise a track switch
        # would orphan the old listener entries (quick-260505-sb9).
        self._teardown_param_message_listeners()
        ChannelStripComponent.update(self)
        self._refresh_param_message_listeners()

    def disconnect(self):
        self._teardown_param_message_listeners()
        self._messenger = None
        self._unregister_timer_callback(self._on_timer)
        ChannelStripComponent.disconnect(self)

    def set_send_controls(self, controls): # override with pre 8.2.5 code
        assert ((controls == None) or isinstance(controls, tuple))
        if (controls != self._send_controls):
            self._send_controls = controls
            self.update()

    def set_pan_control(self, control): # override with pre 8.2.5 code
        assert ((control == None) or isinstance(control, EncoderElement))
        self._pan_control = control

    def set_volume_control(self, control): # override with pre 8.2.5 code
        assert ((control == None) or isinstance(control, EncoderElement))
        if (control != self._volume_control):
            self._volume_control = control
            self.update()        
                
    def _select_value(self, value):
        ChannelStripComponent._select_value(self, value)
        if (self.is_enabled() and (self._track != None)):
            if (self._track.is_foldable and (self._select_button.is_momentary() and (value != 0))):
                self._toggle_fold_ticks_delay = TRACK_FOLD_DELAY
            else:
                self._toggle_fold_ticks_delay = -1

    def _on_timer(self):
        if (self.is_enabled() and (self._track != None)):
            if (self._toggle_fold_ticks_delay > -1):
                assert self._track.is_foldable
                if (self._toggle_fold_ticks_delay == 0):
                    self._track.fold_state = (not self._track.fold_state)
                self._toggle_fold_ticks_delay -= 1


# local variables:
# tab-width: 4