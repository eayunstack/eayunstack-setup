class ESCFG(object):
    def __init__(self, priority=1000, des=''):
        self.des = des

    def ask_user(self):
        pass

    def validation(self):
        pass

    def run(self):
        pass


def make_role(cfgs):
    cfgs[0] = ESCFG('setup role of this host')


def make_network(cfgs):
    cfgs[1] = ESCFG('setup network os this host')


def make_hostname(cfgs):
    cfgs[2] = ESCFG('setup hostname of this host')


def make_openstack(cfgs):
    cfgs[3] = ESCFG('config openstack component')
