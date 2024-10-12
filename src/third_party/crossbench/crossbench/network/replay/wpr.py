# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import abc
import contextlib
import hashlib
import logging
from typing import TYPE_CHECKING, Iterator, List, Optional, Union

from crossbench.flags.base import Flags
from crossbench.helper.path_finder import WprGoToolFinder
from crossbench.network.replay.base import GS_PREFIX, WPR_CACHE, ReplayNetwork
from crossbench.network.replay.web_page_replay import WprReplayServer
from crossbench.parse import PathParser
from crossbench.plt import PLATFORM, Platform
from crossbench.plt.arch import MachineArch

if TYPE_CHECKING:
  from crossbench.browsers.browser import Browser
  from crossbench.network.base import TrafficShaper
  from crossbench.path import AnyPath, LocalPath
  from crossbench.runner.groups.session import BrowserSessionRunGroup


# use value for pylint
assert GS_PREFIX

WPR_PREBUILT_ARCH_MAP = {
  MachineArch.ARM_64: {
    "url": "gs://chromium-telemetry/binary_dependencies/wpr_go_129a66a1378dfcbb815596f66ca680728f77da36",
    "file_hash": "129a66a1378dfcbb815596f66ca680728f77da36",
  },
  MachineArch.ARM_32: {
    "url": "gs://chromium-telemetry/binary_dependencies/wpr_go_92ff5bdb9370b36d2844c2f018e2b7d9c3b8ed39",
    "file_hash": "92ff5bdb9370b36d2844c2f018e2b7d9c3b8ed39",
  },
  MachineArch.X64: {
    "url": "gs://chromium-telemetry/binary_dependencies/wpr_go_6caa467dc6bef92e1c34256f539f8ed8f26a2fe1",
    "file_hash": "6caa467dc6bef92e1c34256f539f8ed8f26a2fe1",
  },
}


def check_hash(file_path: LocalPath, file_hash: str) -> bool:
  if not file_path.exists():
    return False
  sha1 = hashlib.sha1()
  sha1.update(file_path.read_bytes())
  return sha1.hexdigest() == file_hash


class WprReplayNetwork(ReplayNetwork):

  def __init__(self,
               archive: Union[LocalPath, str],
               traffic_shaper: Optional[TrafficShaper] = None,
               wpr_go_bin: Optional[LocalPath] = None,
               browser_platform: Platform = PLATFORM,
               persist_server: bool = False):
    super().__init__(archive, traffic_shaper, browser_platform)
    self._server: Optional[WprReplayServer] = None
    self._tmp_dir: Optional[AnyPath] = None
    self._persist_server = persist_server
    self._ensure_wpr_go(wpr_go_bin)

  def extra_flags(self, browser: Browser) -> Flags:
    assert self.is_running, "Extra network flags are not valid"
    assert self._server
    if not browser.attributes.is_chromium_based:
      raise ValueError(
          "Only chromium-based browsers are supported for wpr replay.")
    # TODO: make ports configurable.
    extra_flags = super().extra_flags(browser)
    # TODO: read this from wpr_public_hash.txt like in the recorder probe
    extra_flags["--ignore-certificate-errors-spki-list"] = (
        "PhrPvGIaAMmd29hj8BCZOq096yj7uMpRNHpn5PDxI6I=,"
        "2HcXCSKKJS0lEXLQEWhpHUfGuojiU0tiT5gOF9LP6IQ=")
    if self._traffic_shaper.is_live:
      # Only remap ports if we're not using the SOCKS proxy from the traffic
      # shaper.
      extra_flags["--host-resolver-rules"] = (
          f"MAP *:80 {self.host}:{self.http_port},"
          f"MAP *:443 {self.host}:{self.https_port},"
          "EXCLUDE localhost")

    return extra_flags

  @abc.abstractmethod
  def _ensure_wpr_go(self, wpr_go_bin: Optional[LocalPath] = None):
    pass

  @abc.abstractmethod
  def _create_server(self, log_dir: LocalPath) -> WprReplayServer:
    pass

  @contextlib.contextmanager
  def open(self, session: BrowserSessionRunGroup) -> Iterator[ReplayNetwork]:
    with super().open(session):
      yield self

  def _ensure_server_started(self, session: BrowserSessionRunGroup):
    log_dir = session.browser_dir if self._persist_server else session.out_dir
    if not self._server or not self._persist_server:
      self._server = self._create_server(log_dir)
      logging.debug("Starting WPR server")
      self._server.start()
    else:
      # TODO: reset wpr server state for reuse
      logging.debug("WPR server already started")

  @contextlib.contextmanager
  def _open_replay_server(self, session: BrowserSessionRunGroup):
    self._ensure_server_started(session)

    try:
      yield self
    finally:
      if not self._persist_server:
        self._server.stop()

  @property
  def http_port(self) -> int:
    assert self._server, "WPR is not running"
    return self._server.http_port

  @property
  def https_port(self) -> int:
    assert self._server, "WPR is not running"
    return self._server.https_port

  @property
  def host(self) -> str:
    assert self._server, "WPR is not running"
    return self._server.host

  def __str__(self) -> str:
    return f"WPR(archive={self.archive_path}, speed={self.traffic_shaper})"


