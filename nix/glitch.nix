{
  self,
  buildPythonApplication,
  black,
  pyright,
  puppetparser,
  bashlex,
  z3-solver,
  typing-extensions,
  tqdm,
  setuptools,
  ruamel-yaml,
  requests,
  bc-python-hcl2,
  prettytable,
  ply,
  pandas,
  nltk,
  jsonschema,
  jinja2,
  configparser,
  click,
  poetry-core,
  pytestCheckHook
}:

buildPythonApplication {
  pname = "GLITCH";
  version = "glitch-${self.shortRev or "dirty"}";
  pyproject = true;

  src = self;

  build-system = [ poetry-core ];

  dependencies = [
    click
    configparser
    jinja2
    jsonschema
    nltk
    pandas
    ply
    prettytable
    bc-python-hcl2
    requests
    ruamel-yaml
    setuptools
    tqdm
    typing-extensions
    z3-solver
    bashlex
    puppetparser
    black
    pyright
  ];

  pythonImportsCheck = [
    "glitch"
  ];

  nativeCheckInputs = [
    pytestCheckHook
  ];

  dontCheckRuntimeDeps = true;
}


