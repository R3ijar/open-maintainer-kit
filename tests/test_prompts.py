from __future__ import annotations

import unittest

from open_maintainer_kit.engine import MaintainerPlan
from open_maintainer_kit.prompts import render_codex_prompt


class PromptTests(unittest.TestCase):
    def test_prompt_contains_plan_and_privacy_boundary(self) -> None:
        plan = MaintainerPlan(
            action_type="fix_ci_failure",
            target="tests",
            title="Fix tests",
            reason="CI is failing",
            confidence="high",
            next_steps=["Reproduce locally"],
            evidence={"decision": {"selected_rule": "ci_runs"}},
        )

        prompt = render_codex_prompt(plan)

        self.assertIn("fix_ci_failure", prompt)
        self.assertIn("Do not expose secrets", prompt)


if __name__ == "__main__":
    unittest.main()
