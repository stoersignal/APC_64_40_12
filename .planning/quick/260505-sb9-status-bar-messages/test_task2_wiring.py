#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wiring inspector for Task 2 (mode-event messenger plumbing).

Asserts the expected substrings appear in each modified file. NOT a
runtime test -- can't import the components outside Ableton because
they pull from `_Framework`. This is a static grep-and-ast inspector
matching the contract spelled out in the PLAN.

Exits 0 + prints "Task 2 OK" if all asserts pass.
"""

import ast
import os
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..'))


def slurp(rel):
    with open(os.path.join(REPO, rel)) as f:
        return f.read()


def assert_parse(rel):
    src = slurp(rel)
    ast.parse(src)
    return src


def must_contain(src, needle, where):
    assert needle in src, where + ' missing expected substring: ' + repr(needle)


# 1. APC_64_40_9.py instantiates StatusBarMessenger and passes it to every
#    mode-emitting component except ShiftableTransportComponent (Task 4).
src = assert_parse('APC_64_40_9.py')
must_contain(src, 'from .StatusBarMessenger import StatusBarMessenger',
             'APC_64_40_9.py')
must_contain(src, 'StatusBarMessenger(self)', 'APC_64_40_9.py')
must_contain(src, 'EncModeSelectorComponent(self._mixer, messenger=self._status_messenger)',
             'APC_64_40_9.py')
must_contain(src, 'MatrixModesComponent(self._matrix, self._session, self._session_zoom, '
             'tuple(self._track_stop_buttons), self, messenger=self._status_messenger)',
             'APC_64_40_9.py')
must_contain(src, 'EncoderAutoFilterComponent(self._mixer, self, messenger=self._status_messenger)',
             'APC_64_40_9.py')
must_contain(src, 'EncoderEQComponent(self._mixer, self, messenger=self._status_messenger)',
             'APC_64_40_9.py')
must_contain(src, 'messenger=self._status_messenger,', 'APC_64_40_9.py')


# 2. DrumRackModeComponent: messenger=None kwarg, _engage emits enter,
#    _disengage emits exit, disconnect nulls.
src = assert_parse('DrumRackModeComponent.py')
must_contain(src, 'messenger=None', 'DrumRackModeComponent.py')
must_contain(src, 'self._messenger = messenger', 'DrumRackModeComponent.py')
must_contain(src, "self._messenger.show_mode('Drum Rack Mode', True)",
             'DrumRackModeComponent.py')
must_contain(src, "self._messenger.show_mode('Drum Rack Mode', False)",
             'DrumRackModeComponent.py')
must_contain(src, 'was_active', 'DrumRackModeComponent.py')
must_contain(src, 'self._messenger = None', 'DrumRackModeComponent.py')


# 3. EncoderAutoFilterComponent: messenger=None kwarg, transition tracker,
#    show_mode on enter / exit, on_enabled_changed exit, disconnect nulls.
src = assert_parse('EncoderAutoFilterComponent.py')
must_contain(src, 'messenger=None', 'EncoderAutoFilterComponent.py')
must_contain(src, 'self._messenger = messenger', 'EncoderAutoFilterComponent.py')
must_contain(src, 'self._last_active_device', 'EncoderAutoFilterComponent.py')
must_contain(src, "show_mode('AutoFilter Mode', True)", 'EncoderAutoFilterComponent.py')
must_contain(src, "show_mode('AutoFilter Mode', False)", 'EncoderAutoFilterComponent.py')
must_contain(src, 'self._messenger = None', 'EncoderAutoFilterComponent.py')


# 4. EncoderEQComponent: same pattern.
src = assert_parse('EncoderEQComponent.py')
must_contain(src, 'messenger=None', 'EncoderEQComponent.py')
must_contain(src, 'self._messenger = messenger', 'EncoderEQComponent.py')
must_contain(src, 'self._last_active_eq_device', 'EncoderEQComponent.py')
must_contain(src, "show_mode('EQ Smart Control', True)", 'EncoderEQComponent.py')
must_contain(src, "show_mode('EQ Smart Control', False)", 'EncoderEQComponent.py')
must_contain(src, 'self._messenger = None', 'EncoderEQComponent.py')


# 5. EncModeSelectorComponent: messenger=None kwarg, _MODE_NAMES tuple,
#    show_event on transition, disconnect nulls.
src = assert_parse('EncModeSelectorComponent.py')
must_contain(src, 'messenger=None', 'EncModeSelectorComponent.py')
must_contain(src, 'self._messenger = messenger', 'EncModeSelectorComponent.py')
must_contain(src, '_MODE_NAMES', 'EncModeSelectorComponent.py')
must_contain(src, "'Encoder mode: '", 'EncModeSelectorComponent.py')
must_contain(src, 'self._messenger = None', 'EncModeSelectorComponent.py')


# 6. MatrixModesComponent: messenger=None kwarg, MATRIX_MODE_NAMES tuple,
#    show_event in set_mode, disconnect nulls.
src = assert_parse('MatrixModesComponent.py')
must_contain(src, 'messenger=None', 'MatrixModesComponent.py')
must_contain(src, 'self._messenger = messenger', 'MatrixModesComponent.py')
must_contain(src, 'MATRIX_MODE_NAMES', 'MatrixModesComponent.py')
must_contain(src, "'Clip Launch'", 'MatrixModesComponent.py')
must_contain(src, "'Global Variations'", 'MatrixModesComponent.py')
must_contain(src, "'Variations'", 'MatrixModesComponent.py')
must_contain(src, "'Matrix: '", 'MatrixModesComponent.py')
must_contain(src, 'self._messenger = None', 'MatrixModesComponent.py')


print('Task 2 OK')
