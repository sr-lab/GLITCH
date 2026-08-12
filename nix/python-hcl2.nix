{
  lib,
  buildPythonPackage,
  fetchFromGitHub,
  setuptools,
  setuptools-scm,
  lark,
  typing-extensions,
}:

buildPythonPackage rec {
  pname = "python-hcl2";
  version = "0.1.dev296";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "Nfsaavedra";
    repo = "python-hcl2";
    rev = "986d879aa65e800322221d61169d52d5111ce7e6";
    hash = "sha256-2Bu1Klgi/3bTvkqJIwHswtKQhs4fLk3x8PcG/w4mYuc=";
  };

  env.SETUPTOOLS_SCM_PRETEND_VERSION = version;

  build-system = [
    setuptools
    setuptools-scm
  ];

  dependencies = [
    lark
    typing-extensions
  ];

  doCheck = false;

  pythonImportsCheck = [ "hcl2" ];
}
