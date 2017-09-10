import os
import shutil


import config


from external import Git
from template import next_step, generate


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
