"""Raw log loading utilities.

This stage is responsible for turning a run directory into a set of readable
inputs for the rest of the pipeline. It should enumerate files, read supported
log inputs, and preserve source lineage so later reports can point back to the
original evidence.
"""