class LocalWprReplayNetwork(WprReplayNetwork):

  def _ensure_wpr_go(self, wpr_go_bin: Optional[LocalPath] = None):
    if not wpr_go_bin:
      if local_wpr_go := WprGoToolFinder(self.runner_platform).path:
        wpr_go_bin = self.runner_platform.local_path(local_wpr_go)
    if not wpr_go_bin:
      raise RuntimeError(
          f"Could not find wpr.go binary on {self.runner_platform}")
    if wpr_go_bin.suffix == ".go" and not self.runner_platform.which("go"):
      raise ValueError(f"'go' binary not found on {self.runner_platform}")
    self._wpr_go_bin: LocalPath = self.runner_platform.local_path(
        PathParser.binary_path(wpr_go_bin, "wpr.go source"))

  @contextlib.contextmanager
  def open(self, session: BrowserSessionRunGroup) -> Iterator[ReplayNetwork]:
    with super().open(session):
      with self._forward_ports(session):
        yield self

  @contextlib.contextmanager
  def _forward_ports(self, session: BrowserSessionRunGroup) -> Iterator:
    browser_platform = session.browser_platform
    if not self._traffic_shaper.is_live or not browser_platform.is_remote:
      yield
      return
    http_port = self.http_port
    https_port = self.https_port
    logging.info("REMOTE PORT FORWARDING: %s <= %s", self.runner_platform,
                 browser_platform)
    # TODO: create port-forwarder service that is shut down properly.
    # TODO: make ports configurable
    browser_platform.reverse_port_forward(http_port, http_port)
    browser_platform.reverse_port_forward(https_port, https_port)
    yield
    browser_platform.stop_reverse_port_forward(http_port)
    browser_platform.stop_reverse_port_forward(https_port)

  def _create_server(self, log_dir: LocalPath) -> WprReplayServer:
    return WprReplayServer(
        self.archive_path,
        self._wpr_go_bin,
        log_path=log_dir / "network.wpr.log",
        platform=self.runner_platform)


class RemoteWprReplayNetwork(WprReplayNetwork):

  def _ensure_wpr_go(self, wpr_go_bin: Optional[LocalPath] = None):
    assert self.browser_platform.is_android
    if wpr_go_bin:
      if wpr_go_bin.suffix == ".go":
        raise ValueError(f"Can't run .go files on {self.browser_platform}")
    else:
      wpr_go_bin = self._download_prebuilt_wpr()
    self._wpr_go_bin: LocalPath = self.runner_platform.local_path(
        PathParser.binary_path(wpr_go_bin, "wpr.go binary"))

  def _download_prebuilt_wpr(self) -> LocalPath:
    wpr_info = WPR_PREBUILT_ARCH_MAP[self.browser_platform.machine]
    local_wpr_go_bin = WPR_CACHE / str(self.browser_platform.machine) / "wpr_go"
    if not check_hash(local_wpr_go_bin, wpr_info["file_hash"]):
      self.runner_platform.sh("gsutil", "cp", wpr_info["url"], local_wpr_go_bin)
    assert check_hash(local_wpr_go_bin, wpr_info["file_hash"])

    return local_wpr_go_bin

  @contextlib.contextmanager
  def open(self, session: BrowserSessionRunGroup) -> Iterator[ReplayNetwork]:
    with self._remote_temp_dir(session):
      with super().open(session):
        yield self

  @contextlib.contextmanager
  def _remote_temp_dir(self, session: BrowserSessionRunGroup) -> Iterator:
    with session.browser_platform.TemporaryDirectory() as tmp_dir:
      self._tmp_dir = tmp_dir
      yield
      self._tmp_dir = None

  def _push_file(self, path: LocalPath) -> AnyPath:
    assert self._tmp_dir is not None
    remote_path = self._tmp_dir / path.name
    self.browser_platform.push(path, remote_path)
    return remote_path

  def _push_required_files(self) -> List[AnyPath]:
    runner_platform = self.browser_platform.host_platform
    local_wpr_go = WprGoToolFinder(runner_platform).path
    wpr_root = self.runner_platform.path(local_wpr_go.parents[1])

    all_files = [self._archive_path,
                 wpr_root / "ecdsa_key.pem",
                 wpr_root / "ecdsa_cert.pem",
                 wpr_root / "deterministic.js"]
    remote_files = [self._push_file(f) for f in all_files]

    remote_wpr_go_bin = self._push_file(self._wpr_go_bin)
    self.browser_platform.sh("chmod", "+x", remote_wpr_go_bin)

    return [remote_wpr_go_bin] + remote_files

  def _create_server(self, log_dir: LocalPath) -> WprReplayServer:
    wpr_go_bin, archive, key_file, cert_file, inject_script =\
        self._push_required_files()
    return WprReplayServer(
        archive_path=archive,
        bin_path=wpr_go_bin,
        key_file=key_file,
        cert_file=cert_file,
        inject_scripts=[inject_script],
        log_path=log_dir / "network.wpr.log",
        platform=self.browser_platform)
