# Copyright 2024 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

from typing import TYPE_CHECKING

from crossbench.benchmarks.loading.config.login.base import PresetLoginBlock
from crossbench.cli.config.secret_type import SecretType

if TYPE_CHECKING:
  from crossbench.benchmarks.loading.action_runner.base import ActionRunner
  from crossbench.benchmarks.loading.page import InteractivePage
  from crossbench.cli.config.secrets import Secret
  from crossbench.runner.actions import Actions
  from crossbench.runner.run import Run

GOOGLE_LOGIN_URL: str = (
    "https://accounts.google.com/Logout?"
    "continue=https%3A%2F%2Faccounts.google.com%2Fv3%2Fsignin%2Fidentifier%3F"
    "flowName%3DGlifWebSignIn%26flowEntry%3DServiceLogin")

TRUSTED_EMAIL_CHECK: str = (
    "return document.getElementById('verifycontactNext') != null")


class GoogleLogin(PresetLoginBlock):
  """Google-specific login steps."""

  def _submit_login_field(self, action: Actions, aria_label: str,
                          input_val: str, button_name: str) -> None:
    action.wait_js_condition(
        ("return "
         f"document.querySelector(\"[aria-label='{aria_label}']\") != null &&"
         f"document.getElementById({repr(button_name)}) != null;"), 0.2, 10)
    action.js(
        f"const inputField = document.querySelector(\"[aria-label='{aria_label}']\");"
        f"inputField.value = {repr(input_val)};"
        f"document.getElementById({repr(button_name)}).click();")

  def run_with(self, runner: ActionRunner, run: Run,
               page: InteractivePage) -> None:
    secret: Secret = self.get_secret(run, page, SecretType.GOOGLE)

    with run.actions("Login") as action:
      action.show_url(GOOGLE_LOGIN_URL)
      self._submit_login_field(action, "Email or phone", secret.username,
                               "identifierNext")
      action.wait_js_condition(
          "return document.getElementById('verifycontactNext') || "
          "document.getElementById('passwordNext') != null;", 0.2, 10)
      if action.js(TRUSTED_EMAIL_CHECK):
        self._test_account_login(action, secret)
      else:
        self._standard_login(action, secret)

  def _standard_login(self, action, secret):
    self._submit_login_field(action, "Enter your password", secret.password,
                             "passwordNext")
    action.wait_js_condition(
        "return document.URL.startsWith('https://myaccount.google.com');", 0.2,
        10)

  def _test_account_login(self, action, secret):
    self._submit_login_field(action, "Enter trusted contact\\’s email",
                             secret.password, "verifycontactNext")
    # TODO: handle account passkey setup, for now each test account needs a
    # one time manual interaction.
    action.wait_js_condition(
        "return document.URL.startsWith('https://myaccount.google.com')", 0.2,
        60)
