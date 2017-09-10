import os


from external import Virtualenv
from . import Project


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
