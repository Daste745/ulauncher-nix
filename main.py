import subprocess
from typing import TypedDict

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import ItemEnterEvent, KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

import nixpkgs


class Preferences(TypedDict):
    lookup: str
    run: str
    channel: str
    max_results: str
    run_feedback: str


class NixExtension(Extension):
    preferences: Preferences

    def __init__(self) -> None:
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(
        self,
        event: KeywordQueryEvent,
        extension: NixExtension,
    ) -> RenderResultListAction | None:
        query = event.get_argument()
        if not query:
            return RenderResultListAction([])

        if event.get_keyword() == extension.preferences["lookup"]:
            return self._handle_lookup(query, extension)

        if event.get_keyword() == extension.preferences["run"]:
            return self._handle_run(query, extension)

        return None

    def _handle_lookup(
        self,
        query: str,
        extension: NixExtension,
    ) -> RenderResultListAction:
        prefs = extension.preferences
        channel = prefs["channel"]
        max_results = int(prefs["max_results"])
        packages = nixpkgs.search(query, channel=channel, max_results=max_results)
        items = [
            ExtensionResultItem(
                icon="images/icon.png",
                name=format_pkg_name(pkg),
                description=pkg.description,
                on_enter=OpenUrlAction(nixpkgs.package_url(pkg.name, query, channel)),
            )
            for pkg in packages
        ]
        return RenderResultListAction(items)

    def _handle_run(
        self,
        query: str,
        extension: NixExtension,
    ) -> RenderResultListAction:
        prefs = extension.preferences
        channel = prefs["channel"]
        max_results = int(prefs["max_results"])
        packages = nixpkgs.search(
            query,
            channel,
            # Fetch extra results since we filter for packages with executables
            max_results=max_results * 3,
        )
        items: list[ExtensionResultItem] = []
        for pkg in packages:
            if len(pkg.programs) == 0:
                continue
            for program in pkg.programs:
                items.append(
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name=program,
                        description=format_pkg_name(pkg),
                        on_enter=ExtensionCustomAction(
                            {"package": pkg.name, "executable": program},
                            keep_app_open=prefs["run_feedback"] == "yes",
                        ),
                    )
                )
                if len(items) >= max_results:
                    break
            if len(items) >= max_results:
                break
        return RenderResultListAction(items)


def format_pkg_name(pkg: nixpkgs.Package) -> str:
    return f"{pkg.name} ({pkg.version})" if pkg.version else pkg.name


class ItemEnterEventListener(EventListener):
    def on_event(
        self,
        event: ItemEnterEvent,
        extension: NixExtension,
    ) -> RenderResultListAction | HideWindowAction:
        data = event.get_data()
        package = data["package"]
        executable = data["executable"]

        command = ["nix", "shell", f"nixpkgs#{package}", "-c", executable]
        subprocess.Popen(
            command,
            start_new_session=True,
        )

        if extension.preferences["run_feedback"] == "no":
            return HideWindowAction()

        return RenderResultListAction(
            [
                ExtensionResultItem(
                    icon="images/icon.png",
                    name=f"Starting {executable}...",
                    description=" ".join(command),
                    on_enter=HideWindowAction(),
                )
            ]
        )


if __name__ == "__main__":
    NixExtension().run()
