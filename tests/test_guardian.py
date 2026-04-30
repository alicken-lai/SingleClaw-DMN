"""Tests for the Guardian policy and risk classifier."""

import pytest

from singleclaw.guardian.policy import GuardianPolicy, ALLOW, REVIEW_REQUIRED, BLOCK
from singleclaw.guardian.risk import RiskClassifier


class TestRiskClassifier:
    def setup_method(self):
        self.clf = RiskClassifier()

    def test_low_risk_default(self):
        assert self.clf.classify("summarise document") == "low"

    def test_high_risk_delete(self):
        assert self.clf.classify("delete files in /tmp") == "high"

    def test_high_risk_git_push(self):
        assert self.clf.classify("git push origin main") == "high"

    def test_critical_rm_rf(self):
        assert self.clf.classify("rm -rf /home/user") == "critical"

    def test_medium_write_file(self):
        assert self.clf.classify("write file report.md") == "medium"

    def test_case_insensitive(self):
        assert self.clf.classify("DELETE FILES") == "high"


class TestGuardianPolicy:
    def setup_method(self):
        self.guardian = GuardianPolicy()

    def test_allow_low_risk(self):
        assert self.guardian.check("read document", risk_level="low") == ALLOW

    def test_review_medium_risk(self):
        assert self.guardian.check("write file report.md", risk_level="medium") == REVIEW_REQUIRED

    def test_block_high_risk(self):
        assert self.guardian.check("some action", risk_level="high") == BLOCK

    def test_block_critical_risk(self):
        assert self.guardian.check("some action", risk_level="critical") == BLOCK

    def test_inferred_high_overrides_low_hint(self):
        # Even though caller says low, the keyword inference detects high risk.
        assert self.guardian.check("git push to production", risk_level="low") == BLOCK

    def test_inferred_medium_overrides_low_hint(self):
        assert self.guardian.check("write file notes.md", risk_level="low") == REVIEW_REQUIRED
