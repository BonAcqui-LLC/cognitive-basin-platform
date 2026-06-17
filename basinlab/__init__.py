"""
Public BasinLab package.

The canonical implementation lives under `python.basinlab`. This top-level
package is a thin compatibility wrapper so clean installs and `python -m
basinlab...` resolve consistently in local and CI environments.
"""

from python.basinlab import *  # noqa: F401,F403
