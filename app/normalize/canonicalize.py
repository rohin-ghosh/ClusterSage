"""Canonicalization routines for unstable log content.

This module will turn variant-heavy raw lines into more comparable normalized
forms by replacing IDs, addresses, and other noisy fields with placeholders.
The resulting text should be easier to group and rank while still traceable to
the original log line.
"""
