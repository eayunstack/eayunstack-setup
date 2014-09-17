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
        LOG.info('Stage: role configuration\n')
        utils.fmt_print('==== ROLE CONFIGURE ====')
        txt = 'Which role do you want to configure this host as? (controller, network, computer) [controller]: '
        user_conf['role'] = utils.ask_user(txt, ('controller', 'network', 'computer'), 'controller')

    def validation(user_conf):
        utils.valid_print('Role', user_conf['role'])

    ec = ESCFG('setup role of this host')
    ec.ask_user = ask_user
    ec.validation = validation
    # do not need run anything for role config

    cfgs[0] = ec


def make_network(cfgs):
    def _check_netmask(ip):
        f = lambda netmask: utils.check_mask_with_ip(netmask, ip)
        return f

    def _check_gw(ip, netmask):
        f = lambda gw: utils.check_gw_with_ip_and_netmask(gw, ip, netmask)
        return f

    # fuck code, need to be recreated
    def ask_user(user_conf):
        def _ask(role):        # role is one of mgt, tun, ext
            # TODO: less than 3 nics?
            if role == 'mgt':
                name = 'management'
                index = 0
            elif role == 'tun':
                name = 'tunnel'
                index = 1
            else:
                name = 'external'
                index = 2
            txt = "which nic do you want to use as %s interface: %s [%s]: " % (name, nics, nics[index])
            user_conf[role + '_nic'] = utils.ask_user(txt, nics, nics[index])
            if role == 'ext':
                # we do not need to config this nic
                return
            txt = 'Do you want this setup to configure the %s network? (Yes, No) [Yes]: ' % (name)
            confirm = utils.ask_user(txt, ('yes, no'), 'yes')
            if confirm.lower() == 'yes':
                user_conf['cfg_' + role] = True  # e.g. user_conf[cfg_mgt]
                utils.fmt_print('==== NETWORK CONFIGURATION FOR %s INTERFACE ====' %
                                (name.upper()))
                # TODO check netmask, gateway
                user_conf[role + '_nic_ip'] = utils.ask_user(
                    'ip address: ', check=utils.check_ip)
                user_conf[role + '_nic_netmask'] = utils.ask_user(
                    'netmask [255.255.255.0]: ', default_val='255.255.255.0',
                    check=_check_netmask(user_conf[role + '_nic_ip']))
                if role == 'mgt':
                    default_gw = utils.first_host_in_subnet(
                        user_conf[role + '_nic_ip'],
                        user_conf[role + '_nic_netmask']
                    )
                    user_conf[role + '_nic_gw'] = utils.ask_user(
                        'gateway [%s]: ' % default_gw, default_val=default_gw,
                        check=_check_gw(user_conf[role + '_nic_ip'],
                                        user_conf[role + '_nic_netmask']))

        LOG.info('Stage: network configuration')
        nics = sorted([i.split('/')[4] for i in
                       glob.glob('/sys/class/net/*/device')])
        LOG.info('Stage: there are %s nics on this host: %s', len(nics), nics)
        for role in ('mgt', 'tun', 'ext'):
            _ask(role)

    def validation(user_conf):
        utils.valid_print('Management network', user_conf['mgt_nic'])
        if 'cfg_mgt' in user_conf.keys() and user_conf['cfg_mgt']:
            utils.valid_print('Management network IP address',
                              user_conf['mgt_nic_ip'])
            utils.valid_print('Management network netmask',
                              user_conf['mgt_nic_netmask'])
            utils.valid_print('Management network gateway',
                              user_conf['mgt_nic_gw'])

        utils.valid_print('Tunnel network', user_conf['tun_nic'])
        if 'cfg_tun' in user_conf.keys() and user_conf['cfg_tun']:
            utils.valid_print('Tunnel network IP addres',
                              user_conf['tun_nic_ip'])
            utils.valid_print('Tunnel network netmask',
                              user_conf['tun_nic_netmask'])

        utils.valid_print('External network', user_conf['ext_nic'])

    def run(user_conf):
        def write_cfg(role):
            CFG_FILE = '/etc/sysconfig/network-scripts/_ifcfg-%s'
            CFG_FMT = """# Created by es-setup
DEVICE=%s
HWADDR=%s
IPADDR=%s
NETMASK=%s
ONBOOT=yes
"""
            CFG_VAL = [
                user_conf[role + '_nic'],
                utils.get_hwaddr(user_conf[role + '_nic']),
                user_conf[role + '_nic_ip'],
                user_conf[role + '_nic_netmask']]

            if role == 'mgt':
                CFG_VAL.append(user_conf[role + '_nic_gw'])
                CFG_FMT += "GATEWAY=%s\n"
            with file(CFG_FILE % user_conf[role + '_nic'], 'w') as f:
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
    CINDER_VOLUME_NAME = 'cinder-volumes'
    cinder_vg_found = False
    (status, out) = commands.getstatusoutput('vgs')
    if status == 0:
        for i in out.split('\n'):
            if i.split()[0] == CINDER_VOLUME_NAME:
                cinder_vg_found = True
    if not cinder_vg_found:
        LOG.warn('No cinder volume group(%s) found' % CINDER_VOLUME_NAME)
        txt = 'Do you want to create cinder volume group now(yes, no) [yes]: '
        cfg_cinder = utils.ask_user(txt, ('yes, no'), 'yes')
        if cfg_cinder.lower() == 'yes':
            txt = 'Please input the name of the device you want to use for cinder:'
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
        LOG.info('Stage: openstack configuration\n')
        utils.fmt_print('==== OPENSTACK CONFIGURATE ====')
        while True:
            # fmt_print('Confirm admin password:')
            txt = 'The password to use for keystone admin user: '
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

        compute_hosts_txt = "IP adresses of compute hosts(separated by ',', eg '10.10.1.2,10.10.1.3'): "
        user_conf['compute_hosts'] = utils.ask_user(compute_hosts_txt, check=utils.check_ip_list)

        # cinder config
        config_cinder(user_conf)

    def validation(user_conf):
        if 'os_cinder_dev' in user_conf.keys():
            utils.valid_print('cinder device', user_conf['os_cinder_dev'])
        if 'compute_hosts' in user_conf.keys():
            utils.valid_print('compute hosts', user_conf['compute_hosts'])

    def run(user_conf):
        if user_conf['role'] == 'controller':
            ANSWER_FILE = '/tmp/eayunstack.answer'
            # Generate answer file with packstack.
            os.system('/usr/bin/packstack --gen-answer-file=%s' % ANSWER_FILE)
            # All opitons needed to update are here.
            configs = {'config_swift_install': 'n',
                       'config_controller_host': user_conf['mgt_nic_ip'],
                       'config_compute_hosts': user_conf['compute_hosts'],
                       'config_network_hosts': user_conf['mgt_nic_ip'],
                       'config_use_epel': 'n',
                       'config_amqp_host': user_conf['mgt_nic_ip'],
                       'config_mysql_host': user_conf['mgt_nic_ip'],
                       'config_cinder_volumes_create': 'n',
                       'config_neutron_ml2_type_drivers': 'gre',
                       'config_neutron_ml2_tenant_network_types': 'gre',
                       'config_neutron_ml2_tunnel_id_ranges': '1:1000',
                       'config_neutron_ovs_tenant_network_type': 'gre',
                       'config_neutron_ovs_bridge_ifaces': 'br-ex:%s' % user_conf['ext_nic'],
                       'config_neutron_ovs_tunnel_ranges': '1:1000',
                       'config_neutron_ovs_tunnel_if': user_conf['tun_nic'],
                       'config_provision_demo': 'n',
                       'config_mongodb_host': user_conf['mgt_nic_ip'],
                       'config_keystone_admin_pw': user_conf['os_pwd']}
            for option in configs:
                # Update options
                os.system('/usr/bin/openstack-config --set %s general %s %s' % (ANSWER_FILE, option, configs[option]))
            # Save answer file
            os.system('/usr/bin/cp %s %s' % (ANSWER_FILE, '~/.eayunstack.answer'))
            # Invoke packstack
            # os.system('/usr/bin/packstack --answer-file=%s' % ANSWER_FILE)
        elif user_conf['role'] == 'compute':
            # Don't handle compute roles at present.
            pass
        else:
            # Don't handle other roles at present.
            pass

    ec = ESCFG('setup openstack of this host')
    ec.ask_user = ask_user
    ec.validation = validation
    ec.run = run
    cfgs[3] = ec
