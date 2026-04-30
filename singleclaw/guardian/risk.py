"""Risk Classifier – infer a risk level from a plain-text action description.

Uses simple keyword matching for the MVP.  Each category maps action keywords
to a risk level: ``low``, ``medium``, ``high``, or ``critical``.
"""

from __future__ import annotations

# Ordered from highest to lowest risk so the first match wins.
_RULES: list[tuple[str, list[str]]] = [
    (
        "critical",
        [
            "drop database",
            "drop table",
            "truncate",
            "rm -rf",
            "format disk",
            "wipe",
            "destroy",
        ],
    ),
    (
        "high",
        [
            "delete file",
            "delete files",
            "overwrite file",
            "overwrite files",
            "git push",
            "git force push",
            "run shell",
            "exec ",
            "subprocess",
            "modify database",
            "batch update",
            "external upload",
            "upload to",
            "send email",
            "send message",
            "publish",
        ],
    ),
    (
        "medium",
        [
            "move file",
            "rename file",
            "update file",
            "write file",
            "create file",
            "git commit",
            "git merge",
            "api call",
            "http post",
            "http put",
            "http patch",
            "http delete",
        ],
    ),
]


class RiskClassifier:
    """Classify an action description using keyword rules.

    Returns ``"low"`` when no rule matches.
    """

    def classify(self, action: str) -> str:
        """Return the inferred risk level for *action*.

        Args:
            action: Human-readable action description.

        Returns:
            One of ``"low"``, ``"medium"``, ``"high"``, or ``"critical"``.
        """
        lower = action.lower()
        for level, keywords in _RULES:
            for kw in keywords:
                if kw in lower:
                    return level
        return "low"
