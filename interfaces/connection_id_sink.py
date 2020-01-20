class ConnectionIDSink:
    '''Receives messages and connection created/deleted events based on a unique connection ID'''

    def open_connection(self, time, connection_id, is_server):
        '''Open a new client-server connection
        time: float, what is returned by time.perf_counter() will do
        connection_id: str, unique identifier of the connection (only used internally, never shown to user)
        is_server: bool/None, if this connection is a server or a client (can be None if value is unknown)
        returns: wl.Connection, the newly created connection
        '''
        # TODO: make return None
        raise NotImplementedError()

    def close_connection(self, time, connection_id):
        '''Close the given connection
        time: float, what is returned by time.perf_counter() will do
        connection_id: str, the unique ID the connection was created with
        '''
        raise NotImplementedError()

    def message(self, connection_id, message):
        '''Process a new message
        connection_id: str, the unique ID of the connection this message was on
        message: wl.Message, the message
        '''
        raise NotImplementedError()
