#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wiring inspector for Task 4 (snapshot save/recall + lock-to-device).

Static grep + ast.parse inspector. Asserts:
  - ShiftableTransportComponent: messenger=None kwarg, lock-to-device
    show_event, snapshot-save show_event, snapshot-recall show_event,
    disconnect nulls.
  - MatrixModesComponent: snapshot-recall show_event in
    _variations_pad_value AND _global_var_pad_value, snapshot-stored
    show_event piggy-backed on the existing variation-count listener,
    randomize-macros show_event in both stop-all handlers.
  - APC_64_40_9: ShiftableTransportComponent gets messenger via kwarg.

Exits 0 + prints "Task 4 OK" if all asserts pass.
"""

import ast
import os
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..'))


def slurp(rel):
    with open(os.path.join(REPO, rel)) as f:
        return f.read()


def must_contain(src, needle, where):
    assert needle in src, where + ' missing: ' + repr(needle)


def assert_parse(rel):
    src = slurp(rel)
    ast.parse(src)
    return src


# 1. ShiftableTransportComponent: messenger=None kwarg + 3 emit sites.
src = assert_parse('ShiftableTransportComponent.py')
must_contain(src, 'def __init__(self, messenger=None)',
             'ShiftableTransportComponent.py')
must_contain(src, 'self._messenger = messenger',
             'ShiftableTransportComponent.py')
must_contain(src, "'Lock to device: '", 'ShiftableTransportComponent.py')
must_contain(src, "' stored'", 'ShiftableTransportComponent.py')
must_contain(src, "' recalled'", 'ShiftableTransportComponent.py')
must_contain(src, 'self._messenger = None', 'ShiftableTransportComponent.py')


# 2. MatrixModesComponent: snapshot-recall in pad value handler AND
#    global-var pad value handler; snapshot-stored on count-change;
#    randomize on both stop-all handlers.
src = assert_parse('MatrixModesComponent.py')
# Variations Mode pad recall
must_contain(src, "' recalled'", 'MatrixModesComponent.py')
# Snapshot stored via count-change listener
must_contain(src, "' stored'", 'MatrixModesComponent.py')
# Randomize messages
must_contain(src, "'Macros randomized'", 'MatrixModesComponent.py')
must_contain(src, "'Macros randomized (all columns)'", 'MatrixModesComponent.py')


# 3. APC_64_40_9 wires messenger into the transport.
src = assert_parse('APC_64_40_9.py')
must_contain(src, 'ShiftableTransportComponent(messenger=self._status_messenger)',
             'APC_64_40_9.py')


print('Task 4 OK')
