"""Fail-closed counts for reviewed component-test selections."""


def evaluate(expected, selected_ids, executed, failures=0, errors=0, skipped=0,
             expected_failures=0, unexpected_successes=0):
    """Return reviewed counts and whether the selection is a complete pass."""
    selected = len(selected_ids)
    distinct = len(set(selected_ids))
    counts = {
        'expected': expected,
        'selected': selected,
        'distinct': distinct,
        'executed': executed,
        'failures': failures,
        'errors': errors,
        'skipped': skipped,
        'expected_failures': expected_failures,
        'unexpected_successes': unexpected_successes,
    }
    counts['passed'] = (
        expected > 0 and selected == expected and distinct == expected
        and executed == expected and not failures and not errors and not skipped
        and not expected_failures and not unexpected_successes
    )
    return counts
