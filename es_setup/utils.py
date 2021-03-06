import logging
import socket
import fcntl
import struct
import string
import commands

LOG = logging.getLogger(__name__)

MOD37_BIT_POSITION = [32, 0, 1, 26, 2, 23, 27, 0, 3, 16,
                      24, 30, 28, 11, 0, 13, 4, 7, 17, 0,
                      25, 22, 31, 15, 29, 10, 12, 6, 0, 21,
                      14, 9, 5, 20, 8, 19, 18]


def fmt_print(msg):
    fmt = ' ' * 10
    print '%s%s' % (fmt, msg)


def fmt_msg(msg):
    fmt = ' ' * 10
    return '%s%s' % (fmt, msg)


def valid_print(key, value):
    fmt_print('%-40s: %s' % (key, value))


def ip_str_to_num(s):
    try:
        return struct.unpack(">l", socket.inet_pton(socket.AF_INET, s))[0]
    except socket.error:
        return 0


def is_netmask(n):
    """
    Bit hack from:
    http://graphics.stanford.edu/~seander/bithacks.html#ZerosOnRightModLookup.
    """
    nn = n >> MOD37_BIT_POSITION[(-n & n) % 37]
    return n < 0 and (nn & (nn + 1)) == 0


def is_ip(n):
    return n != 0 and not is_netmask(n)


def check_ip(value):
    return is_ip(ip_str_to_num(value))


def check_mask_with_ip(value, ip_str):
    ip, netmask = map(ip_str_to_num, [ip_str, value])
    if is_ip(ip) and is_netmask(netmask):
        return bool(ip & ~netmask)
    return False


def first_host_in_subnet(ip_str, netmask_str):
    ip, netmask = map(ip_str_to_num, [ip_str, netmask_str])
    if is_ip(ip) and is_netmask(netmask):
        f = (ip & netmask) + 1
        return socket.inet_ntop(socket.AF_INET, struct.pack(">l", f))
    return ''


def check_gw_with_ip_and_netmask(value, ip_str, netmask_str):
    ip, netmask, gw = map(ip_str_to_num, [ip_str, netmask_str, value])
    if is_ip(ip) and is_netmask(netmask) and is_ip(gw):
        same_subnet = (ip & netmask) == (gw & netmask)
        different_host = (ip & ~netmask) != (gw & ~netmask)
        return same_subnet and different_host
    return False


def check_hostname(hostname):
    allowed = set(string.ascii_letters + string.digits + '-')
    if not hostname or len(hostname) > 255:
        return False
    for label in hostname.split('.'):
        if len(label) > 63 or len(label) < 1:
            return False
        if not ((set(label) <= allowed)
           and not label.startswith('-')
           and not label.endswith('-')):
            return False
    return True


def check_ip_list(value):
    return reduce(lambda x, y: x and y, map(check_ip, value.split(',')))


def ask_user(prompt, accept_value=None, default_val=None, err_prompt=None,
             check=None):
    """ ask user, then get a config value, note: accept must be lower case """
    while True:
        value = raw_input(fmt_msg(prompt))

        if value:
            # if value is not null and not acceptable, ignore
            if accept_value and value.lower() not in accept_value:
                if err_prompt:
                    fmt_print(err_prompt)
                else:
                    fmt_print('you must input one of %s' % str(accept_value))
                continue
        else:
            # if value is null and there is no default value, ignore
            if not default_val:
                continue
            else:
                value = default_val
        # if it is running here, it indicate that we get a acceptable value
        if check and not check(value):
            if err_prompt:
                LOG.warn(err_prompt)
            else:
                LOG.warn('invalid input')
            continue

        return value


def get_hwaddr(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', ifname[:15]))
    return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]


def get_ipaddr(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(s.fileno(), 0x8915,
                           struct.pack('256s', ifname[:15]))[20:24]
    except IOError:
        return None
    return socket.inet_ntoa(info)


def service_operate(service, op):
    # service is an available service in systemctl
    # start&enable the service if start is True, else stop/disable it.
    if op == 'start':
        (_, out) = commands.getstatusoutput('systemctl is-active %s.service' % service)
        if out != 'active':
            commands.getstatusoutput('systemctl start %s.service' % service)
    elif op == 'stop':
        (_, out) = commands.getstatusoutput('systemctl is-active %s.service' % service)
        if out != 'inactive':
            commands.getstatusoutput('systemctl stop %s.service' % service)
    elif op == 'restart':
        commands.getstatusoutput('systemctl restart %s.service' % service)
    elif op == 'enable':
        (_, out) = commands.getstatusoutput('systemctl is-enabled %s.service' % service)
        if out != 'enabled':
            commands.getstatusoutput('systemctl enable %s.service' % service)
    elif op == 'disable':
        (_, out) = commands.getstatusoutput('systemctl is-enabled %s.service' % service)
        if out != 'disabled':
            commands.getstatusoutput('systemctl disable %s.service' % service)
