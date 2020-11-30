from __future__ import annotations

import datetime
from logging import getLogger
from typing import List, Optional

import requests
from dateutil import tz
from lander.ext.parser import DocumentMetadata, FormattedString, Parser, Person
from lander.ext.parser.pandoc import convert_text
from lander.ext.parser.texutils.extract import (
    LaTeXCommand,
    LaTeXCommandElement,
)
from pydantic import BaseModel

from rubinlander.parsers.lsstdoc.lsstmacros import LSSTDOC_MACROS

__all__ = ["LsstDocParser"]

logger = getLogger(__name__)


class LsstDocParser(Parser):
    """Lander metadata parser for lsstdoc-based documents."""

    def extract_metadata(self, tex_source: str) -> DocumentMetadata:
        """Plugin entrypoint for metadata extraction."""
        full_text = FormattedString.from_latex(self.tex_source, fragment=False)

        if self.ci_metadata.github_slug:
            _owner, _repo = self.ci_metadata.github_slug.split("/")
            github_metadata = GitHubMetadata.create(_owner, _repo)
        else:
            github_metadata = GitHubMetadata()

        metadata = DocumentMetadata(
            title=self._parse_title(tex_source),
            authors=LsstDocParser._parse_author(tex_source),
            date_modified=self._parse_date(tex_source),
            identifier=self._parse_doc_ref(tex_source),
            abstract=self._parse_abstract(tex_source),
            version=self.ci_metadata.git_ref,
            repository_url=self.ci_metadata.github_repository,
            ci_url=self.ci_metadata.build_url,
            license_identifier=github_metadata.license_id,
            full_text=full_text,
        )
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

        parsed_titles = [_ for _ in command.parse(tex_source)]
        if len(parsed_titles) == 0:
            logger.warning("lsstdoc has no title")
            title = ""
        else:
            title_content = prep_lsstdoc_latex(parsed_titles[-1]["long_title"])
            title = convert_text(
                content=title_content, source_fmt="latex", output_fmt="plain"
            )
        return title

    @staticmethod
    def _parse_author(tex_source: str) -> List[Person]:
        r"""Parse the author command from TeX source.

        Goal is to parse::

           \author{
           A.~Author,
           B.~Author,
           and
           C.~Author}

        Into::

           ['A. Author', 'B. Author', 'C. Author']
        """
        command = LaTeXCommand(
            "author",
            LaTeXCommandElement(name="authors", required=True, bracket="{"),
        )
        parsed_commands = [_ for _ in command.parse(tex_source)]
        if len(parsed_commands) == 0:
            logger.warning("lsstdoc has no author")
            authors: List[Person] = []
        else:
            content = parsed_commands[-1]["authors"]

            # Clean content
            content = content.replace("\n", " ")
            content = content.replace("~", " ")
            content = content.strip()

            # Split content into list of individual authors
            authors = []
            for part in content.split(","):
                part = part.strip()
                if "and" in part:
                    for split_part in part.split("and"):
                        split_part = split_part.strip()
                        if len(split_part) > 0:
                            authors.append(
                                LsstDocParser._parse_individual_author(
                                    split_part
                                )
                            )
                else:
                    authors.append(
                        LsstDocParser._parse_individual_author(part)
                    )

        return authors

    @staticmethod
    def _parse_individual_author(author_tex: str) -> Person:
        name = convert_text(
            content=prep_lsstdoc_latex(author_tex),
            source_fmt="latex",
            output_fmt="plain",
            deparagraph=True,
        )
        return Person(name=name)

    def _parse_date(self, tex_source: str) -> Optional[datetime.datetime]:
        r"""Parse the ``\date`` command as a datetime."""
        command = LaTeXCommand(
            "date",
            LaTeXCommandElement(name="content", required=True, bracket="{"),
        )
        parsed = [_ for _ in command.parse(tex_source)]
        if len(parsed) == 0:
            logger.warning("lsstdoc has no date command")
            return None

        command_content = parsed[-1]["content"].strip()

        # Try to parse a date from the \date command
        # if command_content == r"\today":
        #     return None
        if command_content is not None and command_content != r"\today":
            try:
                doc_datetime = datetime.datetime.strptime(
                    command_content, "%Y-%m-%d"
                )
                # Assume Noon LSST project time (Pacific) given a precise
                # date is not available.
                project_tz = tz.gettz("US/Pacific")
                doc_datetime = doc_datetime.replace(hour=12, tzinfo=project_tz)
                # Normalize to UTC
                doc_datetime = doc_datetime.astimezone(tz.UTC)
                return doc_datetime
            except ValueError:
                logger.warning(
                    "Could not parse a datetime from "
                    "lsstdoc date command: %r",
                    command_content,
                )

        # Fallback to parsing from Git
        try:
            doc_datetime = self.git_repository.compute_date_modified(
                extensions=["tex", "bib", "pdf", "jpg", "png", "csv"]
            )
            return doc_datetime
        except Exception:
            return None

    def _parse_doc_ref(self, tex_source: str) -> Optional[str]:
        """Parse the setDocRef command to get the document identifier."""
        command = LaTeXCommand(
            "setDocRef",
            LaTeXCommandElement(name="handle", required=True, bracket="{"),
        )
        parsed = [_ for _ in command.parse(tex_source)]
        if len(parsed) == 0:
            logger.warning("lsstdoc has no setDocRef")
            return None

        return parsed[-1]["handle"]

    def _parse_abstract(self, tex_source: str) -> Optional[FormattedString]:
        """Parse the setDocAbstract command."""
        command = LaTeXCommand(
            "setDocAbstract",
            LaTeXCommandElement(name="abstract", required=True, bracket="{"),
        )
        parsed = [_ for _ in command.parse(tex_source)]
        if len(parsed) == 0:
            logger.warning("lsstdoc has no abstract")
            return None

        content = parsed[-1]["abstract"].strip()

        return FormattedString.from_latex(prep_lsstdoc_latex(content))


def prep_lsstdoc_latex(content: str) -> str:
    return "\n".join((LSSTDOC_MACROS, content))


class GitHubMetadata(BaseModel):
    """Metadata about the GitHub repository obtained from the GitHub API."""

    license_id: Optional[str]
    """The SPDX licence identifier."""

    @classmethod
    def create(cls, owner: str, repo: str) -> GitHubMetadata:
        """Create a GitHubMetadata resource by making a request to the GitHub
        REST API.

        Parameters
        ----------
        owner : `str`
            The repository owner (organization or user).
        repo : `str`
            The repository name.

        Returns
        -------
        metadata : `GitHubMetadata`
            The initialized `GitHubMetadata` resource.
        """
        try:
            r = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            r.raise_for_status()
        except requests.HTTPError:
            return cls()

        data = r.json()
        try:
            license_id = data["license"]["spdx_id"]
        except KeyError:
            license_id = None

        return cls(license_id=license_id)
