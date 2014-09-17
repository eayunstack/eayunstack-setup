#!/usr/bin/env python
from twisted.internet import reactor, error, protocol
from twisted.protocols.basic import LineReceiver
from twisted.python import failure
import json
from log import start_log
import logging
logger = logging.getLogger()


# STAGES
STAGE_INIT = 1
STAGE_AUTH = 2
STAGE_CON = 3
STAGE_COM = 4
STAGE_DONE = 5

connectionDone = failure.Failure(error.ConnectionDone())
connectionDone.cleanFailure()


class ESClient(LineReceiver):
    def __init__(self):
        self.stage = STAGE_INIT
        self.ip = None
        self.hostname = None
        self.server = "127.0.1.1"
        self.port = 9000

    def connectionMade(self):
        if self.stage == STAGE_INIT:
            self.peer = self.transport.getPeer()
            logger.info('Connected to %s' % self.peer.host)
            self.stage = STAGE_AUTH
            self.send_password()
        else:
            self.on_error('Wrong stage')

    def connectionLost(self, reason=connectionDone):
        logger.info('Connection lost to %s : %s' % (self.peer.host, reason.getErrorMessage()))
        self.clearLineBuffer()
        self.stage = STAGE_DONE
        reactor.stop()

    def lineReceived(self, data):
        try:
            self.data = json.loads(data)
            if self.stage == STAGE_AUTH:
                self.stage = STAGE_CON
                self.prepare_node()
                self.stage = STAGE_COM
                self.send_node_info()
            elif self.stage == STAGE_COM:
                if self.data['status'] == 0:
                    logger.info('Successfully Added %s' % self.hostname)
                    self.on_success()
            else:
                self.on_error('Wrong stage')
        except Exception, e:
            logger.error('Error: %s' % e.message)
            self.stage = STAGE_AUTH

    def send_node_info(self):
        node_info = {"ip": self.ip,
                     "hostname": self.hostname,
                     "pubkey": "default"}
        self.sendLine(json.dumps(node_info))

    def prepare_node(self):
        # TODO update /etc/hosts, update ssh key
        controller_ip = self.data['ip']
        controller_name = self.data['hostname']
        controller_pubkey = self.data['pubkey']
        logger.info('controller info: %s %s' % (controller_name, controller_ip))

    def send_password(self):
        pw = {'password': 'abc'}
        self.sendLine(json.dumps(pw))

    def on_error(self, reason):
        self.stage = STAGE_INIT
        self.transport.loseConnection()

    def on_success(self):
        self.stage = STAGE_DONE
        self.transport.loseConnection()


if __name__ == '__main__':
    addr = '127.0.0.1'
    port = 9000
    start_log('debug')
    protocol.ClientCreator(reactor, ESClient).connectTCP(addr, port)
    reactor.run()
