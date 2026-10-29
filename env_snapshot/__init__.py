"""Capture the computational environment of an analysis for reproducibility."""
from .core import snapshot, diff_snapshots, to_markdown, git_info

__version__ = "0.1.0"
__all__ = ["snapshot", "diff_snapshots", "to_markdown", "git_info"]
