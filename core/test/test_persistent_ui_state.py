from unittest import TestCase, mock
import interfaces
from core import PersistentUIState

class TestPersistentUIState(TestCase):
    def test_starts_out_correctly(self):
        state = mock.Mock(spec=interfaces.UIState)
        ps = PersistentUIState(state)
        self.assertEqual(ps.paused(), False)
        self.assertEqual(ps.should_quit(), False)

    def test_adds_listener(self):
        state = mock.Mock(spec=interfaces.UIState)
        ps = PersistentUIState(state)
        state.add_ui_state_listener.assert_called_once_with(ps)
        state.remove_ui_state_listener.assert_not_called()

    def test_can_be_paused(self):
        state = mock.Mock(spec=interfaces.UIState)
        ps = PersistentUIState(state)
        self.assertEqual(ps.paused(), False)
        ps.pause_requested()
        self.assertEqual(ps.paused(), True)
        self.assertEqual(ps.should_quit(), False)

    def test_can_be_resumed(self):
        state = mock.Mock(spec=interfaces.UIState)
        ps = PersistentUIState(state)
        ps.pause_requested()
        self.assertEqual(ps.paused(), True)
        ps.resume_requested()
        self.assertEqual(ps.paused(), False)
        self.assertEqual(ps.should_quit(), False)

    def test_can_quit(self):
        state = mock.Mock(spec=interfaces.UIState)
        ps = PersistentUIState(state)
        self.assertEqual(ps.should_quit(), False)
        ps.quit_requested()
        self.assertEqual(ps.should_quit(), True)
