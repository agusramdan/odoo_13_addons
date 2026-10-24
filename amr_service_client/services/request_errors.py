# -*- coding: utf-8 -*-
"""Safe extraction of diagnostic text from requests exceptions."""


def request_exception_text(error):
    """Return available response text and exception text without assuming response exists."""
    response = getattr(error, 'response', None)
    try:
        response_text = getattr(response, 'text', '') if response is not None else ''
    except Exception:
        response_text = ''
    try:
        exception_text = str(error)
    except Exception:
        exception_text = type(error).__name__
    return (response_text or '') + exception_text
