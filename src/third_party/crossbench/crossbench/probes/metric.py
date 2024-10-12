# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import json
import logging
import math
from math import floor, log10
from typing import (TYPE_CHECKING, Any, Callable, Dict, Hashable, Iterable,
                    List, Optional, Sequence, Set, Tuple, Union)

from crossbench.probes import helper

if TYPE_CHECKING:
  from crossbench.path import LocalPath
  from crossbench.types import Json, JsonDict



def is_number(value: Any) -> bool:
  return isinstance(value, (int, float))


class Metric:
  """
  Metric provides simple statistical getters if the collected values are
  ints or floats only.
  """

  @classmethod
  def format(cls,
             value: Union[float, int],
             stddev: Optional[float] = None) -> str:
    """Format value and stdev to only expose significant + 1 digits.
    Example outputs:
      100 ± 10%
      100.1 ± 1.2%
      100.12 ± 0.12%
      100.123 ± 0.012%
      100.1235 ± 0.0012%
    """
    if not stddev:
      return str(value)
    stddev = float(stddev)
    stddev_significant_digit = int(floor(log10(abs(stddev))))
    value_width = max(0, 1 - stddev_significant_digit)
    percent = stddev / value * 100
    percent_significant_digit = int(floor(log10(abs(percent))))
    percent_width = max(0, 1 - percent_significant_digit)
    return f"{value:.{value_width}f} ± {percent:.{percent_width}f}%"

  @classmethod
  def from_json(cls, json_data: JsonDict) -> Metric:
    values = json_data["values"]
    assert isinstance(values, list)
    return cls(values)

  def __init__(self, values: Optional[List] = None) -> None:
    self.values = values or []
    self._is_numeric: bool = all(map(is_number, self.values))

  def __len__(self) -> int:
    return len(self.values)

  @property
  def is_numeric(self) -> bool:
    return self._is_numeric

  @property
  def min(self) -> float:
    assert self._is_numeric
    return min(self.values)

  @property
  def max(self) -> float:
    assert self._is_numeric
    return max(self.values)

  @property
  def sum(self) -> float:
    assert self._is_numeric
    return sum(self.values)

  @property
  def average(self) -> float:
    assert self._is_numeric
    return sum(self.values) / len(self.values)

  @property
  def geomean(self) -> float:
    assert self._is_numeric
    return geomean(self.values)

  @property
  def stddev(self) -> float:
    assert self._is_numeric
    # We're ignoring here any actual distribution of the data and use this as a
    # rough estimate of the quality of the data
    average = self.average
    variance = 0.0
    for value in self.values:
      variance += (average - value)**2
    variance /= len(self.values)
    return math.sqrt(variance)

  def append(self, value: Any) -> None:
    self.values.append(value)
    self._is_numeric = self._is_numeric and is_number(value)

  def to_json(self) -> JsonDict:
    json_data: JsonDict = {"values": self.values}
    if not self.values:
      return json_data
    if self.is_numeric:
      json_data["min"] = self.min
      average = json_data["average"] = self.average
      json_data["geomean"] = self.geomean
      json_data["max"] = self.max
      json_data["sum"] = self.sum
      stddev = json_data["stddev"] = self.stddev
      if average == 0:
        json_data["stddevPercent"] = 0
      else:
        json_data["stddevPercent"] = (stddev / average) * 100
      return json_data
    # Try to simplify repeated non-numeric values
    if not isinstance(self.values[0], Hashable):
      return json_data
    if len(set(self.values)) == 1:
      return self.values[0]
    return json_data


def geomean(values: Iterable[Union[int, float]]) -> float:
  product: float = 1
  length: int = 0
  for value in values:
    product *= value
    length += 1
  return product**(1 / length)


def metric_geomean(metric: Metric) -> float:
  return metric.geomean


