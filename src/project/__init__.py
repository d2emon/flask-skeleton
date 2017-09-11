import os
import shutil
import jinja2


import config


from external import Git
from template import next_step, global_vars


# Environment variables
cwd = os.getcwd()


class Project():
    template_name = "skel"
    config_file = "config.jinja2"
    readme_file = "readme.jinja2"

    templates_dir = config.SCRIPT_DIR

    version = "0.1.0"
    description = "Dummy description"
    database = False

    def __init__(self, appname="app", apppath="temp", **kwargs):
        self.appname = appname
        self.apppath = apppath

        self.git = kwargs.get('git', False)

    @property
    def app_path(self):
        return os.path.join(cwd, self.apppath, self.appname)

    @property
    def brief_var(self):
        brief_var = {
            'appname': self.appname,
            'path': self.app_path,
            'git': self.git,
        }
        return brief_var

    @classmethod
    def tpl_path(cls):
        return os.path.join(cls.templates_dir, cls.template_name)

    @property
    def source_path(self):
        return os.path.join(self.tpl_path(), 'src')

    @property
    def version_file(self):
        return os.path.join(self.app_path, 'VERSION')

    @property
    def project_readme_file(self):
        return os.path.join(self.app_path, 'README.md')

    @classmethod
    def get_template(cls, filename):
        template_loader = jinja2.FileSystemLoader(searchpath=cls.tpl_path())
        template_env = jinja2.Environment(loader=template_loader)
        return template_env.get_template(filename)

    @classmethod
    def generate(cls, template_file, template_vars=dict()):
        template = cls.get_template(template_file)
        template_vars.update(global_vars)
        return template.render(template_vars)

    @classmethod
    def generate_config(cls, config):
        return cls.generate(cls.config_file, config)

    @classmethod
    def generate_readme(cls, config):
        return cls.generate(cls.readme_file, config)

    @property
    def gitignore_template(self):
        return os.path.join(self.templates_dir, 'gitignore')

    @property
    def gitignore_file(self):
        return os.path.join(self.app_path, '.gitignore')

    def install(self):
        self.copy_skeleton()
        self.create_config()
        self.create_version()
        self.create_readme()

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

    @next_step("Setting version file...\t\t")
    def create_version(self):
        with open(self.version_file, 'w') as fd:
            fd.write(self.version)

    @next_step("Creating readme file...\t\t")
    def create_readme(self):
        with open(self.project_readme_file, 'w') as fd:
            fd.write(self.generate_readme(self.config))
