import utils
import logging
import glob
import getpass
import commands
import os
import shutil
from os.path import expanduser

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
        def _ask_mgt_nic(user_conf):
            txt = "which nic do you want to use as management " \
                  "interface: %s [%s]: " % (nics, nics[0])
            user_conf['mgt_nic'] = utils.ask_user(txt, nics, nics[0])
            txt = "Do you want this setup to configure the management " \
                  "network? (Yes, No) [Yes]: "
            confirm = utils.ask_user(txt, ('yes, no'), 'yes')
            if confirm.lower() == 'yes':
                user_conf['cfg_mgt'] = True
                utils.fmt_print("==== NETWORK CONFIGURATION FOR MANAGEMENT "
                                "INTERFACE ====")
                user_conf['mgt_nic_ip'] = utils.ask_user(
                    'ip address: ', check=utils.check_ip)
                user_conf['mgt_nic_netmask'] = utils.ask_user(
                    'netmask [255.255.255.0]: ', default_val='255.255.255.0',
                    check=_check_netmask(user_conf['mgt_nic_ip']))
                default_gw = utils.first_host_in_subnet(
                    user_conf['mgt_nic_ip'],
                    user_conf['mgt_nic_netmask'])
                user_conf['mgt_nic_gw'] = utils.ask_user(
                    'gateway [%s]: ' % default_gw, default_val=default_gw,
                    check=_check_gw(user_conf['mgt_nic_ip'],
                                    user_conf['mgt_nic_netmask']))

        def _ask_tun_nic(user_conf):
            txt = "which nic do you want to use as tunnel " \
                  "interface: %s [%s]: " % (nics, nics[1])
            user_conf['tun_nic'] = utils.ask_user(txt, nics, nics[1])
            txt = "Do you want this setup to configure the tunnel " \
                  "network? (Yes, No) [Yes]: "
            confirm = utils.ask_user(txt, ('yes, no'), 'yes')
            if confirm.lower() == 'yes':
                user_conf['cfg_tun'] = True
                utils.fmt_print("==== NETWORK CONFIGURATION FOR TUNNEL "
                                "INTERFACE ====")
                user_conf['tun_nic_ip'] = utils.ask_user(
                    'ip address: ', check=utils.check_ip)
                user_conf['tun_nic_netmask'] = utils.ask_user(
                    'netmask [255.255.255.0]: ', default_val='255.255.255.0',
                    check=_check_netmask(user_conf['tun_nic_ip']))

        def _ask_ext_nic(user_conf):
            # TODO: if there is only two nics in this host, the management
            # nic should be external nic, am i right?
            if len(nics) <= 2:
                dft_nic = nics[0]
            else:
                dft_nic = nics[2]
            txt = "which nic do you want to use as external " \
                  "interface: %s [%s]: " % (nics, dft_nic)
            user_conf['ext_nic'] = utils.ask_user(txt, nics, dft_nic)

        def _ask_ntp(user_conf):
            LOG.info('Stage: ntp server configuration\n')
            utils.fmt_print('==== NTP SERVER CONFIGURE ====')
            txt = 'Do you have some local ntp servers to use(yes, no) [yes]: '
            set_ntp = utils.ask_user(txt, ('yes, no'), 'yes')
            if set_ntp.lower() == 'yes':
                txt = 'Input the ntp server ip(seperated by ",", eg 10.10.1.1,10.10.1,2): '
                user_conf['ntp_server'] = utils.ask_user(txt, check=utils.check_ip)

        LOG.info('Stage: network configuration')
        nics = sorted([i.split('/')[4] for i in
                       glob.glob('/sys/class/net/*/device')])
        LOG.info('Stage: there are %s nics on this host: %s', len(nics), nics)
        _ask_mgt_nic(user_conf)
        _ask_tun_nic(user_conf)
        if user_conf['role'] in ('controller', 'network'):
            # only network node and controller node can config external nic
            _ask_ext_nic(user_conf)
        _ask_ntp(user_conf)

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

        if user_conf['role'] in ('controller', 'network'):
            utils.valid_print('External network', user_conf['ext_nic'])

        if 'ntp_server' in user_conf.keys():
            utils.valid_print('ntp server', user_conf['ntp_server'])

    def run(user_conf):
        def write_cfg(role):
            CFG_FILE = '/etc/sysconfig/network-scripts/ifcfg-%s'
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

        LOG.info('Checking NetworkManager service')
        (status, out) = commands.getstatusoutput(
            'systemctl is-active NetworkManager.service')
        if out == 'active':
            LOG.info('Stop NetworkManager service')
            commands.getstatusoutput('systemctl stop NetworkManager.service')

        (status, out) = commands.getstatusoutput(
            'systemctl is-enabled NetworkManager.service')
        if out == 'enabled':
            LOG.info('Disable NetworkManager service')
            commands.getstatusoutput('systemctl disable NetworkManager.service')

        LOG.info('Write network config file')
        if 'cfg_mgt' in user_conf.keys() and user_conf['cfg_mgt']:
            write_cfg('mgt')
        if 'cfg_tun' in user_conf.keys() and user_conf['cfg_tun']:
            write_cfg('tun')
        # enable network directly, do we need to check it first?
        LOG.info('Restart network service')
        commands.getstatusoutput('systemctl enable network.service')
        commands.getstatusoutput('systemctl restart network.service')

        if 'ntp_server' not in user_conf.keys():

            LOG.info('Checking ntpd service')
            (_, out) = commands.getstatusoutput(
                'systemctl is-active ntpd.service')
            if out != 'active':
                LOG.info('Starting ntpd service')
                commands.getstatusoutput('systemctl start ntpd.service')

            (_, out) = commands.getstatusoutput(
                'systemctl is-enabled ntpd.service')
            if out != 'enabled':
                LOG.info('Enabling ntpd service')
                commands.getstatusoutput('systemctl enable ntpd.service')

            # After ntpd server started, set ntp server to the controller node.
            user_conf['ntp_server'] = utils.get_ipaddr(user_conf['mgt_nic'])

    ec = ESCFG('setup network of this host')
    ec.ask_user = ask_user
    ec.validation = validation
    ec.run = run
    cfgs[1] = ec


