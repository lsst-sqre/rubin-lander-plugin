from __future__ import annotations

from logging import getLogger

from lander.ext.parser import DocumentMetadata, Parser
from lander.ext.parser.texutils.extract import (
    LaTeXCommand,
    LaTeXCommandElement,
)

__all__ = ["LsstDocParser"]

logger = getLogger(__name__)


class LsstDocParser(Parser):
    """Lander metadata parser for lsstdoc-based documents."""

    def extract_metadata(self, tex_source: str) -> DocumentMetadata:
        """Plugin entrypoint for metadata extraction."""
        metadata = DocumentMetadata(title=self._parse_title(tex_source))
        return metadata

    def _parse_title(self, tex_source: str) -> str:
        """Parse the title command from the lsstdoc."""
        command = LaTeXCommand(
            "title",
            LaTeXCommandElement(
                name="short_title", required=False, bracket="["
            ),
            LaTeXCommandElement(name="long_title", required=True, bracket="{"),
        )

        try:
            parsed = next(command.parse(tex_source))
        except StopIteration:
            logger.warning("lsstdoc has no title")
            title = ""

        title = parsed["long_title"]
        return title
