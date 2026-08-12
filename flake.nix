{
  description = "Flake for the Smelly GLITCH Project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};

      puppetparser = pkgs.python3Packages.callPackage ./nix/puppetparser.nix {};
      package = pkgs.python3Packages.callPackage ./nix/glitch.nix { inherit self puppetparser; };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          package
        ];
      };

      packages.${system}.default = package;
    };
}
