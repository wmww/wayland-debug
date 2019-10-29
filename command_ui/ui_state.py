class UIState:
    class Listener:
        '''Notifies a backend about state changes requested by the UI'''

        def pause_requested(self):
            '''Processing messages should pause'''
            raise NotImplementedError()

        def resume_requested(self):
            '''Processing messages should resume'''
            raise NotImplementedError()

        def quit_requested(self):
            '''Program should quit'''
            raise NotImplementedError()

    def add_ui_state_listener(self, listener):
        '''Get notified about state changes'''
        raise NotImplementedError()

    def remove_ui_state_listener(self, listener):
        '''Stop being notified'''
        raise NotImplementedError()