def make_hostname(cfgs):
    HOSTFILE = '/etc/hostname'

    def ask_user(user_conf):
        LOG.info('Stage: hostname configuration\n')
        utils.fmt_print('==== HOSTNAME CONFIGURE ====')
        txt = 'Do you want to set the hostname(yes, no) [yes]: '
        set_host = utils.ask_user(txt, ('yes, no'), 'yes')
        if set_host.lower() == 'yes':
            txt = 'Input the FQDN hostname you want to use for this host: '
            user_conf['hostname'] = utils.ask_user(txt, check=utils.check_hostname)

    def validation(user_conf):
        if 'hostname' in user_conf.keys():
            utils.valid_print('hostname', user_conf['hostname'])

    def run(user_conf):
        if 'hostname' in user_conf.keys():
            open(HOSTFILE, 'w').write(user_conf['hostname'] + '\n')
        else:
            # Get hostname from /etc/hostname if user has set it manually.
            user_conf['hostname'] = open(HOSTFILE, 'r').read().strip()

    ec = ESCFG('setup hostname of this host')
    ec.ask_user = ask_user
    ec.validation = validation
    ec.run = run
    cfgs[2] = ec


def config_cinder(user_conf):
    CINDER_VOLUME_NAME = 'cinder-volumes'
    # whether we need to set CONFIG_CINDER_VOLUMES_CREATE yes or no
    user_conf['os_rdo_cinder'] = True
    cinder_vg_found = False
    (status, out) = commands.getstatusoutput('vgs')
    if status == 0:
        for i in out.split('\n'):
            if i.split()[0] == CINDER_VOLUME_NAME:
                user_conf['os_cinder'] = False
                cinder_vg_found = True
    if not cinder_vg_found:
        LOG.warn('No cinder volume group(%s) found' % CINDER_VOLUME_NAME)
        txt = 'Do you want to create cinder volume group now(yes, no) [yes]: '
        cfg_cinder = utils.ask_user(txt, ('yes, no'), 'yes')
        if cfg_cinder.lower() == 'yes':
            txt = 'Please input the name of the device you want to use for cinder: '
            cinder_dev = utils.ask_user(txt, check=lambda x: os.path.exists(x))
            user_conf['os_cinder_dev'] = cinder_dev
            user_conf['os_rdo_cinder'] = False
            # (status, out) = commands.getstatusoutput('pvcreate %s' % cinder_dev)
            # if status == 0:
            #     (status1, out1) = commands.getstatusoutput('vgcreate cinder-volumes %s' % cinder_dev)
            #     if status != 0:
            #         LOG.warn(out1)
            # else:
            #     LOG.warn(out)


