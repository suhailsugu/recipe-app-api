"""
Test custom commands for the project
"""

from unittest.mock import patch
from psycopg2 import OperationalError as Psycopg2Error

from django.core.management import call_command
from django.test import SimpleTestCase
from django.db.utils import OperationalError


@patch('core.management.commands.wait_for_db.Command.check')
class TestCommand(SimpleTestCase):
    """Testing Commands"""
    def test_wait_for_db_ready(self, patched_check):
        """ Waiting for db ready"""

        patched_check.return_value= True
        call_command('wait_for_db')
        patched_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_wait_db_delay(self,patched_sleep,patched_check):
        """Testing Database Delay"""

        patched_check.side_effect = [Psycopg2Error] *2 + \
          [OperationalError] * 3 + [True]
        call_command('wait_for_db')
        self.assertEquals(patched_check.call_count,6)
        patched_check.assert_called_once_with(databases=['default'])
