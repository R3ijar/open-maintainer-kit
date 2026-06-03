from __future__ import annotations

import json

from .engine import MaintainerPlan


def render_codex_prompt(plan: MaintainerPlan) -> str:
    lines = [
        "# Maintainer Task Prompt",
        "",
        "You are working on an open-source repository. Make one focused maintainer improvement from the plan below.",
        "",
        "Rules:",
        "",
        "- Keep the change scoped to the selected action.",
        "- Do not invent adoption, impact, or security claims.",
        "- Do not expose secrets, private user data, tokens, or raw payloads.",
        "- Run the smallest relevant validation before finishing.",
        "",
        "## Plan",
        "",
        f"- Action: {plan.action_type}",
        f"- Target: {plan.target or 'none'}",
        f"- Confidence: {plan.confidence}",
        f"- Reason: {plan.reason}",
        "",
        "## Next Steps",
        "",
    ]
    lines.extend(f"- {step}" for step in plan.next_steps)
    lines.extend(["", "## Evidence", "", "```json", json.dumps(plan.evidence, indent=2, sort_keys=True), "```", ""])
    return "\n".join(lines)
