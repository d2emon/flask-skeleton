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

import config

from utils import colors, query_yes_no


# Environment variables
cwd = os.getcwd()

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

    def install(self, project):
        self.copy_skeleton(project)
        self.create_config(project)

        if project.virtualenv:
            self.install_virtualenv(project)
        if project.bower:
            self.install_bower(project, bower=project.bower)
        if project.git:
            self.install_git(project)

    def copy_skeleton(self, project):
        # Copying the whole skeleton into the new path. Error if the path already exists
        # TODO error handling here.
        print('Copying Skeleton...\t\t\t', end="", flush=True)
        shutil.copytree(self.source_dir, project.app_path)
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def create_config(self, project):
        # Creating the configuration file using the command line arguments
        print('Creating config file...\t\t\t', end="", flush=True)
        with open(project.config_file, 'w') as fd:
            fd.write(self.generate_config(project.config))
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def install_virtualenv(self, project):
        # If virtualenv is requested, then create it and install the required libs to work
        print('Creating the virtualenv...\t\t', end="", flush=True)
        output, error = subprocess.Popen(
            [self.externals.virtualenv, project.venv_dir, '--no-site-package'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        log_error(
            config.LOG_VIRTUALENV,
            error,
            "An error occured during the creation of the virtualenv."
        )
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))
        self.install_dependencies(project)

    def install_dependencies(self, project):
        print("Installing Python Dependencies...\t", end="", flush=True)
        output, error = subprocess.Popen(
            [project.pip_file, 'install', '-r', project.requirements_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        log_error(
            config.LOG_PIP,
            error,
            "An error occured during the installation of dependencies.",
        )
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

    def install_bower(self, project, bower=[]):
        os.chdir(project.static_dir)
        for dependency in bower:
            print("Bower {}...\t\t\t".format(dependency.title()), end="", flush=True)
            output, error = subprocess.Popen(
                [self.externals.bower, 'install', dependency],
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

    def install_git(self, project):
        print('Git Init...\t\t\t\t', end="", flush=True)
        output, error = subprocess.Popen(
            [self.externals.git, 'init', project.app_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        log_error(
            config.LOG_GIT,
            error,
            "An error occured during the creation of the virtualenv."
        )
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))

        print('Generating Gitignore...\t\t\t', end="", flush=True)
        shutil.copyfile(self.gitignore, project.gitignore_file)
        print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))


class Project():
    def __init__(self, appname="app", template=None):
        self.appname = appname
        if template is None:
            template = ProjectTemplate()
        self.template = template

        self.secret_key = codecs.encode(os.urandom(32), 'hex').decode('utf-8')
        self.debug = True

        self.virtualenv = False
        self.bower = []
        self.git = False

    @property
    def app_path(self):
        return os.path.join(cwd, self.appname)

    @property
    def venv_dir(self):
        return os.path.join(self.app_path, 'venv')

    @property
    def venv_bin_dir(self):
        return os.path.join(self.app_path, 'venv', 'bin')

    @property
    def static_dir(self):
        return os.path.join(self.app_path, 'app', 'static')

    @property
    def pip_file(self):
        return os.path.join(self.venv_bin_dir, 'pip')

    @property
    def config_file(self):
        return os.path.join(self.app_path, 'config.py')

    @property
    def requirements_file(self):
        return os.path.join(self.app_path, 'requirements.txt')

    @property
    def gitignore_file(self):
        return os.path.join(self.app_path, '.gitignore')

    @property
    def config_template(self):
        return template_env.get_template(self.template.config_file)

    @property
    def config(self):
        return {
            'secret_key': self.secret_key,
            'debug': self.debug,
        }

    @property
    def brief_var(self):
        brief_var = {
            'appname': self.appname,
            'bower': self.bower,
            'debug': self.debug,
            'virtualenv': self.virtualenv,
            'secret_key': self.secret_key,
            'path': self.app_path,
            'database': self.template.database,
            'git': self.git,
        }
        # bower = None
        if self.bower:
            brief_var['bower_exe'] = self.template.externals.bower
        if self.virtualenv:
            brief_var['virtualenv_exe'] = self.template.externals.virtualenv
        return brief_var

    def install(self):
        self.template.install(self)


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
    project = Project(appname, project_template)

    project.debug = debug

    project.bower = bower
    project.virtualenv = virtualenv
    project.git = git

    print(generate_brief(project.brief_var))
    if project_template.externals.has_errors:
        errors = project_template.externals.errors
        print(generate_errorlist({'errors': errors, }))
        sys.exit(1)

    if query_yes_no("Is this correct ?"):
        project.install()
    else:
        print("Aborting")
        sys.exit(0)


if __name__ == '__main__':
    main(sys.argv)
