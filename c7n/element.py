# Copyright 2020 Cloud Custodian Authors.
# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0

import jmespath

from c7n.executor import ThreadPoolExecutor


class Element:
    """Parent base class for filters and actions.
    """

    permissions = ()
    metrics = ()

    executor_factory = ThreadPoolExecutor

    schema = {'type': 'object'}
    # schema aliases get hoisted into a jsonschema definition
    # location, and then referenced inline.
    schema_alias = None

    def get_permissions(self):
        return self.permissions

    def validate(self):
        return self

    def filter_resources(self, resources, key_expr, allowed_values=()):
        # many filters implementing a resource state transition only allow
        # a given set of starting states, this method will filter resources
        # and issue a warning log, as implicit filtering in filters means
        # our policy metrics are off, and they should be added as policy
        # filters.
        resource_count = len(resources)
        search_expr = key_expr
        if not search_expr.startswith('[].'):
            search_expr = '[].' + key_expr
        results = [r for value, r in zip(
            jmespath.search(search_expr, resources), resources)
            if value in allowed_values]
        if resource_count != len(results):
            self.log.warning(
                "%s implicitly filtered %d of %d resources key:%s on %s",
                self.type, len(results), resource_count, key_expr,
                (', '.join(allowed_values)))
        return results
