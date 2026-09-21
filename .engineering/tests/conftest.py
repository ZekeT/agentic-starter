"""Keep embedded project suites isolated from the starter test process."""

# test_semantic_fixtures runs these suites from each fixture's own project root.
collect_ignore = ["fixtures"]
