from typing import TypedDict

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

import nixpkgs


class Preferences(TypedDict):
    lookup: str
    channel: str
    max_results: str


class NixExtension(Extension):
    preferences: Preferences

    def __init__(self) -> None:
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(
        self,
        event: KeywordQueryEvent,
        extension: NixExtension,
    ) -> RenderResultListAction:
        query = event.get_argument()
        if not query:
            return RenderResultListAction([])

        prefs = extension.preferences
        channel = prefs["channel"]
        max_results = int(prefs["max_results"])
        packages = nixpkgs.search(query, channel=channel, max_results=max_results)
        items = [
            ExtensionResultItem(
                icon="images/icon.png",
                name=f"{pkg.name} ({pkg.version})",
                description=pkg.description,
                on_enter=OpenUrlAction(nixpkgs.package_url(pkg.name, query, channel)),
            )
            for pkg in packages
        ]

        return RenderResultListAction(items)


if __name__ == "__main__":
    NixExtension().run()
