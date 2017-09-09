#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import shutil
import jinja2
import codecs
import platform
import subprocess

from utils import colors, query_yes_no


LOG_VIRTUALENV = "virtualenv-error.log"
LOG_PIP = "pip-error.log"
LOG_BOWER = "bower-error.log"
LOG_GIT = "git-error.log"


# Environment variables
cwd = os.getcwd()
base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
script_dir = os.path.join(base_dir, "projects")

# Jinja2 Environment
template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(base_dir, "templates"))
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


class ProjectTemplate():
    def __init__(self, skeleton_dir="skel", config_file="config.jinja2"):
        self.appname = "app"
        self.errors = []
        self.skeleton_dir = skeleton_dir
        self.config_file = config_file
        self.secret_key = codecs.encode(os.urandom(32), 'hex').decode('utf-8')
        self.debug = True

        self.externals = Externals()

        self.database = False

        self.bower = []
        self.virtualenv = False
        self.git = False

    @property
    def source_dir(self):
        return os.path.join(script_dir, self.skeleton_dir)

    @property
    def static_dir(self):
        return os.path.join(self.fullpath, 'app', 'static')

    @property
    def template_var(self):
        template_var = {
            'appname': self.appname,
            'bower': self.bower,
            'debug': self.debug,
            'virtualenv': self.virtualenv,
            'secret_key': self.secret_key,
            'path': self.fullpath,
            'database': self.database,
            'git': self.git,
        }
        # bower = None
        if self.bower:
            template_var['bower_exe'] = self.externals.bower
        if self.virtualenv:
            template_var['virtualenv_exe'] = self.externals.virtualenv
        return template_var

    @property
    def config_var(self):
        return {
            'secret_key': self.secret_key,
            'debug': self.debug,
        }

    @property
    def template(self):
        return template_env.get_template(self.config_file)

    def generate_config(self):
        return generate(self.config_file, self.config_var)

    @property
    def fullpath(self):
        return os.path.join(cwd, self.appname)

    @property
    def venv_dir(self):
        return os.path.join(self.fullpath, 'venv')

    @property
    def venv_bin(self):
        return os.path.join(self.fullpath, 'venv', 'bin')

    @property
    def pip_bin(self):
        return os.path.join(self.venv_bin, 'pip')

    @property
    def requirements(self):
        return os.path.join(self.fullpath, 'requirements.txt')

    @property
    def config(self):
        return os.path.join(self.fullpath, 'config.py')

    @property
    def gitignore_template(self):
        return os.path.join(base_dir, 'templates', 'gitignore')

    @property
    def gitignore(self):
        return os.path.join(self.fullpath, '.gitignore')

    def install(self):
        self.copy_skeleton()
        self.create_config()

        if self.virtualenv:
            self.install_virtualenv()
        if self.bower:
            self.install_bower(bower=self.bower)
        if self.git:
            self.install_git()

    def copy_skeleton(self):
        # Copying the whole skeleton into the new path. Error if the path already exists
        # TODO error handling here.
        print('Copying Skeleton...\t\t\t', end="", flush=True)
        shutil.copytree(self.source_dir, self.fullpath)
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def create_config(self):
        # Creating the configuration file using the command line arguments
        print('Creating config file...\t\t\t', end="", flush=True)
        with open(self.config, 'w') as fd:
            fd.write(self.generate_config())
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def install_virtualenv(self):
        # If virtualenv is requested, then create it and install the required libs to work
        print('Creating the virtualenv...\t\t', end="", flush=True)
        output, error = subprocess.Popen(
            [self.externals.virtualenv, self.venv_dir, '--no-site-package'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        log_error(
            LOG_VIRTUALENV,
            error,
            "An error occured during the creation of the virtualenv."
        )
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))
        self.install_dependencies()

    def install_dependencies(self):
        print("Installing Python Dependencies...\t", end="", flush=True)
        output, error = subprocess.Popen(
            [self.pip_bin, 'install', '-r', self.requirements],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        log_error(
            LOG_PIP,
            error,
            "An error occured during the installation of dependencies.",
        )
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def install_bower(self, bower=[]):
        os.chdir(self.static_dir)
        for dependency in bower:
            print("Bower {}...\t\t\t".format(dependency.title()), end="", flush=True)
            output, error = subprocess.Popen(
                [self.externals.bower, 'install', dependency],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            ).communicate()
            log_error(
                LOG_BOWER,
                error,
                "An error occured during the installation of {dep}.".format(
                    dep=dependency
                ),
                False
            )
            print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def install_git(self):
        print('Git Init...\t\t\t\t', end="", flush=True)
        output, error = subprocess.Popen(
            [self.externals.git, 'init', self.fullpath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        log_error(
            LOG_GIT,
            error,
            "An error occured during the creation of the virtualenv."
        )
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

        print('Generating Gitignore...\t\t\t', end="", flush=True)
        shutil.copyfile(self.gitignore_template, self.gitignore)
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))


def generate(template_file='', template_vars=dict()):
    template = template_env.get_template(template_file)
    template_vars.update(global_vars)
    return template.render(template_vars)


def generate_brief(template_var):
    return generate('brief.jinja2', template_var)


def generate_errorlist(template_var):
    return generate('errors.jinja2', template_var)


def generate_crsf_secret_key():
    return


def main(argv):
    parser = argparse.ArgumentParser(description='Create a skeleton application using some command line options.')
    parser.add_argument('appname', help='The application name')
    parser.add_argument('-b', '--bower', help='Dependencies installed using bower')
    parser.add_argument('-n', '--no-debug', action='store_false')
    parser.add_argument('-v', '--virtualenv', action='store_true')
    parser.add_argument('-d', '--database', action='store_true')
    parser.add_argument('-g', '--git', action='store_true')
    args = parser.parse_args()

    bower_deps = None
    if args.bower:
        bower_deps = args.bower.split(',')

    install(
        bower=bower_deps,
        virtualenv=args.virtualenv,
        debug=args.no_debug,
        appname=args.appname,
        database=args.database,
        git=args.git,
    )


def install(bower=None, virtualenv=False, debug=False, appname="", database=None, git=None):
    if database:
        project_template = ProjectTemplate(
            skeleton_dir='skel_db',
            config_file='config_db.jinja2',
        )
        project_template.database = True
    else:
        project_template = ProjectTemplate()

    project_template.appname = appname
    project_template.debug = debug

    project_template.bower = bower
    project_template.virtualenv = virtualenv
    project_template.git = git

    print(generate_brief(project_template.template_var))
    if project_template.externals.has_errors:
        errors = project_template.externals.errors
        print(generate_errorlist({'errors': errors, }))
        sys.exit(1)

    if query_yes_no("Is this correct ?"):
        project_template.install()
    else:
        print("Aborting")
        sys.exit(0)


if __name__ == '__main__':
    main(sys.argv)
