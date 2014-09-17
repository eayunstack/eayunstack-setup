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
    # fuck code, need to be recreated
    def ask_user(user_conf):
        def _ask(roler):        # roler is one of mgt, tun, ext
            # TODO: less than 3 nics?
            if roler == 'mgt':
                name = 'managerment'
                index = 0
            elif roler == 'tun':
                name = 'tunnel'
                index = 1
            else:
                name = 'external'
                index = 2
            txt = "which nic you want to be as %s interface: %s [%s]: " % (name, nics, nics[index])
            user_conf[roler + '_nic'] = utils.ask_user(txt, nics, nics[index])
            if roler == 'ext':
                # we do not need to config this nic
                return
            txt = 'Do you want Setup to configure the %s network? (Yes, No) [Yes]: ' % (name)
            confirm = utils.ask_user(txt, ('yes, no'), 'yes')
            if confirm.lower() == 'yes':
                user_conf['cfg_' + roler] = True  # e.g. user_conf[cfg_mgt]
                utils.fmt_print('==== NETWORK CONFIG FOR %s INTERFACE ====' %
                                (name.upper()))
                # TODO check netmask, gateway
                user_conf[roler + '_nic_ip'] = utils.ask_user(
                    'ip address: ', check=utils.check_ip)
                user_conf[roler + '_nic_netmask'] = utils.ask_user(
                    'netmask [255.255.255.0]: ', default_val='255.255.255.0')
                if roler == 'mgt':
                    # hack: 192.168.3.157 --> 192.168.3.1
                    default_gw = '.'.join(
                        i for i in user_conf['mgt_nic_ip'].split('.')[0:3]) + \
                        '.1'
                    user_conf[roler + '_nic_gw'] = utils.ask_user(
                        'gateway [%s]: ' % default_gw, default_val=default_gw)

        LOG.info('Stage: network configure')
        nics = sorted([i.split('/')[4] for i in
                       glob.glob('/sys/class/net/*/device')])
        LOG.info('Stage: there are %s nics on this host: %s', len(nics), nics)
        for roler in ('mgt', 'tun', 'ext'):
            _ask(roler)

    def validation(user_conf):
        utils.valid_print('Managerment network', user_conf['mgt_nic'])
        if 'cfg_mgt' in user_conf.keys() and user_conf['cfg_mgt']:
            utils.valid_print('Managerment network IP address',
                              user_conf['mgt_nic_ip'])
            utils.valid_print('Managerment network netmask',
                              user_conf['mgt_nic_netmask'])
            utils.valid_print('Managerment network gateway',
                              user_conf['mgt_nic_gw'])

        utils.valid_print('Tunnel network', user_conf['tun_nic'])
        if 'cfg_tun' in user_conf.keys() and user_conf['cfg_tun']:
            utils.valid_print('Tunnel network IP addres',
                              user_conf['tun_nic_ip'])
            utils.valid_print('Tunnel network netmask',
                              user_conf['tun_nic_netmask'])

        utils.valid_print('External network', user_conf['ext_nic'])

    def run(user_conf):
        def write_cfg(roler):
            CFG_FILE = '/etc/sysconfig/network-scripts/_ifcfg-%s'
            CFG_FMT = """# Created by es-setup
DEVICE=%s
HWADDR=%s
IPADDR=%s
NETMASK=%s
ONBOOT=yes
"""
            CFG_VAL = [
                user_conf[roler + '_nic'],
                utils.get_hwaddr(user_conf[roler + '_nic']),
                user_conf[roler + '_nic_ip'],
                user_conf[roler + '_nic_netmask']]

            if roler == 'mgt':
                CFG_VAL.append(user_conf[roler + '_nic_gw'])
                CFG_FMT += "GATEWAY=%s\n"
            with file(CFG_FILE % user_conf[roler + '_nic'], 'w') as f:
                f.write(CFG_FMT % tuple(CFG_VAL))

        if 'cfg_mgt' in user_conf.keys() and user_conf['cfg_mgt']:
            write_cfg('mgt')
        if 'cfg_tun' in user_conf.keys() and user_conf['cfg_tun']:
            write_cfg('tun')

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
        txt = 'Do you want to config cinder VG (yes, no) [yes]: '
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
