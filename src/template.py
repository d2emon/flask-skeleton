import os
import sys
import shutil
import jinja2
import platform
import subprocess

import config

from utils import colors


# Jinja2 Environment
template_loader = jinja2.FileSystemLoader(searchpath=config.TEMPLATE_DIR)
template_env = jinja2.Environment(loader=template_loader)


global_vars = {
    'pyversion': platform.python_version(),
    'require': colors.WARNING,
    'enabled': colors.OKGREEN,
    'disabled': colors.FAIL,
    'red': colors.FAIL,
    'end': colors.ENDC,
}


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


def generate(template_file='', template_vars=dict()):
    template = template_env.get_template(template_file)
    template_vars.update(global_vars)
    return template.render(template_vars)


def generate_brief(template_var):
    return generate(config.TPL_BRIEF, template_var)


def generate_errorlist(template_var):
    return generate(config.TPL_ERRORS, template_var)


class Externals():
    __bower = None
    __virtualenv = None
    __git = "git"

    def __init__(self):
        self.errors = []

    @property
    def bower(self):
        if self.__bower is None:
            self.__bower = shutil.which('bower')
        if not self.__bower:
            self.errors.append('Bower executable could not be found.')
        return self.__bower

    @property
    def virtualenv(self):
        if self.__virtualenv is None:
            self.__virtualenv = shutil.which('virtualenv')
        if not self.__virtualenv:
            self.errors.append('Virtualenv executable could not be found.')
        return self.__virtualenv

    @property
    def git(self):
        return self.__git

    @property
    def has_errors(self):
        return len(self.errors) > 0

    def install_virtualenv(self, venv_dir):
        # If virtualenv is requested, then create it and install the required libs to work
        print('Creating the virtualenv...\t\t', end="", flush=True)
        output, error = subprocess.Popen(
            [self.virtualenv, venv_dir, '--no-site-package'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        log_error(
            config.LOG_VIRTUALENV,
            error,
            "An error occured during the creation of the virtualenv."
        )
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def install_dependencies(self, pip_file, requirements_file):
        print("Installing Python Dependencies...\t", end="", flush=True)
        output, error = subprocess.Popen(
            [pip_file, 'install', '-r', requirements_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        log_error(
            config.LOG_PIP,
            error,
            "An error occured during the installation of dependencies.",
        )
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def install_bower(self, dependency):
        print("Bower {}...\t\t\t".format(dependency.title()), end="", flush=True)
        output, error = subprocess.Popen(
            [self.bower, 'install', dependency],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        log_error(
            config.LOG_BOWER,
            error,
            "An error occured during the installation of {dep}.".format(
                dep=dependency
            ),
            False
        )
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def install_git(self, app_path):
        print('Git Init...\t\t\t\t', end="", flush=True)
        output, error = subprocess.Popen(
            [self.git, 'init', app_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        log_error(
            config.LOG_GIT,
            error,
            "An error occured during the creation of the virtualenv."
        )
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))


class ProjectTemplate():
    def __init__(self, skeleton_dir="skel", config_file="config.jinja2"):
        self.skeleton_dir = skeleton_dir
        self.config_file = config_file

        self.externals = Externals()

    @property
    def source_dir(self):
        return os.path.join(config.SCRIPT_DIR, self.skeleton_dir)

    def generate_config(self, config):
        return generate(self.config_file, config)

    @property
    def gitignore(self):
        return os.path.join(config.BASE_DIR, 'templates', 'gitignore')

    def venv_dir(self, project):
        return os.path.join(project.app_path, 'venv')

    def venv_bin_dir(self, project):
        return os.path.join(project.app_path, 'venv', 'bin')

    def static_dir(self, project):
        return os.path.join(project.app_path, 'app', 'static')

    def pip_file(self, project):
        return os.path.join(self.venv_bin_dir(project), 'pip')

    def project_config_file(self, project):
        return os.path.join(project.app_path, 'config.py')

    def requirements_file(self, project):
        return os.path.join(project.app_path, 'requirements.txt')

    def gitignore_file(self, project):
        return os.path.join(project.app_path, '.gitignore')

    def install(self, project):
        self.copy_skeleton(project)
        self.create_config(project)

        if project.virtualenv:
            self.externals.install_virtualenv(self.venv_dir(project))
            self.externals.install_dependencies(self.pip_file(project), self.requirements_file(project))
        if project.bower:
            os.chdir(self.static_dir(project))
            for dependency in project.bower:
                self.externals.install_bower(dependency)
        if project.git:
            self.externals.install_git(project.app_path)
            self.install_gitignore(project)

    def copy_skeleton(self, project):
        # Copying the whole skeleton into the new path. Error if the path already exists
        # TODO error handling here.
        print('Copying Skeleton...\t\t\t', end="", flush=True)
        shutil.copytree(self.source_dir, project.app_path)
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def create_config(self, project):
        # Creating the configuration file using the command line arguments
        print('Creating config file...\t\t\t', end="", flush=True)
        with open(self.project_config_file(project), 'w') as fd:
            fd.write(self.generate_config(project.config))
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def install_gitignore(self, project):
        print('Generating Gitignore...\t\t\t', end="", flush=True)
        shutil.copyfile(self.gitignore, self.gitignore_file(project))
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))
