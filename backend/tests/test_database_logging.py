import unittest
from unittest.mock import patch
from app.database import database

class DatabaseLoggingTests(unittest.TestCase):
    def test_connection_failure_does_not_log_driver_details(self):
        with self.assertLogs("app.database.database", level="ERROR") as captured:
            with patch.object(database.engine, "connect", side_effect=RuntimeError("credential detail")):
                self.assertFalse(database.check_database_connection())
        messages = [record.getMessage() for record in captured.records]
        self.assertEqual(["Database connectivity check failed during initialization"], messages)
        self.assertNotIn("credential detail", " ".join(messages))

if __name__ == "__main__":
    unittest.main()
