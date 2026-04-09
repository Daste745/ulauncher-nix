{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
  };

  outputs =
    { systems, nixpkgs, ... }:
    let
      eachSystem =
        f: nixpkgs.lib.genAttrs (import systems) (system: f (import nixpkgs { inherit system; }));
    in
    {
      devShells = eachSystem (pkgs: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            python3
            ulauncher
            (writeShellApplication {
              name = "install-extension";
              text = ''
                EXTENSIONS_DIR="$HOME/.local/share/ulauncher/extensions"
                EXTENSION_ID="com.github.daste745.ulauncher-nix"
                ln -s "$(pwd)" "$EXTENSIONS_DIR/$EXTENSION_ID"
              '';
            })
          ];
          shellHook = ''

          '';
        };
      });
    };
}
