# Copyright 2024 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import dataclasses
from typing import Optional
from typing_extensions import Self

from crossbench.benchmarks.loading.point import Point


@dataclasses.dataclass(frozen=False)
# Represents a rectangular section of the device's display.
class DisplayRectangle:
  # The top left corner of the rectangle.
  origin: Point
  # The width in pixels of the rectangle.
  width: int
  # The height in pixels of the rectangle.
  height: int

  # Stretches or squishes the rectangle by |factor|
  def __mul__(self, factor: float) -> Self:
    return DisplayRectangle(
        Point(round(self.origin.x * factor), round(self.origin.y * factor)),
        round(self.width * factor), round(self.height * factor))

  __rmul__ = __mul__

  def __bool__(self) -> bool:
    return self.width != 0 and self.height != 0

  # Translates the rectangle into |other|
  def shift_by(self, other: Self) -> Self:
    return DisplayRectangle(
        Point(self.origin.x + other.origin.x, self.origin.y + other.origin.y),
        self.width, self.height)

  @property
  def left(self) -> int:
    return self.origin.x

  @property
  def right(self) -> int:
    return self.origin.x + self.width

  @property
  def top(self) -> int:
    return self.origin.y

  @property
  def bottom(self) -> int:
    return self.origin.y + self.height

  @property
  def mid_x(self) -> int:
    return round(self.origin.x + (self.width / 2))

  @property
  def mid_y(self) -> int:
    return round(self.origin.y + (self.height / 2))

  @property
  def middle(self) -> Point:
    return Point(self.mid_x, self.mid_y)
