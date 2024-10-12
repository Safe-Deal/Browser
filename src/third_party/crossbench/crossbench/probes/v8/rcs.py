# Copyright 2022 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import collections
import logging
from typing import TYPE_CHECKING, Optional, Union, cast

from crossbench.browsers.chromium.chromium import Chromium
from crossbench.probes.chromium_probe import ChromiumProbe
from crossbench.probes.probe import ProbeContext, ProbeMissingDataError
from crossbench.probes.results import LocalProbeResult, ProbeResult

if TYPE_CHECKING:
  from crossbench.browsers.browser import Browser
  from crossbench.path import LocalPath
  from crossbench.runner.groups.browsers import BrowsersRunGroup
  from crossbench.runner.groups.repetitions import (
      CacheTemperatureRepetitionsRunGroup, RepetitionsRunGroup)
  from crossbench.runner.groups.stories import StoriesRunGroup
  from crossbench.runner.run import Run


class V8RCSProbe(ChromiumProbe):
  """
  Chromium-only Probe to extract runtime-call-stats data that can be used
  to analyze precise counters and time spent in various VM components in V8:
  https://v8.dev/tools/head/callstats.html
  """
  NAME = "v8.rcs"

  def attach(self, browser: Browser) -> None:
    assert isinstance(browser, Chromium), "Expected Chromium-based browser."
    super().attach(browser)
    chromium = cast(Chromium, browser)
    chromium.js_flags.update(("--runtime-call-stats", "--allow-natives-syntax"))

  def get_context(self, run: Run) -> V8RCSProbeContext:
    return V8RCSProbeContext(self, run)

  def concat_group_files(self,
                         group: Union[RepetitionsRunGroup,
                                      CacheTemperatureRepetitionsRunGroup],
                         file_name: str) -> LocalPath:
    result_dir = group.get_local_probe_result_dir(self)
    result_files = (run.results[self].file for run in group.runs)
    result_file = self.runner_platform.concat_files(
        inputs=result_files,
        output=result_dir / file_name,
        prefix=f"\n== Page: {group.story.name}\n")
    return result_file

  def merge_repetitions(self, group: RepetitionsRunGroup) -> ProbeResult:
    all_file = self.concat_group_files(group, "all.rcs.txt")
    result_files = [all_file]
    for temperature_group in group.cache_temperature_repetitions_groups:
      temperature_file_name = f"{temperature_group.cache_temperature}.rcs.txt"
      group_file = self.concat_group_files(temperature_group,
                                           temperature_file_name)
      result_files.append(group_file)
    result_dir = group.get_local_probe_result_dir(self)
    self.runner_platform.symlink_or_copy(all_file,
                                         result_dir.with_suffix(".rcs.txt"))
    return LocalProbeResult(file=tuple(result_files))

  def merge_stories(self, group: StoriesRunGroup) -> ProbeResult:
    name_groups = collections.defaultdict(list)
    for repetition_group in group.repetitions_groups:
      for result_file in repetition_group.results[self].file_list:
        name_groups[result_file.name].append(result_file)

    result_dir = group.get_local_probe_result_dir(self)
    result_files = []
    for name, files in name_groups.items():
      result_files.append(
          self.runner_platform.concat_files(
              inputs=files, output=result_dir / name))
    src_file = result_dir / "all.rcs.txt"
    self.runner_platform.symlink_or_copy(src_file,
                                         result_dir.with_suffix(".rcs.txt"))
    return LocalProbeResult(file=(src_file,))

  def merge_browsers(self, group: BrowsersRunGroup) -> ProbeResult:
    # We put all the fils by in a toplevel v8.rcs folder
    result_dir = group.get_local_probe_result_dir(self)
    files = []
    for story_group in group.story_groups:
      story_group_file = story_group.results[self].file
      # Be permissive and skip failed probes
      if not story_group_file.exists():
        logging.info("Probe %s: skipping non-existing results file: %s",
                     self.NAME, story_group_file)
        continue
      dest_file = result_dir / f"{story_group.browser.unique_name}.rcs.txt"
      self.runner_platform.symlink_or_copy(story_group_file, dest_file)
      files.append(dest_file)
    return LocalProbeResult(file=files)


class V8RCSProbeContext(ProbeContext[V8RCSProbe]):
  _rcs_table: Optional[str] = None

  def setup(self) -> None:
    pass

  def start(self) -> None:
    pass

  def stop(self) -> None:
    with self.run.actions("Extract RCS") as actions:
      self._rcs_table = actions.js("return %GetAndResetRuntimeCallStats();")

  def teardown(self) -> ProbeResult:
    if not self._rcs_table:
      raise ProbeMissingDataError(
          "Chrome didn't produce any RCS data. "
          "Use Chrome Canary or make sure to enable the "
          "v8_enable_runtime_call_stats compile-time flag.")
    rcs_file = self.local_result_path.with_suffix(".rcs.txt")
    with rcs_file.open("a") as f:
      f.write(self._rcs_table)
    return LocalProbeResult(file=(rcs_file,))