class MetricsMerger:
  """
  Merges hierarchical data into 1-level aggregated data;

  Input:
  data_1 ={
    "a": {
      "aa": 1.1,
      "ab": 2
    }
    "b": 2.1
  }
  data_2 = {
    "a": {
      "aa": 1.2
    }
    "b": 2.2,
    "c": 2
  }

  The merged data maps str => Metric():

  MetricsMerger(data_1, data_2).data == {
    "a/aa": Metric(1.1, 1.2)
    "a/ab": Metric(2)
    "b":    Metric(2.1, 2.2)
    "c":    Metric(2)
  }
  """

  @classmethod
  def merge_json_list(cls,
                      files: Iterable[LocalPath],
                      key_fn: Optional[helper.KeyFnType] = None,
                      merge_duplicate_paths: bool = False) -> MetricsMerger:
    merger = cls(key_fn=key_fn)
    for file in files:
      with file.open(encoding="utf-8") as f:
        merger.merge_values(
            json.load(f), merge_duplicate_paths=merge_duplicate_paths)
    return merger

  def __init__(self,
               *args: Union[Dict, List[Dict]],
               key_fn: Optional[helper.KeyFnType] = None):
    """Create a new MetricsMerger

    Args:
        *args (optional): Optional hierarchical data to be merged.
        key_fn (optional): Maps property paths (Tuple[str,...]) to strings used
          as keys to group/merge values, or None to skip property paths.
    """
    self._data: Dict[str, Metric] = {}
    self._key_fn: helper.KeyFnType = key_fn or helper._default_flatten_key_fn
    self._ignored_keys: Set[str] = set()
    for data in args:
      self.add(data)

  @property
  def data(self) -> Dict[str, Metric]:
    return self._data

  def merge_values(self,
                   data: Dict[str, Dict],
                   prefix_path: Tuple[str, ...] = (),
                   merge_duplicate_paths: bool = False) -> None:
    """Merge a previously json-serialized MetricsMerger object"""
    for property_name, item in data.items():
      path = prefix_path + (property_name,)
      key = self._key_fn(path)
      if key is None or key in self._ignored_keys:
        continue
      if key in self._data:
        if merge_duplicate_paths:
          values = self._data[key]
          for value in item["values"]:
            values.append(value)
        else:
          logging.debug(
              "Removing Metric with the same key-path='%s', key='%s"
              "from multiple files.", path, key)
          del self._data[key]
          self._ignored_keys.add(key)
      else:
        self._data[key] = Metric.from_json(item)

  def add(self, data: Union[Dict, List[Dict]]) -> None:
    """ Merge "arbitrary" hierarchical data that ends up having primitive leafs.
    Anything that is not a dict is considered a leaf node.
    """
    if isinstance(data, list):
      # Assume that top-level lists are repetitions of the same data
      for item in data:
        self._merge(item)
    else:
      self._merge(data)

  def _merge(
      self, data: Union[Dict,
                        List[Dict]], parent_path: Tuple[str, ...] = ()) -> None:
    assert isinstance(data, dict)
    for property_name, value in data.items():
      path = parent_path + (property_name,)
      key: Optional[str] = self._key_fn(path)
      if key is None:
        continue
      if isinstance(value, dict):
        self._merge(value, path)
      else:
        if key in self._data:
          values = self._data[key]
        else:
          values = self._data[key] = Metric()
        if isinstance(value, list):
          for v in value:
            values.append(v)
        else:
          values.append(value)

  def to_json(self,
              value_fn: Optional[Callable[[Any], Json]] = None,
              sort: bool = True) -> JsonDict:
    items = []
    for key, value in self._data.items():
      assert isinstance(value, Metric)
      if value_fn is None:
        json_value: Json = value.to_json()
      else:
        json_value = value_fn(value)
      items.append((key, json_value))
    if sort:
      # Make sure the data is always in the same order, independent of the input
      # order
      items.sort()
    return dict(items)


class CSVFormatter:
  """
  Headers: [
    ["label_1", "value_1"],
    ["label_2", "value_2"],
  ]
  Input: {
      "A_1/B_1/Async": 1,
      "A_1/B_2/Sync": 2,
      "A_1/Total": 3,
      "Total": 3,
    }
  Output: [
    ["label_1",      "",      "",      "",      "value_1],
    ["label_2",      "",      "",      "",      "value_2],
    ["A_1/B1/Async", "A1",    "B1",    "Async", 1],
    ["A_1/B2/Sync",  "A1",    "B2",    "Sync",  2],
    ["A_1/Total",    "A1",    "Total", "",      3],
    ["Total"         "Total", "",      "",      3],
  ]
  """

  def __init__(self,
               metrics: MetricsMerger,
               value_fn: Optional[Callable[[Any], Any]] = None,
               headers: Sequence[Tuple[Any, ...]] = (),
               include_parts: bool = True,
               sort: bool = True):
    self._table: List[Sequence[Any]] = []
    converted = metrics.to_json(value_fn, sort)
    items = self.format_items(converted, sort=sort)
    max_path_depth: int = self.extract_max_depth(items, include_parts)
    self.append_headers(headers, max_path_depth)
    self.append_body(items, include_parts, max_path_depth)

  def extract_max_depth(self, items: Sequence[Tuple[str, Json]],
                        include_parts: bool) -> int:
    max_path_depth = 0
    if include_parts:
      for path, _ in items:
        max_path_depth = max(max_path_depth, path.count("/"))
    max_path_depth += 1
    return max_path_depth

  def append_headers(self, headers, max_path_depth: int) -> None:
    header_padding = ("",) * max_path_depth
    for header in headers:
      assert isinstance(header, tuple), (
          f"Additional CSV headers must be tuples, got {type(header)}: "
          f"{header}")
      row = header[:1] + header_padding + header[1:]
      self._table.append(row)

  def append_body(self, items: Sequence[Tuple[str, Json]], include_parts: bool,
                  max_path_depth: int) -> None:
    for path, value in items:
      if include_parts:
        parts = tuple(path.split("/"))
        buffer = ("",) * (max_path_depth - len(parts))
        row = (path,) + parts + buffer + (value,)
      else:
        row = (path, value)
      self._table.append(row)

  def format_items(self, data: Dict[str, Json],
                   sort: bool) -> Sequence[Tuple[str, Json]]:
    items = tuple(data.items())
    if not sort:
      return items
    return sorted(items)

  @property
  def table(self) -> List[Sequence[Any]]:
    return self._table
