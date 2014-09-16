import utils
import logging

LOG = logging.getLogger(__name__)


class ESCFG(object):
    def __init__(self, priority=1000, des=''):
        self.des = des

    def ask_user(self, user_conf):
        pass

    def validation(self, user_conf):
        pass

    def run(self, user_conf):
        pass


def make_role(cfgs):
    def ask_user(user_conf):
        LOG.info('Stage: role configure\n')
        utils.fmt_print('==== ROLER CONFIGURATE ====')
        while True:
            roler = raw_input(utils.fmt_msg('Which roler do you want to configurate this host as? (controller, network, computer) [controller]: '))
            if not roler:
                # default roler is controller
                roler = 'controller'
                break
            elif roler in ('controller', 'network', 'computer'):
                break
            else:
                utils.fmt_print('roler must be controller, network or computer')
        user_conf['roler'] = roler

    def validation(user_conf):
        utils.fmt_print('--== CONFIGURATION PREVIEW ==--')
        utils.valid_print('Roler', user_conf['roler'])

    ec = ESCFG('setup role of this host')
    ec.ask_user = ask_user
    ec.validation = validation
    # do not need run anything for roler config

    cfgs[0] = ec


def make_network(cfgs):
    cfgs[1] = ESCFG('setup network os this host')


def make_hostname(cfgs):
    cfgs[2] = ESCFG('setup hostname of this host')


def make_openstack(cfgs):
    cfgs[3] = ESCFG('config openstack component')
