import sys
import logging
from log import set_logger
import pkg_resources
import utils
import excp

LOG = logging.getLogger(__name__)

# save all config value user provides
user_conf = dict()


@excp.catches((KeyboardInterrupt, RuntimeError))
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
    utils.fmt_print('--== CONFIGURATION PREVIEW ==--')
    for c in cfgs:
        cfgs[c].validation(user_conf)

    txt = 'Please confirm installation settings (OK, Cancel) [OK]: '
    confirm = utils.ask_user(txt, ('ok, cancel'), 'ok')
    if confirm.lower() == 'cancel':
        sys.exit()

    # last, run every configuration module to setup
    LOG.info('Stage: Transaction setup')
    for c in cfgs:
        cfgs[c].run(user_conf)

if __name__ == '__main__':
    sys.exit(main())
