# Copyright 2020 Cloud Custodian Authors.
# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0

# Initial thinking around the deprecation is identifying changes in filters and
# actions. These are likely to be the most common aspects:
#  * renaming a field
#  * making an optional field required
#  * removing a field
#
# Examples:
#  - renaming a filter itself
# c7n_azure/resources/key_vault
# @KeyVault.filter_registry.register('whitelist')
# - filter 'whitelist' has been deprecated (replaced by 'allow') and will be removed after 2021-03-21
#
# - mark -> tag
# - unmark, untag -> remove-tag
#
#
#  - renaming filter attributes
# c7n/filters/iamaccess
#    schema = type_schema(
#        'cross-account',
#        ...
#        whitelist_from={'$ref': '#/definitions/filters_common/value_from'},
#        whitelist={'type': 'array', 'items': {'type': 'string'}},
#        ...)
# - filter field 'whitelist' has been deprecated (replaced by 'allow') and will be removed after 2021-03-21
#
#
# c7n/tags.py
#  - optional attributes becoming required, in this case one of 'days' or 'hours'
#  - optional action fields deprecated (one of 'days' or 'hours' must be specified) and will become an error after 2021-03-21
#  - optional action field 'tag' deprecated (must be specified) and will become an error after 2021-03-21
#

from datetime import datetime


def action(name, replacement, removed_after):
    """The action has been superseded by another action."""
    return DeprecatedElement('action', name, replacement, removed_after)


def alias(name, removed_after=None, link=None):
    """A filter or action alias is deprecated."""
    return DeprecatedAlias(name, removed_after, link)


def filter(name, replacement, removed_after):
    """The filter has been superseded by another filter."""
    return DeprecatedElement('filter', name, replacement, removed_after)


def field(name, replacement, removed_after):
    """The field has been renamed to something else."""
    return DeprecatedField(name, replacement, removed_after)


def optional_field(name, removed_after):
    """The field must now be specified."""
    return DeprecatedOptionality([name], removed_after)


def optional_fields(names, removed_after):
    """One of the field names must now be specified."""
    return DeprecatedOptionality(names, removed_after)


class Deprecation:
    """Base class for different deprecation types."""

    def __init__(self, removed_after, link):
        """All deprecations can have a removal date, and a link to docs.

        Both of these fields are optional.

        removed_after if specified must be a string representing an ISO8601 date.
        """
        # Question here:
        #  to speed up initialization, should we move the datetime checking to a unit test?
        if removed_after is not None:
            if not isinstance(removed_after, str):
                raise TypeError("removed_after attribute must be a string")
            try:
                datetime.strptime(removed_after, "%Y-%m-%d")
            except:
                raise TypeError(f"removed_after attribute must be a valid date in the format 'YYYY-MM-DD', got '{removed_after}'")

        self.removed_after = removed_after
        self.link = link

    def check(self, data):
        return True


class DeprecatedAlias(Deprecation):
    def __init__(self, name, removed_after=None, link=None):
        super().__init__(removed_after, link)
        self.name = name

    def __str__(self):
        return f"alias '{self.name}' has been deprecated"

    def check(self, data):
        return data.get("type") == self.name


class DeprecatedField(Deprecation):
    def __init__(self, name, replacement, removed_after=None, link=None):
        super().__init__(removed_after, link)
        self.name = name
        self.replacement = replacement

    def __str__(self):
        # filter or action prefix added by Filter and Action classes
        name, replacement = self.name, self.replacement
        # If the replacement is a single word we surround it with quotes,
        # otherwise we just use the replacement as is.
        if ' ' not in replacement:
            replacement = "'" + replacement + "'"
        return f"field '{name}' has been deprecated (replaced by {replacement})"

    def check(self, data):
        if self.name in data:
            return True
        return False


class DeprecatedElement(Deprecation):
    def __init__(self, type_name, name, replacement, removed_after=None, link=None):
        super().__init__(removed_after, link)
        self.type_name = type_name
        self.name = name
        self.replacement = replacement

    def __str__(self):
        # filter or action prefix added by Filter and Action classes
        typ, name, replacement = self.type_name, self.name, self.replacement
        return f"{typ} '{name}' has been deprecated ({replacement})"

    def check(self, data):
        return True


class DeprecatedOptionality(Deprecation):
    def __init__(self, fields, removed_after=None, link=None):
        super().__init__(removed_after, link)
        self.fields = fields

    def check(self, data):
        # check to see that they haven't specified the value
        return all([key not in data for key in self.fields])

    def __str__(self):
        when = self.removed_after
        if len(self.fields) > 1:
            quoted = [f"'{field}'" for field in self.fields]
            names = ' or '.join(quoted)
            return f"optional fields deprecated (one of {names} must be specified)"

        field = self.fields[0]
        return f"optional field '{field}' deprecated (must be specified)"


class Context:
    """Adds extra context to a deprecation."""
    def __init__(self, context, deprecation):
        self.context = context
        self.deprecation = deprecation

    def __str__(self):
        return f"{self.context} {self.deprecation}"


def check_deprecations(source, context=None, data=None):
    if data is None:
        data = getattr(source, 'data', {})
    deprecations = []
    for d in getattr(source, 'deprecations', ()):
        if d.check(data):
            if context is not None:
                d = Context(context, d)
            deprecations.append(d)
    return deprecations


class Report:
    """A deprecation report is generated per policy."""

    def __init__(self, policy_name):
        self.policy_name = policy_name
        self.policy_fields = []
        self.conditions = []
        self.mode = []
        self.resource = []
        self.filters = []
        self.actions = []

    @property
    def has_deprecations(self):
        # Start by checking the most likely things.
        if len(self.filters) > 0:
            return True
        if len(self.actions) > 0:
            return True
        if len(self.policy_fields) > 0:
            return True
        if len(self.conditions) > 0:
            return True
        if len(self.resource) > 0:
            return True
        if len(self.mode) > 0:
            return True
        return False

    def format(self, source_locator=None):
        """Format the report for output.

        If a source locator is specified, it is used to provide file and line number
        information for the policy.
        """
        location = ""
        if source_locator is not None:
            file_and_line = source_locator.find(self.policy_name)
            location = f" ({file_and_line})"
        lines = [f"policy '{self.policy_name}'{location}"]
        lines.extend(self.section('attributes', self.policy_fields))
        lines.extend(self.section('condition', self.conditions))
        lines.extend(self.section('mode', self.mode))
        lines.extend(self.section('resource', self.resource))
        lines.extend(self.section('filters', self.filters))
        lines.extend(self.section('actions', self.actions))
        return "\n".join(lines)

    def section(self, name, deprecations):
        count = len(deprecations)
        if count == 0:
            return ()
        if count == 1:
            return (f"  {name}: {deprecations[0]}",)
        result = [f"  {name}:"]
        result.extend([f"    {d}" for d in deprecations])
        return result

