# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0
from .common import BaseTest

from mock import Mock
from textwrap import dedent

from c7n import deprecated

class DeprecationTest(BaseTest):

    def test_action(self):
        deprecation = deprecated.action('set-snapshot-copy-tags', "use modify-db instead with `CopyTagsToSnapshot`", '2021-06-30')
        # Always matches.
        self.assertTrue(deprecation.check({}))
        self.assertEqual(
            str(deprecation),
            "action 'set-snapshot-copy-tags' has been deprecated (use modify-db instead with `CopyTagsToSnapshot`)"
            )

    def test_filter(self):
        deprecation = deprecated.filter('unused', "use the 'used' filter with 'state' attribute", '2021-06-30')
        # Always matches.
        self.assertTrue(deprecation.check({}))
        self.assertEqual(
            str(deprecation),
            "filter 'unused' has been deprecated (use the 'used' filter with 'state' attribute)"
            )

    def test_field(self):
        deprecation = deprecated.field('severity_normalized', 'severity_label', '2021-06-30')
        self.assertTrue(deprecation.check({'severity_normalized': '10'}))
        self.assertFalse(deprecation.check({'no-match': 'ignored'}))
        self.assertEqual(
            str(deprecation),
            "field 'severity_normalized' has been deprecated (replaced by 'severity_label')"
            )



class ReportTest(BaseTest):

    def test_empty(self):
        report = deprecated.Report("some-policy")
        self.assertFalse(report.has_deprecations)
        self.assertEqual(report.format(), "policy 'some-policy'")

    def test_policy_source_locator(self):
        locator = Mock()
        locator.find.return_value = "somefile.yml:1234"
        report = deprecated.Report("some-policy")
        self.assertEqual(report.format(locator), "policy 'some-policy' (somefile.yml:1234)")
        locator.find.assert_called_with("some-policy")

    def test_one_condition(self):
        report = deprecated.Report("some-policy")
        report.conditions = [
            deprecated.field('region', 'region in condition block', '2021-06-30')]
        self.assertTrue(report.has_deprecations)
        self.assertEqual(report.format(), dedent("""
            policy 'some-policy'
              condition: field 'region' has been deprecated (replaced by region in condition block)
            """)[1:-1])

    def test_two_conditions(self):
        report = deprecated.Report("some-policy")
        report.conditions = [
            deprecated.field('start', 'value filter in condition block', '2021-06-30'),
            deprecated.field('end', 'value filter in condition block', '2021-06-30'),
        ]
        self.assertTrue(report.has_deprecations)
        self.assertEqual(report.format(), dedent("""
            policy 'some-policy'
              condition:
                field 'start' has been deprecated (replaced by value filter in condition block)
                field 'end' has been deprecated (replaced by value filter in condition block)
            """)[1:-1])

    def test_one_mode(self):
        report = deprecated.Report("some-policy")
        report.mode = [deprecated.field('foo', 'bar', '2021-06-30')]
        self.assertTrue(report.has_deprecations)
        self.assertEqual(report.format(), dedent("""
            policy 'some-policy'
              mode: field 'foo' has been deprecated (replaced by 'bar')
            """)[1:-1])

    def test_two_modes(self):
        report = deprecated.Report("some-policy")
        report.mode = [
            deprecated.field('foo', 'bar', '2021-06-30'),
            deprecated.field('baz', 'yet', '2021-06-30'),
        ]
        self.assertTrue(report.has_deprecations)
        self.assertEqual(report.format(), dedent("""
            policy 'some-policy'
              mode:
                field 'foo' has been deprecated (replaced by 'bar')
                field 'baz' has been deprecated (replaced by 'yet')
            """)[1:-1])

    # No examples of resource deprecation just yet. Looking for one.

    def test_one_action(self):
        report = deprecated.Report("some-policy")
        report.actions = [
            deprecated.Context(
                'mark-for-op:', deprecated.optional_field('tag', '2021-06-30')),
        ]
        self.assertTrue(report.has_deprecations)
        self.assertEqual(report.format(), dedent("""
            policy 'some-policy'
              actions: mark-for-op: optional field 'tag' deprecated (must be specified)
            """)[1:-1])

    def test_two_actions(self):
        report = deprecated.Report("some-policy")
        report.actions = [
            deprecated.Context(
                'mark-for-op:', deprecated.optional_fields(('hours', 'days'), '2021-06-30')),
            deprecated.Context(
                'mark-for-op:', deprecated.optional_field('tag', '2021-06-30')),
        ]
        self.assertTrue(report.has_deprecations)
        self.assertEqual(report.format(), dedent("""
            policy 'some-policy'
              actions:
                mark-for-op: optional fields deprecated (one of 'hours' or 'days' must be specified)
                mark-for-op: optional field 'tag' deprecated (must be specified)
            """)[1:-1])
