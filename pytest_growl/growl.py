import socket
import struct
from cStringIO import StringIO
from hashlib import md5
_GROWL_UDP_PORT = 9887
_DEFAULT_TITLE = "Test Complete"
APPLICATION_NAME = "pytest"
_GROWL_VERSION = 1
_PACKET_TYPE_REGISTRATION = 0
_PACKET_TYPE_NOTIFICATION = 1
_GROWL_PRIORITIES = {0: 0, 1: 1, 2: 2, -2: 3, -1: 4}


def pytest_addoption(parser):
    """Adds options to control growl notifications."""
    group = parser.getgroup('terminal reporting')
    group.addoption('--growl',
                    dest='growl',
                    default=True,
                    help='Enable Growl notifications.')


def pytest_terminal_summary(terminalreporter):
    if terminalreporter.config.option.growl:
        tr = terminalreporter
        try:
            passes = len(tr.stats['passed'])
        except KeyError:
            passes = 0
        try:
            fails = len(tr.stats['failed'])
        except KeyError:
            fails = 0
        if passes & fails == 0:
            message_to_send = "No tests were ran."
            send_growl(message=message_to_send, title="Alert:")
        else:
            message_to_send = "Passed: %s Failed: %s" % (passes, fails)
            send_growl(message=message_to_send)


class SignedStructStream(object):
    def __init__(self):
        super(SignedStructStream, self).__init__()
        self._stream = StringIO()
        self._hash = md5()
    
    def writeBuffer(self, buff, sign=True):
        if sign:
            self._hash.update(buff)
        self._stream.write(buff)
    
    def sign(self):
        self.writeBuffer(self._hash.digest(), sign=False)
    
    def write(self, format, *data):
        packed = struct.pack(format, *data)
        self.writeBuffer(packed)
    
    def getvalue(self):
        return self._stream.getvalue()
    
    def gethash(self):
        return self._hash.digest()
    

def build_registration_packet(application_name, notifications):
    returned = SignedStructStream()
    returned.write("b", _GROWL_VERSION)
    returned.write("b", _PACKET_TYPE_REGISTRATION)
    returned.write("!H", len(application_name))
    returned.write("bb", len(notifications), len(notifications))
    returned.writeBuffer(application_name.encode('utf-8'))
    for notification in notifications:
        returned.write("!H", len(notification))
        returned.writeBuffer(notification.encode('utf-8'))
    for i in xrange(len(notifications)):
        returned.write("b", i)
    returned.sign()
    return returned.getvalue()


def build_notification_packet(application_name, notification_name, title, message, priority, sticky):
    flags = ((_GROWL_PRIORITIES.get(priority, 0) & 007) * 2)
    if sticky:
        flags |= 1
    returned = SignedStructStream()
    returned.write("!BBHHHHH",
                   _GROWL_VERSION,
                   _PACKET_TYPE_NOTIFICATION,
                   flags,
                   len(notification_name),
                   len(title),
                   len(message),
                   len(application_name),
                   )
    for x in (notification_name, title, message, application_name):
        returned.writeBuffer(x.encode('utf-8'))
    returned.sign()
    return returned.getvalue()


def send_growl(host="127.0.0.1", message='',
          title=_DEFAULT_TITLE,
          port=_GROWL_UDP_PORT,
          sticky=False,
          priority=1,
          notification='Notification',
          application=APPLICATION_NAME,
          _socket=socket.socket,
          _build_notification_packet=build_notification_packet,
          _build_registration_packet=build_registration_packet,
          ):
    s = _socket(socket.AF_INET, socket.SOCK_DGRAM)
    reg_packet = _build_registration_packet(application_name=application, notifications=[notification])
    s.sendto(reg_packet, (host, port))
    notification = _build_notification_packet(
        priority=priority,
        message=message,
        title=title,
        notification_name=notification,
        application_name=application,
        sticky=sticky)
    s.sendto(notification, (host, port))
    s.close()
