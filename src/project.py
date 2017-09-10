import os
import shutil
import codecs


import config


from external import Virtualenv, Bower, Git
from template import template_env, next_step, generate


# Environment variables
cwd = os.getcwd()


class Project():
    source_dir = "skel"
    config_file = "config.jinja2"
    database = False

    def __init__(self, appname="app", **kwargs):
        self.appname = appname

        self.git = kwargs.get('git', False)

    @property
    def app_path(self):
        return os.path.join(cwd, self.appname)

    @property
    def brief_var(self):
        brief_var = {
            'appname': self.appname,
            'path': self.app_path,
            'git': self.git,
        }
        return brief_var

    @property
    def source_path(self):
        return os.path.join(config.SCRIPT_DIR, self.source_dir)

    @classmethod
    def generate_config(cls, config):
        return generate(cls.config_file, config)

    @property
    def gitignore_template(self):
        return os.path.join(config.BASE_DIR, 'templates', 'gitignore')

    @property
    def gitignore_file(self):
        return os.path.join(self.app_path, '.gitignore')

    def install(self):
        self.copy_skeleton()
        self.create_config()

        if self.git:
            Git.install(self.app_path, self.gitignore_template, self.gitignore_file)

    @next_step("Copying Skeleton...\t\t")
    def copy_skeleton(self):
        # Copying the whole skeleton into the new path. Error if the path already exists
        # TODO error handling here.
        shutil.copytree(self.source_path, self.app_path)

    @next_step("Creating config file...\t\t")
    def create_config(self):
        # Creating the configuration file using the command line arguments
        with open(self.project_config_file, 'w') as fd:
            fd.write(self.generate_config(self.config))


class PythonProject(Project):
    def __init__(self, appname="app", **kwargs):
        Project.__init__(self, appname, **kwargs)
        self.virtualenv = kwargs.get('virtualenv', False)

    @property
    def brief_var(self):
        brief_var = {
            'appname': self.appname,
            'virtualenv': self.virtualenv,
            'path': self.app_path,
            'git': self.git,
        }
        if self.virtualenv:
            brief_var['virtualenv_exe'] = Virtualenv.cmd()
        return brief_var

    @property
    def venv_dir(self):
        return os.path.join(self.app_path, 'venv')

    @property
    def requirements_file(self):
        return os.path.join(self.app_path, 'requirements.txt')

    def install(self):
        Project.install(self)
        if self.virtualenv:
            Virtualenv.install(self.venv_dir, self.requirements_file)


class FlaskProject(PythonProject):
    def __init__(self, appname="app", **kwargs):
        PythonProject.__init__(self, appname, **kwargs)

        self.secret_key = codecs.encode(os.urandom(32), 'hex').decode('utf-8')
        self.debug = kwargs.get('debug', True)
        self.bower = kwargs.get('bower', [])

    @property
    def config_template(self):
        return template_env.get_template(self.config_file)

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
            'database': self.database,
            'git': self.git,
        }
        # bower = None
        if self.bower:
            brief_var['bower_exe'] = Bower.cmd()
        if self.virtualenv:
            brief_var['virtualenv_exe'] = Virtualenv.cmd()
        return brief_var

    @property
    def static_dir(self):
        return os.path.join(self.app_path, 'app', 'static')

    @property
    def project_config_file(self):
        return os.path.join(self.app_path, 'config.py')

    def install(self):
        PythonProject.install(self)
        if self.bower:
            Bower.install(self.static_dir, self.bower)


class FlaskDbProject(FlaskProject):
    skeleton_dir = "skel_db"
    config_file = "config_db.jinja2"
    database = True
