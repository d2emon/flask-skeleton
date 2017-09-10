import os
import codecs

from template import Virtualenv, Bower, ProjectTemplate, FlaskProjectTemplate, template_env


# Environment variables
cwd = os.getcwd()


class Project():
    def __init__(self, appname="app", template=None):
        self.appname = appname
        if template is None:
            template = ProjectTemplate()
        self.template = template

        self.git = False

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

    def install(self):
        self.template.install(self)


class PythonProject(Project):
    def __init__(self, appname="app", template=None):
        Project.__init__(self, appname, template)
        self.virtualenv = False

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


class FlaskProject(PythonProject):
    def __init__(self, appname="app", template=None):
        if template is None:
            template = FlaskProjectTemplate()
        PythonProject.__init__(self, appname, template)

        self.secret_key = codecs.encode(os.urandom(32), 'hex').decode('utf-8')
        self.debug = True
        self.bower = []

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
            brief_var['bower_exe'] = Bower.cmd()
        if self.virtualenv:
            brief_var['virtualenv_exe'] = Virtualenv.cmd()
        return brief_var
