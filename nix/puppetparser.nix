{
  lib,
  ply,
  poetry-core,
  buildPythonPackage,
  fetchFromGitHub,
}:

buildPythonPackage rec {
  pname = "puppetparser";
  version = "unstable-${src.rev}";
  format = "pyproject";

  src = fetchFromGitHub {
    owner = "Nfsaavedra";
    repo = "puppetparser";
    rev = "e74b3e6ba55df93c24397d7b6032aed97de08966";
    hash = "sha256-SWFLWdJTS4xdZVR4QOXBg2iPlg6FwjmMH/8InmmBt+4=";
  };

  nativeBuildInputs = [
    poetry-core
  ];

  dependencies = [
    ply
  ];

  pythonImportsCheck = [
    "puppetparser"
  ];
}
