#!/usr/bin/env python
from twisted.internet import reactor, error, protocol, defer, threads
from twisted.protocols.basic import LineReceiver
from twisted.python import failure
import json
from log import start_log
import logging
logger = logging.getLogger()
import time


# STAGES
STAGE_INIT = 1
STAGE_AUTH = 2
STAGE_CON = 3
STAGE_COM = 4
STAGE_DONE = 5

connectionDone = failure.Failure(error.ConnectionDone())
connectionDone.cleanFailure()


class ESFactory(protocol.Factory):

    def __init__(self, ip, hostname):
        self.ip = ip
        self.hostname = hostname

    def buildProtocol(self, addr):
        p = ESProtocol(self)
        return p


class ESProtocol(LineReceiver):

    def __init__(self, factory):
        self.factory = factory
        self.stage = STAGE_INIT
        self.ip = self.factory.ip
        self.hostname = self.factory.hostname

    def connectionMade(self):
        if self.stage == STAGE_INIT:
            logger.debug('stage is %s' % self.stage)
            self.peer = self.transport.getPeer()
            logger.info(self.peer.host + 'connected')
            self.stage = STAGE_AUTH
        else:
            self.on_error('Wrong stage')

    def connectionLost(self, reason=connectionDone):
        logger.info('Connection lost to %s : %s' % (self.peer.host, reason.getErrorMessage()))
        self.clearLineBuffer()
        self.stage = STAGE_DONE

    def lineReceived(self, line):
        try:
            self.data = json.loads(line)
            logger.debug('stage is %s ' % self.stage)
            if self.stage == STAGE_AUTH:
                self.authorize()
                self.stage = STAGE_CON
            elif self.stage == STAGE_CON:
                self.stage = STAGE_COM
                self.add_compute()
            else:
                self.on_error('Wrong stage')
        except Exception, e:
            logger.error('Error : %s' + str(e))
            self.on_error('Internal Error: %s' % str(e))

    def send_controller_info(self):
        # TODO get pub key
        controller_info = {'ip': self.ip,
                           'hostname': self.hostname,
                           'pubkey': 'default'}
        self.sendLine(json.dumps(controller_info))

    def on_success(self):
        self.stage = STAGE_DONE
        msg = {'status': 0, 'msg': 'success'}
        self.sendLine(json.dumps(msg))
        self.transport.loseConnection()

    def on_error(self, reason):
        self.stage = STAGE_DONE
        msg = {'status': 1, 'msg': reason}
        self.sendLine(json.dumps(msg))
        self.transport.loseConnection()

    @defer.inlineCallbacks
    def authorize(self, pw=None):
        # TODO check password
        try:
            password = self.data['password']
            yield time.sleep(5)
            self.send_controller_info()
        except Exception, e:
            logging.error(e.message)
            self.on_error('Authorization Failed')

    @defer.inlineCallbacks
    def add_compute(self):
        try:
            # TODO do things about adding node, update /etc/hosts
            # TODO send logs to client
            compute_ip = self.data['ip']
            compute_name = self.data['hostname']
            compute_pubkey = self.data['pubkey']
            logger.info('Adding compute node %s' % compute_name)
            yield time.sleep(10)
            self.on_success()
        except Exception, e:
            logger.error(e.messge)
            self.on_error('Failed to add compute node %s ' % (compute_name + compute_ip))


if __name__ == '__main__':
    start_log('debug')
    esfactory = ESFactory(ip="127.0.0.1", hostname="localhost")
    reactor.listenTCP(9000, esfactory)
    reactor.run()
