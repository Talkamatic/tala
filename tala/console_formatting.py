HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


def header(string):
    return "%s%s%s" % (HEADER, string, ENDC)


def ok_blue(string):
    return "%s%s%s" % (OKBLUE, string, ENDC)


def ok_green(string):
    return "%s%s%s" % (OKGREEN, string, ENDC)


def warning(string):
    return "%s%s%s" % (WARNING, string, ENDC)


def fail(string):
    return "%s%s%s" % (FAIL, string, ENDC)


def bold(string):
    return "%s%s%s" % (BOLD, string, ENDC)


def underline(string):
    return "%s%s%s" % (UNDERLINE, string, ENDC)
