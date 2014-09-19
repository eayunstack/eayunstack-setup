import sys
import os
import logging
from log import set_logger
import pkg_resources
import utils
import excp
from os.path import expanduser

LOG = logging.getLogger(__name__)

# save all configuration values provided by user.
user_conf = dict()
user_conf_file = os.path.join(expanduser("~"), '.es-setup.cfg')


@excp.catches((KeyboardInterrupt, RuntimeError))
def main():
    set_logger()
    cfgs = dict()
    entry_points = [
        (e.name, e.load()) for e in pkg_resources.iter_entry_points(
            'es_setup.cfg')
    ]
    for (_, fn) in entry_points:
        fn(cfgs)

    cfgs = dict(sorted(cfgs.iteritems(), key=lambda cfgs: cfgs[0]))  # sort

    # OK, we enter our core logic
    LOG.info('Stage: Initializing\n')

    # first, ask user some question
    rebuild = 'no'
    if os.path.exists(user_conf_file):
        txt = "You have built eayunstack, do you want to reuse the same " \
              "configuration (yes, no) [no]: "
        rebuild = utils.ask_user(txt, ('yes, no'), 'no')
        if rebuild.lower() == 'yes':
            with file(user_conf_file, 'r') as f:
                s = f.read().strip('\n')
                user_conf.update((eval(s)))
    if rebuild.lower() == 'no':
        for c in cfgs:
            cfgs[c].ask_user(user_conf)
            # save for next using
        with file(user_conf_file, 'w') as f:
            f.write(str(user_conf))

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
