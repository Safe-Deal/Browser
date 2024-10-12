# Copyright 2024 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# pytype: skip-file

# This script is to be run directly on a ChromeOS device to query and return
# the touch device information.
import sys

sys.path.append("/usr/local/autotest/bin")

import common
import logging
from autotest_lib.client.bin.input import input_device
from autotest_lib.client.cros.input_playback import input_playback

logging.disable(logging.ERROR)

playback = input_playback.InputPlayback()
playback.find_connected_inputs()
touchscreen_node = playback.devices["touchscreen"].node
touchscreen = input_device.InputDevice(touchscreen_node)
print(touchscreen_node, touchscreen.get_x_max(), touchscreen.get_y_max())