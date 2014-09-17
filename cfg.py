import utils
import logging
import glob
import getpass
import commands
import os

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
        txt = 'Which roler do you want to configurate this host as? (controller, network, computer) [controller]: '
        user_conf['roler'] = utils.ask_user(txt, ('controller', 'network', 'computer'), 'controller')

    def validation(user_conf):
        utils.valid_print('Roler', user_conf['roler'])

    ec = ESCFG('setup role of this host')
    ec.ask_user = ask_user
    ec.validation = validation
    # do not need run anything for roler config

    cfgs[0] = ec


def make_network(cfgs):
    def ask_user(user_conf):
        LOG.info('Stage: network configure')
        nics = sorted([i.split('/')[4] for i in
                       glob.glob('/sys/class/net/*/device')])
        LOG.info('Stage: there are %s nics on this host: %s', len(nics), nics)

        utils.fmt_print('\n==== NETWORK CONFIG FOR MANAGEMENT INTERFACE ====')
        # TODO check netmask, gateway
        mgt_txt = "which nic you want to be as manager interface: %s [%s]: " % (nics, nics[0])
        user_conf['mgt_nic'] = utils.ask_user(mgt_txt, nics, nics[0])
        user_conf['mgt_nic_ip'] = utils.ask_user('ip address: ', check=utils.check_ip)
        user_conf['mgt_nic_netmask'] = utils.ask_user('netmask [255.255.255.0]: ', default_val='255.255.255.0',)
        user_conf['mgt_nic_gw'] = utils.ask_user('gateway: ')

        utils.fmt_print('\n==== NETWORK CONFIG FOR TUNNEL INTERFACE ====')
        tun_txt = "which nic you want to be as tunnel interface: %s [%s]: " % (nics, nics[1])
        user_conf['tun_nic'] = utils.ask_user(tun_txt, nics, nics[1],)
        user_conf['tun_nic_ip'] = utils.ask_user('ip address: ', check=utils.check_ip)
        user_conf['tun_nic_netmask'] = utils.ask_user('netmask [255.255.255.0]: ', default_val='255.255.255.0')

        utils.fmt_print('\n==== NETWORK CONFIG FOR EXTERNAL INTERFACE ====')
        ext_txt = "which nic you want to be as external interface: %s [%s]: " % (nics, nics[2])
        user_conf['ext_nic'] = utils.ask_user(ext_txt, nics, nics[2])

    def validation(user_conf):
        utils.valid_print('Managerment network', user_conf['mgt_nic'])
        utils.valid_print('Managerment network IP address', user_conf['mgt_nic_ip'])
        utils.valid_print('Managerment network netmask', user_conf['mgt_nic_netmask'])
        utils.valid_print('Managerment network gateway', user_conf['mgt_nic_gw'])
        utils.valid_print('Tunnel network', user_conf['tun_nic'])
        utils.valid_print('Tunnel network IP addres', user_conf['tun_nic_ip'])
        utils.valid_print('Tunnel network netmask', user_conf['tun_nic_netmask'])
        utils.valid_print('External network', user_conf['ext_nic'])

    def run(user_conf):
        # TODO: mac address?
        CFG_FILE = '/etc/sysconfig/network-scripts/_ifcfg-%s'
        MGT_FMT = """# Created by es-setup
DEVICE=%s
HWADDR=%s
IPADDR=%s
GATEWAY=%s
NETMASK=%s
ONBOOT=yes
"""
        with file(CFG_FILE % user_conf['mgt_nic'], 'w') as f:
            f.write(MGT_FMT % (
                user_conf['mgt_nic'],
                utils.get_hwaddr(user_conf['mgt_nic']),
                user_conf['mgt_nic_ip'],
                user_conf['mgt_nic_gw'],
                user_conf['mgt_nic_netmask']))

        TUN_FMT = """# Created by es-setup
DEVICE=%s
HWADDR=%s
IPADDR=%s
NETMASK=%s
ONBOOT=yes
"""
        with file(CFG_FILE % user_conf['tun_nic'], 'w') as f:
            f.write(TUN_FMT % (
                user_conf['mgt_nic'],
                utils.get_hwaddr(user_conf['tun_nic']),
                user_conf['mgt_nic_ip'],
                user_conf['mgt_nic_netmask']))

    ec = ESCFG('setup network of this host')
    ec.ask_user = ask_user
    ec.validation = validation
    ec.run = run
    cfgs[1] = ec


def make_hostname(cfgs):
    cfgs[2] = ESCFG('setup hostname of this host')


def config_cinder(user_conf):
    cinder_vg_found = False
    (status, out) = commands.getstatusoutput('vgs')
    if status == 0:
        for i in out.split('\n'):
            if i.split()[0] == 'cinder-volumes':
                cinder_vg_found = True
    if not cinder_vg_found:
        LOG.warn('There is no cinder-volumes')
        txt = 'Do you want to config cinder VG (yes, no)[yes]: '
        cfg_cinder = utils.ask_user(txt, ('yes, no'), 'yes')
        if cfg_cinder.lower() == 'yes':
            txt = 'Please input device name you want to config as cinder device: '
            cinder_dev = utils.ask_user(txt, check=lambda x: os.path.exists(x))
            user_conf['os_cinder_dev'] = cinder_dev
            # (status, out) = commands.getstatusoutput('pvcreate %s' % cinder_dev)
            # if status == 0:
            #     (status1, out1) = commands.getstatusoutput('vgcreate cinder-volumes %s' % cinder_dev)
            #     if status != 0:
            #         LOG.warn(out1)
            # else:
            #     LOG.warn(out)


def make_openstack(cfgs):
    def ask_user(user_conf):
        LOG.info('Stage: openstack configure\n')
        utils.fmt_print('==== OPENSTACK CONFIGURATE ====')
        while True:
            # fmt_print('Confirm admin password:')
            txt = 'The password to use for the Keystone admin user: '
            pwd = getpass.getpass(utils.fmt_msg(txt))
            if not pwd:
                continue
            else:
                txt2 = 'Confirm admin password: '
                pwd2 = getpass.getpass(utils.fmt_msg(txt2))
                if pwd == pwd2:
                    user_conf['os_pwd'] = pwd
                    break
                else:
                    utils.fmt_print('Sorry, passwords do not match')

        # cinder config
        config_cinder(user_conf)

    def validation(user_conf):
        if 'os_cinder_dev' in user_conf.keys():
            utils.valid_print('cinder device', user_conf['os_cinder_dev'])

    ec = ESCFG('setup openstack of this host')
    ec.ask_user = ask_user
    ec.validation = validation
    cfgs[3] = ec
