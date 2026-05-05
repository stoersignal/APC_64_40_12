# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-
"""
StatusBarMessenger -- centralized Application.show_message helper for the
APC40 script. Quick task 260505-sb9.

Single chokepoint for all transient bottom-status feedback. Components own
the WHEN (mode-transition path, hardware listener, etc.) and pass formatted
text via three public methods:

  show_mode(mode_name, entered)            -- mode entry/exit
  show_event(text)                         -- arbitrary one-liner
  show_param(param_name, formatted, param_id=None)
                                           -- parameter-value change (throttled)

Behavioural guarantees (locked decisions D-01..D-06 and gotchas #6/#7):
  - Cold-start silence: messages emitted within COLD_START_QUIET_MS
    (default 2000) of construction time are dropped silently. Stops the
    handshake-time setup paint from spamming the user.
  - Identical-text dedup: if the about-to-emit string equals the last
    emitted string AND the dedup window is still open (4*THROTTLE_MS),
    the call is dropped. Prevents flicker on rapid same-text events.
  - show_param throttle: same param_id within THROTTLE_MS (default 50ms)
    is dropped. Different param_id always emits immediately. Mode events
    bypass throttling entirely (they fire infrequently).
  - Fail-quiet: every public method wraps its body in try/except so a
    misbehaving parent (e.g. application() returning None mid-teardown)
    never crashes the caller. The project idiom is silent failure over
    a stack trace mid-set.

Module imports nothing from Live or _Framework -- the caller passes a
parent ControlSurface in the constructor and we use parent.application()
at emit-time. Keeps the file unit-testable outside Ableton.
"""

import time


