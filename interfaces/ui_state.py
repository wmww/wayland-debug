from abc import abstractmethod

class UIState:
    class Listener:
        '''Notifies a backend about state changes requested by the UI'''

        def pause_requested(self) -> None:
            '''Processing messages should pause'''
            raise NotImplementedError()

        def resume_requested(self) -> None:
            '''Processing messages should resume'''
            raise NotImplementedError()

        def quit_requested(self) -> None:
            '''Program should quit'''
            raise NotImplementedError()

    def add_ui_state_listener(self, listener: Listener) -> None:
        '''Get notified about state changes'''
        raise NotImplementedError()

    def remove_ui_state_listener(self, listener: Listener) -> None:
        '''Stop being notified'''
        raise NotImplementedError()
