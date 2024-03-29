from interfaces import UIState

class PersistentUIState(UIState.Listener):
    '''Keeps track of a UI state
    UIState.Listener methods can be called directly to set the state without other listeners being notified'''

    def __init__(self, state: UIState) -> None:
        self._paused = False
        self._should_quit = False
        state.add_ui_state_listener(self)

    def paused(self) -> bool:
        return self._paused

    def should_quit(self) -> bool:
        return self._should_quit

    def pause_requested(self) -> None:
        '''Overrides a method in UIState.Listener'''
        self._paused = True

    def resume_requested(self) -> None:
        '''Overrides a method in UIState.Listener'''
        self._paused = False

    def quit_requested(self) -> None:
        '''Overrides a method in UIState.Listener'''
        self._should_quit = True
