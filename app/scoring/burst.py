"""Burst scoring logic.

Burst heuristics detect sudden increases in event frequency across short time
windows. They help surface periods worth inspecting first when raw log volume
is too high for line-by-line review.
"""
