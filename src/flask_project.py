#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import codecs

from utils import query_yes_no
from template import FlaskProjectTemplate, template_env, generate_brief, generate_errorlist


# Environment variables
cwd = os.getcwd()


class FlaskProject():
    def __init__(self, appname="app", template=None):
        self.appname = appname
        if template is None:
            template = FlaskProjectTemplate()
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

    bower = None
    if args.bower:
        bower = args.bower.split(',')
    virtualenv = args.virtualenv
    debug = args.no_debug
    appname = args.appname
    database = args.database
    git = args.git

    if database:
        project_template = FlaskProjectTemplate(
            skeleton_dir='skel_db',
            config_file='config_db.jinja2',
        )
        project_template.database = True
    else:
        project_template = FlaskProjectTemplate()
    project = FlaskProject(appname, project_template)

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
