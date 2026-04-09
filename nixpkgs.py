import json
import urllib.request
from dataclasses import dataclass
from urllib.error import URLError
from urllib.parse import urlencode

SEARCH_URL = "https://search.nixos.org/backend/latest-44-nixos-{}/_search"
# Public read-only credential from the search.nixos.org frontend
SEARCH_AUTH = "Basic YVdWU0FMWHBadjpYOGdQSG56TDUyd0ZFZWt1eHNmUTljU2g="


@dataclass
class Package:
    name: str
    version: str
    description: str


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
                name=src.get("package_attr_name", ""),
                version=src.get("package_pversion", ""),
                description=src.get("package_description") or "",
            )
        )

    return packages


def package_url(package_name: str, query: str, channel: str = "unstable") -> str:
    params = {"channel": channel, "query": query, "show": package_name}
    return "https://search.nixos.org/packages?" + urlencode(params)
