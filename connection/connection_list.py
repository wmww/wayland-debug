class ConnectionList:
    '''Simply a list of wl.Connections that supports adding listeners'''

    class Listener:
        '''Gets notified when connections are opened
        To be notified when connections are closed, register a connection listener
        '''

        def connection_opened(self, connection_list, connection):
            '''A new connection has been opened
            connection: wl.Connection
            '''
            raise NotImplementedError()

    def connections(self):
        '''Get all connections (open and closed) in order they were created
        returns: tuple of wl.Connection
        '''
        raise NotImplementedError()

    def add_connection_list_listener(self, listener, catch_up):
        '''Add a listener to be notified of opened and closed connections
        listener: ConnectionList.Listener
        catch_up: bool, if to send connection_opened() events for all open and closed connections
        '''
        raise NotImplementedError()

    def remove_connection_list_listener(self, listener):
        '''Remove the given listener so it no longer gets notifications
        listener: ConnectionList.Listener
        '''
        raise NotImplementedError()
