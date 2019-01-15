import unittest

from tala.model.speaker import Speaker


class speakerTests(unittest.TestCase):
    def testSpeakerClass(self):
        self.assertEquals("SYS", Speaker.SYS)
        self.assertEquals("USR", Speaker.USR)
