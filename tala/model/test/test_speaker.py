from tala.model.speaker import Speaker
from tala.testing import unittest as unittest


class speakerTests(unittest.TestCase):
    def testSpeakerClass(self):
        self.assertEquals("SYS", Speaker.SYS)
        self.assertEquals("USR", Speaker.USR)