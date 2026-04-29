# -*- coding: utf-8 -*-
"""This module contains the FastMCP server implementation for the EFF scorer."""

# Allow running as a script: add project root to sys.path for eff imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from fastmcp import FastMCP
from eff.scorer import score_story, DEFAULT_DIMENSIONS_PATH, DEFAULT_MODEL

mcp = FastMCP("eff-mcp")


@mcp.tool()
def ethics_filter(user_story: str) -> dict:
    """Run the Ethics Filter Framework on a user story."""
    return score_story(
        content=user_story,
        dimensions_path=DEFAULT_DIMENSIONS_PATH,
        model=DEFAULT_MODEL,
    )


if __name__ == "__main__":
    mcp.run()
