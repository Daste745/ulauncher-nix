import json
import urllib.request
from dataclasses import dataclass, field
from urllib.error import URLError
from urllib.parse import urlencode

# Use a wildcard for the index version to avoid needing to update it manually
# every time there's a new index.
# This means we'll get results from multiple indexes, which then have to be deduplicated.
# A single package can have multiple versions (and outputs) from different indexes.
#
# This approach is inspired by nix-search-cli's handling of search.nixos.org indexes.
# See: https://github.com/peterldowns/nix-search-cli/blob/main/pkg/nixsearch/esclient.go#L21
SEARCH_URL = "https://search.nixos.org/backend/latest-*-nixos-{}/_search"
# Public read-only credential from the search.nixos.org frontend
SEARCH_AUTH = "Basic YVdWU0FMWHBadjpYOGdQSG56TDUyd0ZFZWt1eHNmUTljU2g="


@dataclass
class Package:
    index: str
    name: str
    version: str
    description: str
    programs: list[str] = field(default_factory=list)
    main_program: str | None = None


def search(
    query: str,
    channel: str = "unstable",
    max_results: int = 8,
) -> list[Package]:
    body = json.dumps(
        {
            "from": 0,
            "size": max_results,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "package_pname^3",
                        "package_attr_name^2",
                        "package_programs^2",
                        "package_description",
                    ],
                    "type": "best_fields",
                }
            },
        }
    ).encode()

    req = urllib.request.Request(
        SEARCH_URL.format(channel),
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "ulauncher-nix",
            "Authorization": SEARCH_AUTH,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
    except (URLError, TimeoutError):
        return []

    packages: list[Package] = []
    for hit in data.get("hits", {}).get("hits", []):
        src = hit["_source"]
        packages.append(
            Package(
                index=hit.get("_index", ""),
                name=src.get("package_attr_name", ""),
                version=src.get("package_pversion", ""),
                description=src.get("package_description") or "",
                programs=src.get("package_programs") or [],
                main_program=src.get("package_mainProgram"),
            )
        )

    return packages


def package_url(package_name: str, query: str, channel: str = "unstable") -> str:
    params = {"channel": channel, "query": query, "show": package_name}
    return "https://search.nixos.org/packages?" + urlencode(params)


def package_attribute(name: str, pkgs_attrset: str = "pkgs") -> str:
    return f"{pkgs_attrset}.{name}"
