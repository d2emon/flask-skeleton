import os
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
    def install(cls, static_dir, dependencies):
        os.chdir(static_dir)
        for dependency in dependencies:
            cls.install_dependency(dependency)

    @classmethod
    @next_step("Bower")
    def install_dependency(cls, dependency):
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
    def venv_bin_dir(cls, venv_path):
        return os.path.join(venv_path, 'bin')

    @classmethod
    def pip_bin(cls, venv_path):
        return os.path.join(cls.venv_bin_dir(venv_path), 'pip')

    @classmethod
    def install(cls, venv_path, requirements_file):
        cls.install_venv(venv_path)
        cls.install_dependencies(venv_path, requirements_file)

    @classmethod
    @next_step("Creating the virtualenv...\t")
    def install_venv(cls, venv_path):
        # If virtualenv is requested, then create it and install the required libs to work
        run(
            [cls.cmd(), venv_path, '--no-site-package'],
            config.LOG_VIRTUALENV,
            "An error occured during the creation of the virtualenv."
        )

    @classmethod
    @next_step("Installing Python Dependencies...")
    def install_dependencies(cls, venv_path, requirements_file):
        run(
            [cls.pip_bin(venv_path), 'install', '-r', requirements_file],
            config.LOG_PIP,
            "An error occured during the installation of dependencies.",
        )


class Git(External):
    _util = "git"
    cmd_name = "git"

    @classmethod
    def install(cls, app_path, gitignore_template, gitignore_file):
        cls.install_git(app_path)
        cls.install_gitignore(gitignore_template, gitignore_file)

    @classmethod
    @next_step("Git Init...\t\t\t")
    def install_git(cls, app_path):
        run(
            [cls.cmd(), 'init', app_path],
            config.LOG_GIT,
            "An error occured during the creation of the virtualenv."
        )

    @classmethod
    @next_step("Generating Gitignore...\t\t")
    def install_gitignore(cls, gitignore_template, gitignore_file):
        shutil.copyfile(gitignore_template, gitignore_file)
