import sys
import logging
from log import set_logger
import pkg_resources

LOG = logging.getLogger(__name__)


def main():
    set_logger()
    cfgs = dict()
    entry_points = [
        (e.name, e.load()) for e in pkg_resources.iter_entry_points('cfg')
    ]
    for (name, fn) in entry_points:
        fn(cfgs)

    cfgs = dict(sorted(cfgs.iteritems(), key=lambda cfgs: cfgs[0]))  # sort

    # OK, we enter our core logic
    # first, ask user some question
    for c in cfgs:
        cfgs[c].ask_user()

    # then, we output the result user set just
    for c in cfgs:
        cfgs[c].validation()

    # last, run every configuration module to setup
    for c in cfgs:
        cfgs[c].run()

if __name__ == '__main__':
    sys.exit(main())
