import os


LOG_VIRTUALENV = "virtualenv-error.log"
LOG_PIP = "pip-error.log"
LOG_BOWER = "bower-error.log"
LOG_GIT = "git-error.log"

TPL_BRIEF = "brief.jinja2"
TPL_ERRORS = "errors.jinja2"

SRC_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SRC_DIR, ".."))
SCRIPT_DIR = os.path.join(BASE_DIR, "projects")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
