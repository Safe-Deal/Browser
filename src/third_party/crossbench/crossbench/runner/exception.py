# Copyright 2024 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

class StopStoryException(Exception):
    """Exceptions thrown that resulted in the termination of the story."""
