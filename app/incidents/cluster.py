"""Incident clustering logic.

This module merges related suspicious windows into broader candidate incidents
using time proximity and shared evidence. The output should remain traceable
back to concrete lines and templates.
"""
