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
      jinja2 = pkgs.python3Packages.callPackage ./nix/jinja2.nix {};
      python-hcl2 = pkgs.python3Packages.callPackage ./nix/python-hcl2.nix {};
      librego = pkgs.callPackage ./nix/librego.nix {};
      package = pkgs.python3Packages.callPackage ./nix/glitch.nix {
        inherit self puppetparser librego jinja2 python-hcl2;
        z3 = pkgs.z3;
      };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          package
          pkgs.ruby
          pkgs.z3
          pkgs.python3Packages.pytest
        ];
      };

      packages.${system} = {
        default = package;
        librego = librego;
      };
    };
}
