from django.core.management.base import BaseCommand
from psycopg2 import OperationalError as Psycopg2Error
import time
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for database."""   
    def handle(self, *args, **options):
        
        """Entry point for command"""
        
        self.stdout.write('Waiting for database...')
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True     
            except (Psycopg2Error,OperationalError):
                self.stdout.write("Database is not available, waiting for 1 second")
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Database is available!'))
        