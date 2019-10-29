class ConnectionList:
    '''Simply a list of wl.Connections that supports adding listeners'''

    class Listener:
        '''Gets notified when connections are opened or closed'''

        def connection_opened(self, connection_list, connection):
            '''A new connection has been opened
            connection: wl.Connection
            '''
            raise NotImplementedError()

        def connection_closed(self, connection_list, connection):
            '''A connection has been closed
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
        catch_up: bool, if to send opened and closed events to catch the listener up to the current state
                  open connections will get a single connection_opened()
                  closed connections will get a connection_opened() followed by a connection_closed()
        '''
        raise NotImplementedError()

    def remove_connection_list_listener(self, listener):
        '''Remove the given listener so it no longer gets notifications
        listener: ConnectionList.Listener
        '''
        raise NotImplementedError()
