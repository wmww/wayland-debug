class Connection:
    '''A single Wayland client-server connection'''

    class Sink:
        '''Used to update connection state'''

        def message(self, message):
            '''Process a new wl.Message'''
            raise NotImplementedError()

        def close(self, time):
            '''Close the connection
            time: float, the time the connection was closed
            '''
            raise NotImplementedError()

    class Listener:
        '''Implement to be notified of connection state changes'''

        def connection_str_changed(self, connection):
            '''Called whenever str(connection) may return different output'''
            raise NotImplementedError()

        def connection_got_new_message(self, connection, message):
            '''Called when a new wl.Message has been processed'''
            raise NotImplementedError()

        def connection_closed(self, connection):
            '''Called only once when the connection is closed'''
            raise NotImplementedError()

    def messages(self):
        '''Returns a tuple of all messages in order they were processed'''
        raise NotImplementedError()

    def is_open(self):
        '''Returns if this connection is currently open'''
        raise NotImplementedError()

    def name(self):
        '''Returns the name the connection was created with'''
        raise NotImplementedError()

    def __str__(self):
        '''Describes connection'''
        raise NotImplementedError()

    def add_connection_listener(self, listener):
        '''Get notified of connection changes and messages'''
        raise NotImplementedError()

    def remove_connection_list_listener(self, listener):
        '''Stop the listener from being notified'''
        raise NotImplementedError()
