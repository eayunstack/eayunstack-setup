import sys
import logging
from log import set_logger
import pkg_resources

LOG = logging.getLogger(__name__)

# save all config value user provides
user_conf = dict()


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
    LOG.info('Stage: Initializing\n')

    # first, ask user some question
    for c in cfgs:
        cfgs[c].ask_user(user_conf)

    # then, we output the result user set just
    LOG.info('Stage: Setup validation\n')
    for c in cfgs:
        cfgs[c].validation(user_conf)

    # last, run every configuration module to setup
    for c in cfgs:
        cfgs[c].run(user_conf)

if __name__ == '__main__':
    sys.exit(main())
