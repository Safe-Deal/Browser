# Copyright 2022 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# pytype: disable=attribute-error

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import unittest
from typing import List, Sequence, cast
from unittest import mock

from crossbench.benchmarks.loading.action_runner.base import ActionRunner
from crossbench.benchmarks.loading.action_runner.basic_action_runner import \
    BasicActionRunner
from crossbench.benchmarks.loading.action_type import ActionType
from crossbench.benchmarks.loading.config.blocks import ActionBlockListConfig
from crossbench.benchmarks.loading.config.login.google import (GOOGLE_LOGIN_URL,
                                                               GoogleLogin)
from crossbench.benchmarks.loading.loading_benchmark import (LoadingPageFilter,
                                                             PageLoadBenchmark)
from crossbench.benchmarks.loading.page import (PAGE_LIST, PAGE_LIST_SMALL,
                                                CombinedPage, LivePage)
from crossbench.benchmarks.loading.playback_controller import \
    PlaybackController
from crossbench.benchmarks.loading.tab_controller import TabController
from crossbench.browsers.settings import Settings
from crossbench.cli.config.secrets import SecretsConfig
from crossbench.env import HostEnvironmentConfig, ValidationMode
from crossbench.runner.runner import Runner
from tests import test_helper
from tests.crossbench.base import BaseCliTestCase
from tests.crossbench.benchmarks import helper
from tests.crossbench.mock_browser import JsInvocation


