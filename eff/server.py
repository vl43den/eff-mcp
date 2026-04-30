# -*- coding: utf-8 -*-
"""This module contains the FastMCP server implementation for the EFF scorer."""
import sys
import os
from pathlib import Path
from fastmcp import FastMCP

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from eff.scorer import score_story, DEFAULT_DIMENSIONS_PATH, DEFAULT_MODEL
from eff.rewriter import rewrite_story

# Resource file paths
RESOURCES_PATH = Path(__file__).resolve().parent.parent / "resources"


mcp = FastMCP("eff-mcp")


#############
# MCP Tools #
#############

@mcp.tool()
def ethics_filter(user_story: str) -> dict:
    """Run the Ethics Filter Framework on a user story."""
    return score_story(
        content=user_story,
        dimensions_path=DEFAULT_DIMENSIONS_PATH,
        model=DEFAULT_MODEL,
    )


@mcp.tool()
def eff_rewrite(user_story: str, scoring_result: dict) -> dict:
    """Rewrite a user story using the EFF scoring result."""
    return rewrite_story(user_story, scoring_result)


#################
# MCP Resources #
#################

@mcp.resource("eff://dimensions")
def get_dimensions():
    """Serve the EFF dimensions.json as an MCP resource."""
    with open(RESOURCES_PATH / "dimensions.json", "r", encoding="utf-8") as f:
        return f.read()


@mcp.resource("eff://skill")
def get_skill():
    """Serve the EFF SKILL.md as an MCP resource."""
    with open(RESOURCES_PATH / "SKILL.md", "r", encoding="utf-8") as f:
        return f.read()


@mcp.resource("eff://examples")
def get_examples():
    """Serve the EFF examples.md as an MCP resource."""
    with open(RESOURCES_PATH / "examples.md", "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    mcp.run()
