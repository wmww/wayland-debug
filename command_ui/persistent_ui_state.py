from .ui_state import UIState

class PersistentUIState(UIState.Listener):
    '''Keeps track of a UI state
    UIState.Listener methods can be called directly to set the state without other listeners being notified'''

    def __init__(self, state):
        assert isinstance(state, UIState)
        self._paused = False
        self._should_quit = False
        state.add_ui_state_listener(self)

    def paused(self):
        return self._paused

    def should_quit(self):
        return self._should_quit

    def pause_requested(self):
        '''Overrides a method in UIState.Listener'''
        self._paused = True

    def resume_requested(self):
        '''Overrides a method in UIState.Listener'''
        self._paused = False

    def quit_requested(self):
        '''Overrides a method in UIState.Listener'''
        self._should_quit = True
