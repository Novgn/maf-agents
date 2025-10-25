"""
Unit tests for Production Promotion Executor.

Tests promotion change generation and PR creation logic.
"""

import pytest
import json
from workflows.detector_workflow import _generate_promotion_changes


class TestGeneratePromotionChanges:
    """Tests for _generate_promotion_changes function."""

    def test_generate_promotion_changes_with_feature_flag_pattern(self):
        """Test generation of promotion changes with feature flag pattern."""
        workflow_data = {
            "rule_id": "test_rule",
            "provider_guid": "12345678-1234-1234-1234-123456789012",
            "results_summary": "Detector found 42 events",
            "events_detected": 42,
            "error_rate": 0.0,
        }

        patterns = {
            "production_indicators": [
                {
                    "type": "feature_flags",
                    "description": "Feature flag configuration files",
                    "count": 3,
                    "examples": [
                        "config/features.json",
                        "flags/detector_flags.yaml",
                        "config/app_flags.json"
                    ]
                }
            ],
            "pr_count": 5,
        }

        changes = _generate_promotion_changes(workflow_data, patterns)

        # Verify feature flag file uses pattern
        assert "config/features.json" in changes
        feature_flags = json.loads(changes["config/features.json"])
        assert "features" in feature_flags
        assert "detector_test_rule" in feature_flags["features"]
        assert feature_flags["features"]["detector_test_rule"]["enabled"] is True
        assert feature_flags["features"]["detector_test_rule"]["customer_facing"] is True

    def test_generate_promotion_changes_default_location(self):
        """Test generation with default feature flag location."""
        workflow_data = {
            "rule_id": "test_rule",
            "provider_guid": "12345678-1234-1234-1234-123456789012",
            "results_summary": "Detector validated",
            "events_detected": 100,
            "error_rate": 1.5,
        }

        # No feature flag patterns
        patterns = {
            "production_indicators": [],
            "pr_count": 0,
        }

        changes = _generate_promotion_changes(workflow_data, patterns)

        # Should use default location
        assert "config/feature_flags.json" in changes
        feature_flags = json.loads(changes["config/feature_flags.json"])
        assert "features" in feature_flags
        assert "detector_test_rule" in feature_flags["features"]

    def test_generate_promotion_changes_includes_readme(self):
        """Test that changes include documentation."""
        workflow_data = {
            "rule_id": "detector_1",
            "provider_guid": "ABC-123",
            "results_summary": "Test summary",
            "events_detected": 50,
            "error_rate": 0.5,
        }

        patterns = {
            "production_indicators": [],
            "pr_count": 0,
        }

        changes = _generate_promotion_changes(workflow_data, patterns)

        # Verify README is generated
        assert "docs/DETECTOR_PROMOTION.md" in changes
        readme_content = changes["docs/DETECTOR_PROMOTION.md"]

        # Check content includes key information
        assert "detector_1" in readme_content
        assert "Rule ID" in readme_content
        assert "ABC-123" in readme_content
        assert "Test summary" in readme_content
        assert "50" in readme_content
        assert "0.5" in readme_content

    def test_generate_promotion_changes_feature_flag_structure(self):
        """Test structure of generated feature flags."""
        workflow_data = {
            "rule_id": "my_detector",
            "provider_guid": "test-guid",
            "results_summary": "Passed validation",
            "events_detected": 75,
            "error_rate": 0.0,
        }

        patterns = {
            "production_indicators": [],
            "pr_count": 0,
        }

        changes = _generate_promotion_changes(workflow_data, patterns)

        # Parse feature flags
        feature_flags = json.loads(changes["config/feature_flags.json"])
        detector_config = feature_flags["features"]["detector_my_detector"]

        # Verify all required fields
        assert detector_config["enabled"] is True
        assert detector_config["customer_facing"] is True
        assert detector_config["rollout_percentage"] == 100
        assert "description" in detector_config
        assert "my_detector" in detector_config["description"]

    def test_generate_promotion_changes_readme_sections(self):
        """Test README includes all required sections."""
        workflow_data = {
            "rule_id": "test_detector",
            "provider_guid": "guid-123",
            "results_summary": "All tests passed",
            "events_detected": 200,
            "error_rate": 0.1,
        }

        patterns = {
            "production_indicators": [],
            "pr_count": 0,
        }

        changes = _generate_promotion_changes(workflow_data, patterns)
        readme = changes["docs/DETECTOR_PROMOTION.md"]

        # Verify sections
        assert "# Detector Promotion:" in readme
        assert "## Overview" in readme
        assert "## Detector Information" in readme
        assert "## Results Summary" in readme
        assert "## Metrics" in readme
        assert "## Changes" in readme
        assert "## Testing" in readme

    def test_generate_promotion_changes_multiple_files(self):
        """Test that multiple files are generated."""
        workflow_data = {
            "rule_id": "test",
            "provider_guid": "test-guid",
            "results_summary": "Test",
            "events_detected": 10,
            "error_rate": 0.0,
        }

        patterns = {
            "production_indicators": [],
            "pr_count": 0,
        }

        changes = _generate_promotion_changes(workflow_data, patterns)

        # Should generate at least 2 files
        assert len(changes) >= 2
        assert any("json" in path for path in changes.keys())  # Feature flag
        assert any(".md" in path for path in changes.keys())  # README

    def test_generate_promotion_changes_with_missing_optional_fields(self):
        """Test generation with minimal workflow data."""
        workflow_data = {
            "rule_id": "minimal_detector",
        }

        patterns = {
            "production_indicators": [],
            "pr_count": 0,
        }

        changes = _generate_promotion_changes(workflow_data, patterns)

        # Should still generate files
        assert "config/feature_flags.json" in changes
        assert "docs/DETECTOR_PROMOTION.md" in changes

        # Check defaults are used
        readme = changes["docs/DETECTOR_PROMOTION.md"]
        assert "N/A" in readme  # For missing provider_guid
        assert "No results summary available" in readme or "0" in readme

    def test_generate_promotion_changes_feature_flag_json_valid(self):
        """Test that generated feature flag JSON is valid."""
        workflow_data = {
            "rule_id": "json_test",
            "provider_guid": "test",
            "results_summary": "test",
            "events_detected": 1,
            "error_rate": 0.0,
        }

        patterns = {
            "production_indicators": [],
            "pr_count": 0,
        }

        changes = _generate_promotion_changes(workflow_data, patterns)

        # Should be valid JSON
        try:
            feature_flags = json.loads(changes["config/feature_flags.json"])
            assert isinstance(feature_flags, dict)
            assert "features" in feature_flags
        except json.JSONDecodeError:
            pytest.fail("Generated feature flag JSON is invalid")
