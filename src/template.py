import jinja2
import platform

import config

from utils import colors


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
