import unittest

from tala.model import speaker


class speakerTests(unittest.TestCase):
    def test_speaker_class(self):
        self.assertEqual("SYS", speaker.SYS)
        self.assertEqual("USR", speaker.USR)