class StatusBarMessenger(object):
    """Centralized Application.show_message helper. See module docstring."""

    THROTTLE_MS = 50            # D-04 -- per-param debounce window
    COLD_START_QUIET_MS = 2000  # gotcha #7 -- handshake-time silence
    DEDUP_WINDOW_MS = 200       # 4 * THROTTLE_MS -- identical-text dedup window

    def __init__(self, parent):
        # parent = the ControlSurface (APC_64_40_9 instance). Stored so we
        # can call parent.song().show_message(...) at emit-time. song() is
        # queried lazily because on cold boot it can raise (handshake not
        # complete yet) -- the cold-start gate below covers that window,
        # but we also catch in _emit.
        self._parent = parent
        self._construct_ms = self._now_ms()
        # show_param throttle keyed on id(param). None means "no last param".
        self._last_param_id = None
        self._last_param_emit_ms = 0.0
        # Identical-text dedup. _last_text reset to None after DEDUP_WINDOW_MS
        # of inactivity so a deliberate re-display works after a pause.
        self._last_text = None
        self._last_text_ms = 0.0

    # -- timing utilities ----------------------------------------------------

    def _now_ms(self):
        # time.time() returns seconds-since-epoch as float; *1000 -> ms.
        return time.time() * 1000.0

    def _is_cold_start(self):
        return (self._now_ms() - self._construct_ms) < self.COLD_START_QUIET_MS

    # -- single emit chokepoint ---------------------------------------------

    def _emit(self, text):
        """Try multiple show_message dispatch strategies until one
        succeeds. Live 11/12 binding has been seen to reject single-arg
        Application.show_message(str) with a TText/buttons/enable_markup/
        show_success_icon C++ signature mismatch; Song.show_message also
        not always available; explicit-defaults form sometimes satisfies
        Boost.Python binding. We try in order and log which one wins.
        Round-2 fix removed once we confirm which path works on this
        Live build."""
        try:
            if self._parent is None:
                return
        except Exception:
            return

        # Each strategy returns (sent_bool, label_str_for_log).
        strategies = (
            ('song.show_message(text)',
             lambda: self._try_song_show_message(text)),
            ('app.show_message(text)',
             lambda: self._try_app_show_message_simple(text)),
            ('app.show_message(text, 0, False, False)',
             lambda: self._try_app_show_message_full(text)),
        )

        for label, fn in strategies:
            try:
                ok, exc_text = fn()
            except Exception as exc:
                ok, exc_text = False, type(exc).__name__ + ': ' + str(exc)
            if ok:
                self._last_text = text
                self._last_text_ms = self._now_ms()
                # One-shot log per success-strategy so the next UAT round
                # tells us which form Live 11/12 accepts. Logged ONCE per
                # text via _last_text comparison so we don't spam.
                if not getattr(self, '_logged_winner_' + label, False):
                    try:
                        self._parent.log_message(
                            '[StatusBar] WINNER strategy=' + repr(label) +
                            ' text=' + repr(text))
                    except Exception:
                        pass
                    setattr(self, '_logged_winner_' + label, True)
                return
            else:
                if not getattr(self, '_logged_loser_' + label, False):
                    try:
                        self._parent.log_message(
                            '[StatusBar] FAIL strategy=' + repr(label) +
                            ' err=' + repr(exc_text))
                    except Exception:
                        pass
                    setattr(self, '_logged_loser_' + label, True)
        # All strategies failed -- fail quiet.

    def _try_song_show_message(self, text):
        try:
            song = self._parent.song()
            if song is None:
                return False, 'song() is None'
            song.show_message(text)
            return True, None
        except Exception as exc:
            return False, type(exc).__name__ + ': ' + str(exc)

    def _try_app_show_message_simple(self, text):
        try:
            app = self._parent.application()
            if app is None:
                return False, 'application() is None'
            app.show_message(text)
            return True, None
        except Exception as exc:
            return False, type(exc).__name__ + ': ' + str(exc)

    def _try_app_show_message_full(self, text):
        try:
            app = self._parent.application()
            if app is None:
                return False, 'application() is None'
            # Match the C++ signature exactly: text, buttons, enable_markup,
            # show_success_icon. The first error message hinted that
            # Boost.Python isn't auto-filling defaults on this build.
            app.show_message(text, 0, False, False)
            return True, None
        except Exception as exc:
            return False, type(exc).__name__ + ': ' + str(exc)

    def _check_dedup(self, text):
        """Return True if `text` should be dropped due to identical-text
        dedup. Reset _last_text if the dedup window has expired so a
        repeat after a pause is allowed."""
        if self._last_text is None:
            return False
        if (self._now_ms() - self._last_text_ms) > self.DEDUP_WINDOW_MS:
            # Window expired -- forget the last text; allow same text again.
            self._last_text = None
            return False
        return text == self._last_text

    # -- public API ----------------------------------------------------------

    def show_mode(self, mode_name, entered):
        """Mode-entry/exit message per D-06 rows 1+2.
          entered=True  -> "<mode_name>"
          entered=False -> "<mode_name> exited"
        Bypasses param throttle; honors cold-start silence + identical-
        text dedup."""
        try:
            if self._is_cold_start():
                return
            text = mode_name if entered else (str(mode_name) + ' exited')
            if self._check_dedup(text):
                return
            self._emit(text)
        except Exception:
            pass

    def show_event(self, text):
        """Arbitrary one-shot message per D-06 rows 3-7. Bypasses param
        throttle; honors cold-start silence + identical-text dedup."""
        try:
            if self._is_cold_start():
                return
            if self._check_dedup(text):
                return
            self._emit(text)
        except Exception:
            pass

    def show_param(self, param_name, formatted_value, param_id=None):
        """Parameter-value change per D-06 row 8.
          text = "<param_name>: <formatted_value>"
        Throttle: same param_id within THROTTLE_MS -> drop. Different
        param_id OR elapsed > THROTTLE_MS -> emit. param_id=None bypasses
        the throttle (caller signalled a one-off). Honors cold-start
        silence + identical-text dedup."""
        try:
            if self._is_cold_start():
                return
            now = self._now_ms()
            if param_id is not None and param_id == self._last_param_id:
                if (now - self._last_param_emit_ms) < self.THROTTLE_MS:
                    return
            text = str(param_name) + ': ' + str(formatted_value)
            if self._check_dedup(text):
                # Dedup also updates the param-emit clock so the next non-
                # duplicate same-param call still respects the throttle.
                self._last_param_id = param_id
                self._last_param_emit_ms = now
                return
            self._last_param_id = param_id
            self._last_param_emit_ms = now
            self._emit(text)
        except Exception:
            pass

    # -- factory for hardware-control listeners (Task 3) --------------------

    def make_hardware_value_callback(self, param_provider, name_provider=None):
        """Build a value-listener callback for an APC40 hardware control
        (EncoderElement / SliderElement / ButtonElement). On every MIDI-
        driven value event the callback reads the bound parameter's
        current value, formats via str_for_value (with repr fallback),
        and dispatches show_param.

        param_provider: zero-arg callable returning the bound Live
          Parameter (or None if currently unbound). Called at fire-time,
          NOT cached at registration -- the binding may change as the
          user switches modes / tracks. If it raises, the callback
          fails quiet.

        name_provider: optional zero-arg callable returning the display
          name. Defaults to param.name with original_name fallback.
        """
        messenger = self  # capture for closure
        def _cb(value):
            try:
                param = param_provider()
                if param is None:
                    return
                # Format the current value via Live's str_for_value (UI-
                # accurate, with units). Fall back to repr if the param
                # type doesn't implement it.
                try:
                    fmt = param.str_for_value(param.value)
                except Exception:
                    try:
                        fmt = repr(param.value)
                    except Exception:
                        return
                # Resolve display name. Try the caller-provided name_provider
                # first, then param.name, then param.original_name, then '?'.
                if name_provider is not None:
                    try:
                        nm = name_provider()
                    except Exception:
                        nm = (getattr(param, 'name', None)
                              or getattr(param, 'original_name', '?'))
                else:
                    nm = (getattr(param, 'name', None)
                          or getattr(param, 'original_name', '?'))
                messenger.show_param(nm, fmt, param_id=id(param))
            except Exception:
                # Fail-quiet -- never crash the MIDI processing loop.
                pass
        return _cb


# local variables:
# tab-width: 4
