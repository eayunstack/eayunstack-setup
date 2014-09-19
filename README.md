EayunStack-Setup
===============

An automated deployment tool for openstack.

####Support Platforms:
CentOS 7

####Feature Description:
Support one controller and multi-computer deployment;
Interacting with user to prepare all openstack nodes' env;
Once prepared, the whole deployment process doesn't need human intervention.
Besides keystone, nova and glance, cinder, neutron, heat, ceilometer are all supported.

####Howto:

** On every openstack node **

    $git clone https://github.com/eayunstack/eayunstack-setup.git
    $cd eayunstack-setup
    $python setup.py install
    $es-setup
** answer all questions asked, then it's done **

####Procedure Review:


    [ INFO  ] Stage: Initializing

            You have built eayunstack, do you want to reuse the same configuration (yes, no) [no]: no
    [ INFO  ] Stage: role configuration

            ==== ROLE CONFIGURE ====
            Which role do you want to configure this host as? (controller, network, computer) [controller]: 
    [ INFO  ] Stage: network configuration
    [ INFO  ] Stage: there are 3 nics on this host: ['eth0', 'eth1', 'eth2']
            which nic do you want to use as management interface: ['eth0', 'eth1', 'eth2'] [eth0]: 
            Do you want this setup to configure the management network? (Yes, No) [Yes]: no
            which nic do you want to use as tunnel interface: ['eth0', 'eth1', 'eth2'] [eth1]: 
            Do you want this setup to configure the tunnel network? (Yes, No) [Yes]: no
            which nic do you want to use as external interface: ['eth0', 'eth1', 'eth2'] [eth2]: 
    [ INFO  ] Stage: ntp server configuration

            ==== NTP SERVER CONFIGURE ====
            Do you have some local ntp servers to use(yes, no) [yes]: no
    [ INFO  ] Stage: hostname configuration

            ==== HOSTNAME CONFIGURE ====
            Do you want to set the hostname(yes, no) [yes]: no
    [ INFO  ] Stage: openstack configuration

            ==== OPENSTACK CONFIGURE ====
            The password to use for keystone admin user: 
            Confirm admin password: 
            IP adresses of compute hosts(seperated by ',', eg '10.10.1.2,10.10.1.3'): 10.10.1.200
    [ WARNIN] No cinder volume group(cinder-volumes) found
            Do you want to create cinder volume group now(yes, no) [yes]: 
            Please input the name of the device you want to use for cinder: /dev/sdb
    [ INFO  ] Stage: Setup validation

            --== CONFIGURATION PREVIEW ==--
            Role                                    : controller
            Management network                      : eth0
            Tunnel network                          : eth1
            External network                        : eth2
            cinder device                           : /dev/sdb
            compute hosts                           : 10.10.1.200
            Please confirm installation settings (OK, Cancel) [OK]: 
    [ INFO  ] Stage: Transaction setup
    [ INFO  ] Disabling NetworkManager service
    [ INFO  ] Write network config file
    [ INFO  ] Restart network service
    [ INFO  ] Starting openstack deployment
    Welcome to Installer setup utility