class TestPageLoadBenchmark(helper.SubStoryTestCase):

  @property
  def benchmark_cls(self):
    return PageLoadBenchmark

  def story_filter(  # pylint: disable=arguments-differ
      self,
      patterns: Sequence[str],
      separate: bool = True,
      playback: PlaybackController = PlaybackController.default(),
      tabs: TabController = TabController.default(),
      action_runner: ActionRunner = BasicActionRunner(),
      about_blank_duration: dt.timedelta = dt.timedelta(),
      run_login: bool = True,
      run_setup: bool = True) -> LoadingPageFilter:
    args = argparse.Namespace(
        about_blank_duration=about_blank_duration,
        playback=playback,
        tabs=tabs,
        action_runner=action_runner,
        run_login=run_login,
        run_setup=run_setup)
    return cast(LoadingPageFilter,
                super().story_filter(patterns, args=args, separate=separate))

  def test_all_stories(self):
    stories = self.story_filter(["all"]).stories
    self.assertGreater(len(stories), 1)
    for story in stories:
      self.assertIsInstance(story, LivePage)
    names = set(story.name for story in stories)
    self.assertEqual(len(names), len(stories))
    self.assertEqual(names, set(page.name for page in PAGE_LIST))

  def test_default_stories(self):
    stories = self.story_filter(["default"]).stories
    self.assertGreater(len(stories), 1)
    for story in stories:
      self.assertIsInstance(story, LivePage)
    names = set(story.name for story in stories)
    self.assertEqual(len(names), len(stories))
    self.assertEqual(names, set(page.name for page in PAGE_LIST_SMALL))

  def test_combined_stories(self):
    stories = self.story_filter(["all"], separate=False).stories
    self.assertEqual(len(stories), 1)
    combined = stories[0]
    self.assertIsInstance(combined, CombinedPage)

  def test_filter_by_name(self):
    for preset_page in PAGE_LIST:
      stories = self.story_filter([preset_page.name]).stories
      self.assertListEqual([p.url for p in stories], [preset_page.url])
    with self.assertRaises(argparse.ArgumentTypeError) as cm:
      self.story_filter([])
    self.assertIn("empty", str(cm.exception).lower())

  def test_filter_by_name_with_duration(self):
    pages = PAGE_LIST
    filtered_pages = self.story_filter([pages[0].name, pages[1].name,
                                        "1001"]).stories
    self.assertListEqual([p.url for p in filtered_pages],
                         [pages[0].url, pages[1].url])
    self.assertEqual(filtered_pages[0].duration, pages[0].duration)
    self.assertEqual(filtered_pages[1].duration, dt.timedelta(seconds=1001))

  def test_page_by_url(self):
    url1 = "http://example.com/test1"
    url2 = "http://example.com/test2"
    stories = self.story_filter([url1, url2]).stories
    self.assertEqual(len(stories), 2)
    self.assertEqual(stories[0].first_url, url1)
    self.assertEqual(stories[1].first_url, url2)

  def test_page_by_url_www(self):
    url1 = "www.example.com/test1"
    url2 = "www.example.com/test2"
    stories = self.story_filter([url1, url2]).stories
    self.assertEqual(len(stories), 2)
    self.assertEqual(stories[0].first_url, f"https://{url1}")
    self.assertEqual(stories[1].first_url, f"https://{url2}")

  def test_page_by_url_combined(self):
    url1 = "http://example.com/test1"
    url2 = "http://example.com/test2"
    stories = self.story_filter([url1, url2], separate=False).stories
    self.assertEqual(len(stories), 1)
    combined = stories[0]
    self.assertIsInstance(combined, CombinedPage)

  def test_run_combined(self):
    stories = [CombinedPage(PAGE_LIST)]
    self._test_run(stories)
    self._assert_urls_loaded([story.url for story in PAGE_LIST])

  def test_run_default(self):
    stories = PAGE_LIST
    self._test_run(stories)
    self._assert_urls_loaded([story.url for story in stories])

  def test_run_throw(self):
    stories = PAGE_LIST
    self._test_run(stories)
    self._assert_urls_loaded([story.url for story in stories])

  def test_run_repeat_with_about_blank(self):
    url1 = "https://www.example.com/test1"
    url2 = "https://www.example.com/test2"
    stories = self.story_filter(
        [url1, url2],
        separate=False,
        about_blank_duration=dt.timedelta(seconds=1)).stories
    self._test_run(stories)
    urls = [url1, "about:blank", url2, "about:blank"]
    self._assert_urls_loaded(urls)

  def test_run_repeat_with_about_blank_separate(self):
    url1 = "https://www.example.com/test1"
    url2 = "https://www.example.com/test2"
    stories = self.story_filter(
        [url1, url2],
        separate=True,
        about_blank_duration=dt.timedelta(seconds=1)).stories
    self._test_run(stories)
    urls = [url1, "about:blank", url2, "about:blank"]
    self._assert_urls_loaded(urls)

  def test_run_repeat(self):
    url1 = "https://www.example.com/test1"
    url2 = "https://www.example.com/test2"
    stories = self.story_filter([url1, url2],
                                separate=False,
                                playback=PlaybackController.repeat(3)).stories
    self._test_run(stories)
    urls = [url1, url2] * 3
    self._assert_urls_loaded(urls)

  def test_run_repeat_separate(self):
    url1 = "https://www.example.com/test1"
    url2 = "https://www.example.com/test2"
    stories = self.story_filter([url1, url2],
                                separate=True,
                                playback=PlaybackController.repeat(3)).stories
    self._test_run(stories)
    urls = [url1] * 3 + [url2] * 3
    self._assert_urls_loaded(urls)

  def _test_run(self, stories, throw: bool = False):
    benchmark = self.benchmark_cls(stories)
    self.assertTrue(len(benchmark.describe()) > 0)
    runner = Runner(
        self.out_dir,
        self.browsers,
        benchmark,
        env_config=HostEnvironmentConfig(),
        env_validation_mode=ValidationMode.SKIP,
        platform=self.platform,
        throw=throw)
    runner.run()
    self.assertTrue(runner.is_success)
    self.assertTrue(self.browsers[0].did_run)
    self.assertTrue(self.browsers[1].did_run)

  def _assert_urls_loaded(self, story_urls):
    browser_1_urls = self.filter_splashscreen_urls(self.browsers[0].url_list)
    self.assertEqual(browser_1_urls, story_urls)
    browser_2_urls = self.filter_splashscreen_urls(self.browsers[1].url_list)
    self.assertEqual(browser_2_urls, story_urls)


