import os
import codecs

from external import Virtualenv, Bower
from template import template_env
from .python import PythonProject


class FlaskProject(PythonProject):
    template_name = "flask"

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
            'appname': self.appname,
            'description': self.description,
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
        return self.app_path

    @property
    def project_config_file(self):
        return os.path.join(self.app_path, 'config.py')

    def install(self):
        PythonProject.install(self)
        if self.bower:
            Bower.install(self.static_dir, self.bower)


class FlaskDbProject(FlaskProject):
    template_name = "skel_db"
    database = True
