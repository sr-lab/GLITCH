{
  lib,
  buildGoModule,
}:

buildGoModule {
  pname = "librego";
  version = "0.2.0";

  # Directory is named `go`, which breaks GOPATH; give the store path a safe name.
  src = builtins.path {
    path = ../glitch/rego/rego_python/src/rego_python/go;
    name = "librego-src";
  };

  vendorHash = "sha256-UNlQqxjxsY978cO+Oz9bH22FdemPrUhHiLgw9mFi5fI=";

  # Shared library; no Go unit tests to run via buildGoModule's checkPhase
  doCheck = false;

  # c-shared is incompatible with `go install` used by the default buildPhase
  buildPhase = ''
    runHook preBuild
    go build -o librego-linux-amd64.so -buildmode=c-shared .
    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p $out/lib
    cp librego-linux-amd64.so $out/lib/
    runHook postInstall
  '';

  meta = {
    description = "OPA Rego shared library used by GLITCH";
    platforms = [ "x86_64-linux" ];
  };
}
