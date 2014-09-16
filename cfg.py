import utils
import logging
import glob

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
        utils.valid_print('Roler', user_conf['roler'])

    ec = ESCFG('setup role of this host')
    ec.ask_user = ask_user
    ec.validation = validation
    # do not need run anything for roler config

    cfgs[0] = ec


def _ask_user(acceptable_value, default_value, prompt_msg, error_promtp_msg=None, check=None):
    """ ask user, then get a config value """
    while True:
        value = raw_input(utils.fmt_msg(prompt_msg))

        if value:
            # if value is not null and not acceptable, ignore
            if acceptable_value and value not in acceptable_value:
                if error_promtp_msg:
                    utils.fmt_print(error_promtp_msg)
                continue
        else:
            # if value is null and there is no default value, ignore
            if not default_value:
                if error_promtp_msg:
                    utils.fmt_print(error_promtp_msg)
                continue
            else:
                value = default_value
        # if it is running here, it indicate that we get a acceptable value
        if check and not check(value):
            LOG.warn('value is not valid, please input again')
            continue

        return value


def make_network(cfgs):
    def ask_user(user_conf):
        LOG.info('Stage: network configure')
        nics = sorted([i.split('/')[4] for i in
                       glob.glob('/sys/class/net/*/device')])
        LOG.info('Stage: there are %s nics on this host: %s\n', len(nics), nics)

        utils.fmt_print('==== NETWORK CONFIG FOR MANAGEMENT INTERFACE ====\n')
        # TODO check netmask, gateway
        mgt_txt = "which nic you want to be as manager interface: %s [%s]: " % (nics, nics[0])
        user_conf['mgt_nic'] = _ask_user(nics, nics[0], mgt_txt)
        user_conf['mgt_nic_ip'] = _ask_user(None, None, 'ip address: ', check=utils.check_ip)
        user_conf['mgt_nic_netmask'] = _ask_user(None, '255.255.255.0', 'netmask [255.255.255.0]: ')
        user_conf['mgt_nic_gw'] = _ask_user(None, None, 'gateway: ')

        utils.fmt_print('==== NETWORK CONFIG FOR TUNNEL INTERFACE ====\n')
        tun_txt = "which nic you want to be as tunnel interface: %s [%s]: " % (nics, nics[1])
        user_conf['tun_nic'] = _ask_user(nics, nics[1], tun_txt)
        user_conf['tun_nic_ip'] = _ask_user(None, None, 'ip address: ', check=utils.check_ip)
        user_conf['tun_nic_netmask'] = _ask_user(None, '255.255.255.0', 'netmask [255.255.255.0]: ')

        utils.fmt_print('==== NETWORK CONFIG FOR EXTERNAL INTERFACE ====\n')
        ext_txt = "which nic you want to be as external interface: %s [%s]: " % (nics, nics[2])
        user_conf['ext_nic'] = _ask_user(nics, nics[2], ext_txt)

    def validation(user_conf):
        utils.valid_print('Managerment network', user_conf['mgt_nic'])
        utils.valid_print('Tunnel network', user_conf['tun_nic'])
        utils.valid_print('External network', user_conf['ext_nic'])

    def run(user_conf):
        # TODO: mac address?
        CFG_FILE = '/etc/sysconfig/network-scripts/_ifcfg-%s'
        MGT_FMT = """# Created by es-setup
DEVICE=%s
IPADDR=%s
GATEWAY=%s
NETMASK=%s
ONBOOT=yes
"""
        with file(CFG_FILE % user_conf['mgt_nic'], 'w') as f:
            f.write(MGT_FMT % (
                user_conf['mgt_nic'],
                user_conf['mgt_nic_ip'],
                user_conf['mgt_nic_gw'],
                user_conf['mgt_nic_netmask']))

        TUN_FMT = """# Created by es-setup
DEVICE=%s
IPADDR=%s
NETMASK=%s
ONBOOT=yes
"""
        with file(CFG_FILE % user_conf['tun_nic'], 'w') as f:
            f.write(TUN_FMT % (
                user_conf['mgt_nic'],
                user_conf['mgt_nic_ip'],
                user_conf['mgt_nic_netmask']))

    ec = ESCFG('setup network of this host')
    ec.ask_user = ask_user
    ec.validation = validation
    ec.run = run
    cfgs[1] = ec


def make_hostname(cfgs):
    cfgs[2] = ESCFG('setup hostname of this host')


def make_openstack(cfgs):
    cfgs[3] = ESCFG('config openstack component')