class LoadingBenchmarkCliTestCase(BaseCliTestCase):

  def test_invalid_duplicate_urls_stories(self):
    with self.assertRaises(argparse.ArgumentTypeError) as cm:
      with self.patch_get_browser():
        url = "http://test.com"
        self.run_cli("loading", "run", f"--urls={url}", f"--stories={url}",
                     "--env-validation=skip", "--throw")
    self.assertIn("--urls", str(cm.exception))
    self.assertIn("--stories", str(cm.exception))

  def test_invalid_duplicate_urls_config(self):
    with self.assertRaises(argparse.ArgumentError) as cm:
      with self.patch_get_browser():
        self.run_cli("loading", "run", "--urls=https://test.com",
                     "--page-config=config.hjson", "--env-validation=skip",
                     "--throw")
    self.assertIn("--urls", str(cm.exception))
    self.assertIn("--page-config", str(cm.exception))

  def test_invalid_duplicate_stories_config(self):
    with self.assertRaises(argparse.ArgumentTypeError) as cm:
      with self.patch_get_browser():
        self.run_cli("loading", "run", "--stories=https://test.com",
                     "--page-config=config.hjson", "--env-validation=skip",
                     "--throw")
    self.assertIn("--stories", str(cm.exception))
    self.assertIn("page config", str(cm.exception).lower())

  def test_conflicting_global_config(self):
    config_data = {
        "browsers": {
            "chrome": "chrome-stable"
        },
        "pages": {
            "google_search_result": [{
                "action": "get",
                "url": "https://www.google.com/search?q=cats"
            },]
        }
    }
    config_file = pathlib.Path("config.hjson")
    with config_file.open("w") as f:
      json.dump(config_data, f)
    with self.assertRaises(argparse.ArgumentTypeError) as cm:
      with self.patch_get_browser():
        self.run_cli("loading", "run", "--stories=https://test.com",
                     "--config=config.hjson", "--page-config=config.hjson",
                     "--env-validation=skip", "--throw")
    error_message = str(cm.exception).lower()
    self.assertIn("conflict", error_message)
    self.assertIn("--config", error_message)
    self.assertIn("--page-config", error_message)

  def test_page_list_file(self):
    config = pathlib.Path("test/pages.txt")
    self.fs.create_file(config)
    url_1 = "http://one.test.com"
    url_2 = "http://two.test.com"
    with config.open("w") as f:
      f.write("\n".join((url_1, url_2)))
    with self.patch_get_browser():
      self.run_cli("loading", "run", f"--urls-file={config}",
                   "--env-validation=skip", "--throw")
      for browser in self.browsers:
        self.assertListEqual([url_1, url_2],
                             browser.url_list[self.SPLASH_URLS_LEN:])

  def test_page_list_file_separate(self):
    config = pathlib.Path("test/pages.txt")
    self.fs.create_file(config)
    url_1 = "http://one.test.com"
    url_2 = "http://two.test.com"
    with config.open("w") as f:
      f.write("\n".join((url_1, url_2)))
    with self.patch_get_browser():
      self.run_cli("loading", "run", f"--urls-file={config}",
                   "--env-validation=skip", "--separate", "--throw")
      for browser in self.browsers:
        self.assertEqual(len(browser.url_list), (self.SPLASH_URLS_LEN + 1) * 2)
        self.assertEqual(url_1, browser.url_list[self.SPLASH_URLS_LEN])
        self.assertEqual(url_2, browser.url_list[self.SPLASH_URLS_LEN * 2 + 1])

  def test_urls_single(self):
    with self.patch_get_browser():
      url = "http://test.com"
      self.run_cli("loading", "run", f"--urls={url}", "--env-validation=skip",
                   "--throw")
      for browser in self.browsers:
        self.assertListEqual([url], browser.url_list[self.SPLASH_URLS_LEN:])

  def test_urls_multiple(self):
    with self.patch_get_browser():
      url_1 = "http://one.test.com"
      url_2 = "http://two.test.com"
      self.run_cli("loading", "run", f"--urls={url_1},{url_2}",
                   "--env-validation=skip", "--throw")
      for browser in self.browsers:
        self.assertListEqual([url_1, url_2],
                             browser.url_list[self.SPLASH_URLS_LEN:])

  def test_urls_multiple_separate(self):
    with self.patch_get_browser():
      url_1 = "http://one.test.com"
      url_2 = "http://two.test.com"
      self.run_cli("loading", "run", f"--urls={url_1},{url_2}",
                   "--env-validation=skip", "--separate", "--throw")
      for browser in self.browsers:
        self.assertEqual(len(browser.url_list), (self.SPLASH_URLS_LEN + 1) * 2)
        self.assertEqual(url_1, browser.url_list[self.SPLASH_URLS_LEN])
        self.assertEqual(url_2, browser.url_list[self.SPLASH_URLS_LEN * 2 + 1])

  def test_repeat_playback(self):
    with self.patch_get_browser():
      url_1 = "http://one.test.com"
      url_2 = "http://two.test.com"
      self.run_cli("loading", "run", f"--urls={url_1},{url_2}", "--playback=2x",
                   "--env-validation=skip", "--throw")
      for browser in self.browsers:
        self.assertListEqual([url_1, url_2, url_1, url_2],
                             browser.url_list[self.SPLASH_URLS_LEN:])

  def test_repeat_playback_separate(self):
    with self.patch_get_browser():
      url_1 = "http://one.test.com"
      url_2 = "http://two.test.com"
      self.run_cli("loading", "run", f"--urls={url_1},{url_2}", "--playback=2x",
                   "--separate", "--env-validation=skip", "--throw")
      for browser in self.browsers:
        self.assertEqual(len(browser.url_list), (self.SPLASH_URLS_LEN + 2) * 2)
        self.assertListEqual(
            [url_1, url_1],
            browser.url_list[self.SPLASH_URLS_LEN:self.SPLASH_URLS_LEN + 2])
        self.assertListEqual([url_2, url_2],
                             browser.url_list[self.SPLASH_URLS_LEN * 2 + 2:])

  def simple_pages_config(self):
    url_1 = "http://one.test.com"
    url_2 = "http://two.test.com"
    config = {
        "pages": {
            "test_one": [{
                "action": "get",
                "url": url_1
            }, {
                "action": "get",
                "url": url_2
            }]
        }
    }
    return url_1, url_2, config

  def test_actions_config(self):
    url_1, url_2, config = self.simple_pages_config()
    config_file = pathlib.Path("test/page_config.json")
    self.fs.create_file(config_file, contents=json.dumps(config))
    with self.patch_get_browser():
      self.run_cli("loading", "run", f"--page-config={config_file}",
                   "--env-validation=skip", "--throw")
      for browser in self.browsers:
        self.assertListEqual([url_1, url_2],
                             browser.url_list[self.SPLASH_URLS_LEN:])

  def setup_expected_google_login_js(self):
    expected_scripts: List[JsInvocation] = [
        JsInvocation(True, re.compile(r".*Email or phone.*")),
        JsInvocation(None, re.compile(r".*user@test.com.*")),
        JsInvocation(True, re.compile(r".*passwordNext.*")),
        JsInvocation(False, re.compile(r".*verifycontactNext.*")),
        JsInvocation(True, re.compile(r".*Enter your password.*")),
        JsInvocation(True, re.compile(r".*s3cr3t.*")),
        JsInvocation(True, re.compile(r".*https://myaccount.google.com.*")),
    ]
    for browser in self.browsers:
      for script in expected_scripts:
        browser.expect_js(script)

  def simple_pages_with_login_config(self):
    url_1 = "http://one.test.com"
    url_2 = "http://two.test.com"
    config = {
        "pages": {
            "test_one": {
                "login":
                    "google",
                "actions": [{
                    "action": "get",
                    "url": url_1
                }, {
                    "action": "get",
                    "url": url_2
                }]
            }
        }
    }
    return url_1, url_2, config

  def test_actions_config_with_login_preset(self):
    url_1, url_2, config = self.simple_pages_with_login_config()
    config.update({
        "secrets": {
            "google": {
                "username": "user@test.com",
                "password": "s3cr3t"
            }
        },
    })
    config_file = pathlib.Path("test/page_config.json")
    self.fs.create_file(config_file, contents=json.dumps(config))
    self.setup_expected_google_login_js()
    with self.patch_get_browser():
      self.run_cli("loading", "run", f"--page-config={config_file}",
                   "--env-validation=skip", "--throw")
      for browser in self.browsers:
        self.assertListEqual([GOOGLE_LOGIN_URL, url_1, url_2],
                             browser.url_list[self.SPLASH_URLS_LEN:])

  def test_actions_config_with_login_preset_global_secrets(self):
    url_1, url_2, config = self.simple_pages_with_login_config()
    config_file = pathlib.Path("test/page_config.json")
    self.fs.create_file(config_file, contents=json.dumps(config))
    secrets_data = {
        "google": {
            "username": "user@test.com",
            "password": "s3cr3t"
        }
    }
    secrets_dict = SecretsConfig.parse(secrets_data).as_dict()
    self.setup_expected_google_login_js()
    with self.patch_get_browser():
      with mock.patch.object(
          Settings, "secrets",
          new_callable=mock.PropertyMock) as mock_get_secrets:
        mock_get_secrets.return_value = secrets_dict
        self.run_cli("loading", "run", f"--page-config={config_file}",
                     "--env-validation=skip", "--throw",
                     f"--secrets={json.dumps(secrets_data)}")
      for browser in self.browsers:
        self.assertListEqual([GOOGLE_LOGIN_URL, url_1, url_2],
                             browser.url_list[self.SPLASH_URLS_LEN:])

  def test_actions_config_with_login_preset_missing_secrets(self):
    _, _, config = self.simple_pages_with_login_config()
    config_file = pathlib.Path("test/page_config.json")
    self.fs.create_file(config_file, contents=json.dumps(config))
    self.setup_expected_google_login_js()
    with self.patch_get_browser():
      with self.assertRaises(Exception) as cm:
        self.run_cli("loading", "run", f"--page-config={config_file}",
                     "--env-validation=skip", "--throw")
      self.assertIn("google", str(cm.exception))

  def test_global_config_actions_config(self):
    url_1 = "http://one.test.com"
    url_2 = "http://two.test.com"
    global_config_file = pathlib.Path("config.hjson")
    global_config_data = {
        # Dummy entry, not actually used by the test
        "browsers": {
            "chrome": "chrome-stable"
        },
        "pages": {
            "test_one": [{
                "action": "get",
                "url": url_1
            }, {
                "action": "get",
                "url": url_2
            }]
        }
    }
    with global_config_file.open("w") as f:
      json.dump(global_config_data, f)
    with self.patch_get_browser():
      self.run_cli("loading", "run", f"--config={global_config_file}",
                   "--env-validation=skip", "--throw")
      for browser in self.browsers:
        self.assertListEqual([url_1, url_2],
                             browser.url_list[self.SPLASH_URLS_LEN:])


