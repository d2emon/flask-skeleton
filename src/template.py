import os
import shutil
import jinja2
import platform

import config

from utils import colors
from external import Virtualenv, Bower, Git, run


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


def next_step(msg="Next step"):
    def next_step_decorator(f):
        def decorated(*args, **kwargs):
            print("{msg}\t".format(msg=msg), end="", flush=True)
            f(*args, **kwargs)
            print("{green}Ok{end}".format(green=colors.OKGREEN, end=colors.ENDC))
        return decorated
    return next_step_decorator


def generate(template_file='', template_vars=dict()):
    template = template_env.get_template(template_file)
    template_vars.update(global_vars)
    return template.render(template_vars)


def generate_brief(template_var):
    return generate(config.TPL_BRIEF, template_var)


def generate_errorlist(template_var):
    return generate(config.TPL_ERRORS, template_var)


@next_step("Creating the virtualenv...\t")
def install_virtualenv(venv_dir):
    # If virtualenv is requested, then create it and install the required libs to work
    run(
        [Virtualenv.cmd(), venv_dir, '--no-site-package'],
        config.LOG_VIRTUALENV,
        "An error occured during the creation of the virtualenv."
    )


@next_step("Installing Python Dependencies...")
def install_dependencies(pip_file, requirements_file):
    run(
        [pip_file, 'install', '-r', requirements_file],
        config.LOG_PIP,
        "An error occured during the installation of dependencies.",
    )


@next_step("Bower")
def install_bower(dependency):
    print("{}...\t\t\t".format(dependency.title()), end="", flush=True)
    run(
        [Bower.cmd(), 'install', dependency],
        config.LOG_BOWER,
        "An error occured during the installation of {dep}.".format(
            dep=dependency
        ),
        False
    )


@next_step("Git Init...\t\t\t")
def install_git(app_path):
    run(
        [Git.cmd(), 'init', app_path],
        config.LOG_GIT,
        "An error occured during the creation of the virtualenv."
    )


class ProjectTemplate():
    def __init__(self, skeleton_dir="skel", config_file="config.jinja2"):
        self.skeleton_dir = skeleton_dir
        self.config_file = config_file

    @property
    def source_dir(self):
        return os.path.join(config.SCRIPT_DIR, self.skeleton_dir)

    def generate_config(self, config):
        return generate(self.config_file, config)

    @property
    def gitignore(self):
        return os.path.join(config.BASE_DIR, 'templates', 'gitignore')

    def gitignore_file(self, project):
        return os.path.join(project.app_path, '.gitignore')

    def install(self, project):
        self.copy_skeleton(project)
        self.create_config(project)

        if project.git:
            install_git(project.app_path)
            self.install_gitignore(project)

    @next_step("Copying Skeleton...\t\t")
    def copy_skeleton(self, project):
        # Copying the whole skeleton into the new path. Error if the path already exists
        # TODO error handling here.
        shutil.copytree(self.source_dir, project.app_path)

    @next_step("Creating config file...\t\t")
    def create_config(self, project):
        # Creating the configuration file using the command line arguments
        with open(self.project_config_file(project), 'w') as fd:
            fd.write(self.generate_config(project.config))

    @next_step("Generating Gitignore...\t\t")
    def install_gitignore(self, project):
        shutil.copyfile(self.gitignore, self.gitignore_file(project))


class PythonProjectTemplate(ProjectTemplate):
    def venv_dir(self, project):
        return os.path.join(project.app_path, 'venv')

    def venv_bin_dir(self, project):
        return os.path.join(project.app_path, 'venv', 'bin')

    def pip_file(self, project):
        return os.path.join(self.venv_bin_dir(project), 'pip')

    def requirements_file(self, project):
        return os.path.join(project.app_path, 'requirements.txt')

    def install(self, project):
        ProjectTemplate.install(self, project)
        if project.virtualenv:
            install_virtualenv(self.venv_dir(project))
            install_dependencies(self.pip_file(project), self.requirements_file(project))
        if project.bower:
            os.chdir(self.static_dir(project))
            for dependency in project.bower:
                install_bower(dependency)


class FlaskProjectTemplate(PythonProjectTemplate):
    def static_dir(self, project):
        return os.path.join(project.app_path, 'app', 'static')

    def project_config_file(self, project):
        return os.path.join(project.app_path, 'config.py')


class FlaskDbProjectTemplate(FlaskProjectTemplate):
    def __init__(self, skeleton_dir="skel_db", config_file="config_db.jinja2"):
        FlaskProjectTemplate.__init__(self, skeleton_dir, config_file)
        self.database = True