def make_openstack(cfgs):
    def ask_user(user_conf):
        if user_conf['role'] != 'controller':
            # nothing shoule be done for other kinds of node for now
            return

        LOG.info('Stage: openstack configuration\n')
        utils.fmt_print('==== OPENSTACK CONFIGURE ====')
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

        compute_hosts_txt = "IP adresses of compute hosts(seperated by ',', eg '10.10.1.2,10.10.1.3'): "
        user_conf['compute_hosts'] = utils.ask_user(compute_hosts_txt, check=utils.check_ip_list)

        # cinder config
        config_cinder(user_conf)

    def validation(user_conf):
        if user_conf['role'] != 'controller':
            # nothing shoule be done for other kinds of node
            return

        if 'os_cinder_dev' in user_conf.keys():
            utils.valid_print('cinder device', user_conf['os_cinder_dev'])
        if 'compute_hosts' in user_conf.keys():
            utils.valid_print('compute hosts', user_conf['compute_hosts'])

    def cinder_create(user_conf):
        (status, out) = commands.getstatusoutput(
            'pvcreate %s' % user_conf['os_cinder_dev'])
        if status == 0:
            (status1, out1) = commands.getstatusoutput(
                'vgcreate cinder-volumes %s' % user_conf['os_cinder_dev'])
            if status1 != 0:
                LOG.warn(out1)
                raise RuntimeError('failed to create cinder VG using %s' %
                                   (user_conf['os_cinder_dev']))
        else:
            LOG.warn(out)
            raise RuntimeError('failed to create cinder PV using %s' %
                               (user_conf['os_cinder_dev']))

    def packstack(user_conf):
        ANSWER_FILE = '/tmp/eayunstack.answer'
        ANSWER_SAVE = os.path.join(expanduser("~"), '.es-setup.answer')
        # Generate answer file with packstack.
        (status, out) = commands.getstatusoutput('/usr/bin/packstack --gen-answer-file=%s' % ANSWER_FILE)
        if status != 0:
            LOG.warn(out)
            raise RuntimeError('Failed to generate answer file')
        if 'cfg_mgt' not in user_conf.keys():
            user_conf['mgt_nic_ip'] = utils.get_ipaddr(user_conf['mgt_nic'])

        # cinder config
        if user_conf['os_rdo_cinder']:
            rdo_cinder = 'y'
        else:
            cinder_create(user_conf)
            rdo_cinder = 'n'

        # All opitons needed to update are here.
        configs = {'config_swift_install': 'n',
                   'config_heat_install': 'y',
                   'config_controller_host': user_conf['mgt_nic_ip'],
                   'config_compute_hosts': user_conf['compute_hosts'],
                   'config_network_hosts': user_conf['mgt_nic_ip'],
                   'config_use_epel': 'n',
                   'config_amqp_host': user_conf['mgt_nic_ip'],
                   'config_mysql_host': user_conf['mgt_nic_ip'],
                   'config_cinder_volumes_create': rdo_cinder,
                   'config_neutron_ml2_type_drivers': 'gre',
                   'config_neutron_ml2_tenant_network_types': 'gre',
                   'config_neutron_ml2_tunnel_id_ranges': '1:1000',
                   'config_neutron_ovs_tenant_network_type': 'gre',
                   'config_neutron_ovs_bridge_ifaces': 'br-ex:%s' % user_conf['ext_nic'],
                   'config_neutron_ovs_tunnel_ranges': '1:1000',
                   'config_neutron_ovs_tunnel_if': user_conf['tun_nic'],
                   'config_provision_demo': 'n',
                   'config_mongodb_host': user_conf['mgt_nic_ip'],
                   'config_keystone_admin_pw': user_conf['os_pwd'],
                   'config_ntp_servers': user_conf['ntp_server']}
        for option in configs:
            # Update options
            (status, out) = commands.getstatusoutput('/usr/bin/openstack-config --set %s general %s %s'
                                                     % (ANSWER_FILE, option, configs[option]))
            if status != 0:
                LOG.warn(out)
                raise RuntimeError('Failed to update option %s in answer file' % option)
        # Save answer file
        shutil.copyfile(ANSWER_FILE, ANSWER_SAVE)
        # Invoke packstack, currently not hide the output from packstack.
        LOG.info('Starting openstack deployment')
        os.system('/usr/bin/packstack --answer-file=%s' % ANSWER_FILE)
        # (status, out) = commands.getstatusoutput('/usr/bin/packstack --answer-file=%s' % ANSWER_FILE)
        # if status != 0:
        #     LOG.warn(out)
        #     raise RuntimeError('Failed to deploy openstack')

    def run(user_conf):
        if user_conf['role'] == 'controller':
            packstack(user_conf)
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
