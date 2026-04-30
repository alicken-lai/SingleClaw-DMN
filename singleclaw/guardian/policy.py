"""Guardian Policy – rule-based safety classification.

Classifies every action as one of:

* ``ALLOW``          – safe to execute immediately.
* ``REVIEW_REQUIRED``– medium risk; show a dry-run preview first.
* ``BLOCK``          – high risk; refuse execution.

The policy is intentionally simple and rule-based for the MVP.  A future
version may support user-configurable policy files.
"""

from __future__ import annotations

from singleclaw.guardian.risk import RiskClassifier

# Human-readable decision constants
ALLOW = "ALLOW"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
BLOCK = "BLOCK"


class GuardianPolicy:
    """Evaluate an action description and return a Guardian decision.

    Usage::

        guardian = GuardianPolicy()
        decision = guardian.check("delete temporary files", risk_level="high")
        # → "BLOCK"
    """

    def __init__(self) -> None:
        self._classifier = RiskClassifier()

    def check(self, action: str, risk_level: str = "low") -> str:
        """Return the Guardian decision for an action.

        The final risk level is the *maximum* of the explicit ``risk_level``
        argument and the level inferred from the action text by
        :class:`~singleclaw.guardian.risk.RiskClassifier`.

        Args:
            action:     Human-readable description of the action.
            risk_level: Caller-supplied risk hint (``low``, ``medium``,
                        ``high``, or ``critical``).

        Returns:
            One of ``"ALLOW"``, ``"REVIEW_REQUIRED"``, or ``"BLOCK"``.
        """
        inferred = self._classifier.classify(action)
        effective = _max_risk(risk_level, inferred)

        if effective in ("critical", "high"):
            return BLOCK
        if effective == "medium":
            return REVIEW_REQUIRED
        return ALLOW


# ── helpers ──────────────────────────────────────────────────────────────────

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _max_risk(a: str, b: str) -> str:
    """Return the higher of two risk level strings."""
    rank_a = _RISK_ORDER.get(a.lower(), 0)
    rank_b = _RISK_ORDER.get(b.lower(), 0)
    return a if rank_a >= rank_b else b
