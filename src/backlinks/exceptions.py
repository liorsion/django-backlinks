from xmlrpclib import Fault

# Server-side exceptions

class BacklinkServerError(Fault): # Does this need to be a Fault subclass?
    code = 0x0000
    message = 'Unknown error'
    def __init__(self, message=None, *args, **kwargs):
        self.message = message or self.message
        Fault.__init__(self, self.code, self.message)

class BacklinkSourceDoesNotExist(BacklinkServerError):
    code = 0x0010
    message = 'Source does not exist'

class BacklinkSourceDoesNotLink(BacklinkServerError):
    code = 0x0011
    message = 'Source does not link'

class BacklinkTargetDoesNotExist(BacklinkServerError):
    code = 0x0020
    message = 'Target does not exist'

class BacklinkTargetNotPingable(BacklinkServerError):
    code = 0x0021
    message = 'Target is not pingable'

class BacklinkAlreadyRegistered(BacklinkServerError):
    code = 0x0030
    message = 'Ping to target from given source already registered'

class BacklinkAccessDenied(BacklinkServerError):
    code = 0x0031
    message = 'Access denied'

class BacklinkConnectionError(BacklinkServerError):
    code = 0x0032
    message = 'A connection error has occurred'


# Client-side exceptions

class BacklinkClientError(Exception):
    code = 0x0000
    message = 'An unknown error has occurred'
    reason = ''
    def __init__(self, message='', reason=''):
        self.message = message or self.message
        self.reason = reason or self.reason

class BacklinkClientSourceDoesNotExist(BacklinkClientError):
    code = 0x0010
    message = 'Source does not exist'

class BacklinkClientSourceDoesNotLink(BacklinkClientError):
    code = 0x0011
    message = 'Source does not link'

class BacklinkClientTargetDoesNotExist(BacklinkClientError):
    code = 0x0020
    message = 'Target does not exist'

class BacklinkClientTargetNotPingable(BacklinkClientError):
    code = 0x0021
    message = 'Target not pingable'

class BacklinkClientAlreadyRegistered(BacklinkClientError):
    code = 0x0030
    message = 'Ping from given source to given target already registered'

class BacklinkClientAccessDenied(BacklinkClientError):
    code = 0x0031
    message = 'Access denied'

class BacklinkClientServerConnectionError(BacklinkClientError):
    code = 0x0032
    message = 'Server encountered a connection error'

class BacklinkClientServerDoesNotExist(BacklinkClientError):
    code = 0x0100
    message = 'The given server resource does not exist'

class BacklinkClientRemoteError(BacklinkClientError):
    code = 0x0101
    message = 'An error occurred on the remote server'
    
class BacklinkClientInvalidResponse(BacklinkClientError):
    code = 0x0111
    message = 'The received response was invalid'

class BacklinkClientConnectionError(BacklinkClientError):
    code = 0x0132
    message = 'Error connecting to server'
    
fault_code_to_client_error = {
    0x0000: BacklinkClientError,
    0x0010: BacklinkClientSourceDoesNotExist,
    0x0011: BacklinkClientSourceDoesNotLink,
    0x0020: BacklinkClientTargetDoesNotExist,
    0x0021: BacklinkClientTargetNotPingable,
    0x0030: BacklinkClientAlreadyRegistered,
    0x0031: BacklinkClientAccessDenied,
    0x0032: BacklinkClientServerConnectionError,
    0x0100: BacklinkClientServerDoesNotExist,
    0x0101: BacklinkClientRemoteError,
    0x0111: BacklinkClientInvalidResponse,
    0x0132: BacklinkClientConnectionError,
}
