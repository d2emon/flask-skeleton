import sys
import shutil
import subprocess


import config


from utils import colors
from template import next_step


def log_error(logfile='error.log', error="", msg="", exit_on_error=True):
    if not error:
        return
    with open(logfile, 'w') as fd:
        fd.write(error.decode('utf-8'))
        print("{red}{msg} Please consult {yellow}{logfile}{red} file for details.{end}".format(
            msg=msg,
            logfile=logfile,
            red=colors.FAIL,
            yellow=colors.WARNING,
            end=colors.ENDC
        ))
        if exit_on_error:
            sys.exit(2)


def run(params, logfile, msg, exit_on_error=True):
    output, error = subprocess.Popen(
        params,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ).communicate()
    log_error(
        logfile,
        error,
        msg,
        exit_on_error
    )


class External():
    _util = None
    errors = []
    cmd_name = ""
    error_msg = ""

    @classmethod
    def cmd(cls):
        if cls._util is None:
            cls._util = shutil.which(cls.cmd_name)
        if not cls._util:
            cls.errors.append(cls.error_msg)
        return cls._util


class Bower(External):
    cmd_name = "bower"
    error_msg = 'Bower executable could not be found.'

    @classmethod
    @next_step("Bower")
    def install(cls, dependency):
        print("{}...\t\t\t".format(dependency.title()), end="", flush=True)
        run(
            [cls.cmd(), 'install', dependency],
            config.LOG_BOWER,
            "An error occured during the installation of {dep}.".format(
                dep=dependency
            ),
            False
        )


class Virtualenv(External):
    cmd_name = "virtualenv"
    error_msg = 'Virtualenv executable could not be found.'

    @classmethod
    @next_step("Creating the virtualenv...\t")
    def install(cls, venv_dir):
        # If virtualenv is requested, then create it and install the required libs to work
        run(
            [cls.cmd(), venv_dir, '--no-site-package'],
            config.LOG_VIRTUALENV,
            "An error occured during the creation of the virtualenv."
        )

    @classmethod
    @next_step("Installing Python Dependencies...")
    def install_dependencies(cls, pip_file, requirements_file):
        run(
            [pip_file, 'install', '-r', requirements_file],
            config.LOG_PIP,
            "An error occured during the installation of dependencies.",
        )


class Git(External):
    _util = "git"
    cmd_name = "git"

    @classmethod
    @next_step("Git Init...\t\t\t")
    def install(cls, app_path):
        run(
            [cls.cmd(), 'init', app_path],
            config.LOG_GIT,
            "An error occured during the creation of the virtualenv."
        )
