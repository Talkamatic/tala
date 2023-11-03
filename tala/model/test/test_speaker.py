import unittest

from tala.model.speaker import Speaker


class speakerTests(unittest.TestCase):
    def test_speaker_class(self):
        self.assertEqual("SYS", Speaker.SYS)
        self.assertEqual("USR", Speaker.USR)
