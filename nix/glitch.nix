{
  self,
  buildPythonApplication,
  black,
  pyright,
  puppetparser,
  librego,
  bashlex,
  z3-solver,
  typing-extensions,
  tqdm,
  setuptools,
  ruamel-yaml,
  requests,
  python-hcl2,
  prettytable,
  ply,
  pandas,
  nltk,
  jsonschema,
  jinja2,
  configparser,
  click,
  poetry-core,
  pytestCheckHook,
  python,
  ruby,
  z3,
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
    python-hcl2
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

  # Place librego where the Python wrapper expects it (see README Rego build docs).
  # postPatch: pytest imports from the source tree, which otherwise has no .so.
  # postInstall: poetry skips gitignored *.so files when packaging.
  postPatch = ''
    mkdir -p glitch/rego/rego_python/src/rego_python/bin
    cp ${librego}/lib/librego-linux-amd64.so glitch/rego/rego_python/src/rego_python/bin/
  '';

  postInstall = ''
    bin_dir="$out/${python.sitePackages}/glitch/rego/rego_python/src/rego_python/bin"
    mkdir -p "$bin_dir"
    cp ${librego}/lib/librego-linux-amd64.so "$bin_dir/"
  '';

  pythonImportsCheck = [
    "glitch"
  ];

  nativeCheckInputs = [
    pytestCheckHook
    ruby
    z3
  ];

  enabledTestPaths = [ "tests" ];

  disabledTests = [
    # Ripper sexp for mix.rb changed on Ruby 3.x (CI uses 2.7.4).
    "test_chef_parser_mix"
    # Relies on `ulimit -v`, which the Nix sandbox does not enforce.
    "test_patch_solver_puppet_memory_limit"
  ];

  # CLI tests invoke the `glitch` script; patch solver shells out to `z3`.
  preCheck = ''
    export PATH="$out/bin:$PATH"
  '';

  dontCheckRuntimeDeps = true;
}
