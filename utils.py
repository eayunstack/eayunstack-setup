def fmt_print(msg):
    fmt = ' ' * 10
    print '%s%s' % (fmt, msg)


def fmt_msg(msg):
    fmt = ' ' * 10
    return '%s%s' % (fmt, msg)


def valid_print(key, value):
    fmt_print('%-40s:%s' % (key, value))


def check_ip(value):
    try:
        if len(value.split('.')) != 4:
            return False
        for i in value.split('.'):
            if int(i) < 0 or int(i) > 255:
                return False
    except:
        return False
    return True
