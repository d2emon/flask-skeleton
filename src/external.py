import sys
import shutil
import subprocess


from utils import colors


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


def run(params, logfile, msg, exit_on_error=True):
    output, error = subprocess.Popen(
        params,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ).communicate()
    log_error(
        logfile,
        error,
        msg,
        exit_on_error
    )


class External():
    _util = None
    errors = []
    cmd_name = ""
    error_msg = ""

    @classmethod
    def cmd(cls):
        if cls._util is None:
            cls._util = shutil.which(cls.cmd_name)
        if not cls._util:
            cls.errors.append(cls.error_msg)
        return cls._util


class Bower(External):
    cmd_name = "bower"
    error_msg = 'Bower executable could not be found.'


class Virtualenv(External):
    cmd_name = "virtualenv"
    error_msg = 'Virtualenv executable could not be found.'


class Git(External):
    _util = "git"
    cmd_name = "git"
