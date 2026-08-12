{
  buildPythonPackage,
  fetchFromGitHub,
  flit-core,
  markupsafe,
}:

buildPythonPackage rec {
  pname = "jinja2";
  version = "unstable-${src.rev}";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "Nfsaavedra";
    repo = "jinja";
    rev = "ab3be80906494926ab47da0b103af6fa2c6ca544";
    hash = "sha256-XPTWtkkm93gd/9RYFmifPRWFsaWpxKIW+oqpl1b2414=";
  };

  build-system = [ flit-core ];

  dependencies = [ markupsafe ];

  doCheck = false;

  pythonImportsCheck = [ "jinja2" ];
}
