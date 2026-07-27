import unittest
from jules_mcp.jules_mcp import _clean_session_id

class TestJulesMCP(unittest.TestCase):
    def test_clean_session_id(self):
        # Test with standard session_id
        self.assertEqual(_clean_session_id('12345'), '12345')

        # Test with resource name format
        self.assertEqual(_clean_session_id('sessions/12345'), '12345')

        # Test with empty string
        self.assertEqual(_clean_session_id(''), '')

        # Test with only slashes
        self.assertEqual(_clean_session_id('///'), '')

if __name__ == '__main__':
    unittest.main()