class ActionBlockListConfigTestCase(unittest.TestCase):

  def test_parse_invalid(self):
    for invalid in ("", (), {}, 1):
      with self.subTest(invalid=invalid):
        with self.assertRaises(argparse.ArgumentTypeError):
          ActionBlockListConfig.parse(invalid)

  def test_parse_default_action_list(self):
    config = ActionBlockListConfig.parse([{
        "action": "get",
        "url": "http://test.com",
        "duration": "12.5s",
    }])
    self.assertEqual(len(config.blocks), 1)
    block = config.blocks[0]
    self.assertEqual(block.label, "default")
    self.assertEqual(len(block.actions), 1)
    self.assertEqual(block.actions[0].TYPE, ActionType.GET)
    self.assertEqual(block.duration, dt.timedelta(seconds=12.5))

  def test_parse_default_action_list_2(self):
    config = ActionBlockListConfig.parse([{
        "action": "get",
        "url": "http://test.com",
        "duration": "12.5s",
    }, {
        "action": "wait",
        "duration": "100s",
    }])
    self.assertEqual(len(config.blocks), 1)
    block = config.blocks[0]
    self.assertEqual(block.label, "default")
    self.assertEqual(len(block.actions), 2)
    self.assertEqual(block.actions[0].TYPE, ActionType.GET)
    self.assertEqual(block.actions[1].TYPE, ActionType.WAIT)
    self.assertEqual(block.duration, dt.timedelta(seconds=112.5))

  def test_parse_single_block_action_list(self):
    config = ActionBlockListConfig.parse([{
        "label": "block 1",
        "actions": [{
            "action": "get",
            "url": "http://test.com"
        }]
    }])
    self.assertEqual(len(config.blocks), 1)
    block = config.blocks[0]
    self.assertEqual(block.label, "block 1")
    self.assertEqual(len(block.actions), 1)
    self.assertEqual(block.actions[0].TYPE, ActionType.GET)

  def test_parse_multi_block_action_list(self):
    config = ActionBlockListConfig.parse([{
        "label":
            "block 0",
        "actions": [{
            "action": "get",
            "url": "http://test.com/0",
            "duration": "10s",
        }]
    }, {
        "label":
            "block 1",
        "actions": [{
            "action": "get",
            "url": "http://test.com/1",
            "duration": "11s",
        }]
    }])
    self.assertEqual(len(config.blocks), 2)
    for index, block in enumerate(config.blocks):
      self.assertEqual(block.label, f"block {index}")
      self.assertEqual(len(block.actions), 1)
      self.assertEqual(block.actions[0].TYPE, ActionType.GET)
      self.assertEqual(block.actions[0].url, f"http://test.com/{index}")
      self.assertEqual(block.duration, dt.timedelta(seconds=10 + index))

  def test_parse_single_block_dict(self):
    config = ActionBlockListConfig.parse(
        {"block 1": {
            "actions": [{
                "action": "get",
                "url": "http://test.com"
            }]
        }})
    self.assertEqual(len(config.blocks), 1)
    block = config.blocks[0]
    self.assertEqual(block.label, "block 1")
    self.assertEqual(len(block.actions), 1)
    self.assertEqual(block.actions[0].TYPE, ActionType.GET)

  def test_parse_block_dict_action_list_2(self):
    config = ActionBlockListConfig.parse({
        "block 1": [{
            "action": "get",
            "url": "http://test.com"
        }, {
            "action": "wait",
            "duration": "2s"
        }]
    })
    self.assertEqual(len(config.blocks), 1)
    block = config.blocks[0]
    self.assertEqual(block.label, "block 1")
    self.assertEqual(len(block.actions), 2)
    self.assertEqual(block.actions[0].TYPE, ActionType.GET)
    self.assertEqual(block.actions[1].TYPE, ActionType.WAIT)

  def test_parse_single_block_multi_action_dict(self):
    config = ActionBlockListConfig.parse({
        "block 1": {
            "actions": [{
                "action": "get",
                "url": "http://test.com/0",
                "duration": "1s",
            }, {
                "action": "get",
                "url": "http://test.com/1",
                "duration": "20s",
            }]
        }
    })
    self.assertEqual(len(config.blocks), 1)
    block = config.blocks[0]
    self.assertEqual(block.label, "block 1")
    self.assertEqual(block.duration, dt.timedelta(seconds=21))
    self.assertEqual(len(block.actions), 2)
    for index, action in enumerate(block.actions):
      self.assertEqual(action.TYPE, ActionType.GET)
      self.assertEqual(action.url, f"http://test.com/{index}")

  def test_parse_multi_block_actions_dict(self):
    config = ActionBlockListConfig.parse({
        "block 0": {
            "actions": [{
                "action": "get",
                "url": "http://test.com/0"
            }]
        },
        "block 1": {
            "actions": [{
                "action": "get",
                "url": "http://test.com/1"
            }]
        }
    })
    self.assertEqual(len(config.blocks), 2)
    for index, block in enumerate(config.blocks):
      self.assertEqual(block.label, f"block {index}")
      self.assertEqual(len(block.actions), 1)
      self.assertEqual(block.actions[0].TYPE, ActionType.GET)
      self.assertEqual(block.actions[0].url, f"http://test.com/{index}")

  def test_parse_multi_block_actions_list(self):
    config = ActionBlockListConfig.parse({
        "block 0": [{
            "action": "get",
            "url": "http://test.com/0"
        }],
        "block 1": [{
            "action": "get",
            "url": "http://test.com/1"
        }]
    })
    self.assertEqual(len(config.blocks), 2)
    for index, block in enumerate(config.blocks):
      self.assertEqual(block.label, f"block {index}")
      self.assertEqual(len(block.actions), 1)
      self.assertEqual(block.actions[0].TYPE, ActionType.GET)
      self.assertEqual(block.actions[0].url, f"http://test.com/{index}")

  def test_parse_dict_label_conflict(self):
    with self.assertRaises(argparse.ArgumentTypeError) as cm:
      ActionBlockListConfig.parse({
          "block 1": {
              "label": "block 2",
              "actions": [{
                  "action": "get",
                  "url": "http://test.com"
              }]
          }
      })
    self.assertIn("block 2", str(cm.exception))

  def test_parse_invalid_dict_missing_actions(self):
    with self.assertRaises(argparse.ArgumentTypeError) as cm:
      ActionBlockListConfig.parse({"block 1": {}})
    self.assertIn("actions", str(cm.exception))

  def test_parse_invalid_dict_empty_actions(self):
    with self.assertRaises(argparse.ArgumentTypeError) as cm:
      ActionBlockListConfig.parse({"block 1": {"actions": []}})
    self.assertIn("actions", str(cm.exception))

  def test_parse_logins(self):
    with self.assertRaises(argparse.ArgumentTypeError) as cm:
      _ = ActionBlockListConfig.parse({
          "login": [{
              "action": "get",
              "url": "http://test.com/login"
          }],
          "block 0": [{
              "action": "get",
              "url": "http://test.com/1"
          }]
      })
    self.assertIn("login", str(cm.exception))


if __name__ == "__main__":
  test_helper.run_pytest(__file__)
