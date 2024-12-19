from django.conf import settings
from django.core.management.base import BaseCommand


BASE_DIR = settings.BASE_DIR


class Command(BaseCommand):
    help = 'Remove all migrations'

    def handle(self, *args, **kwargs):
        import os
        import shutil

        for root, dirs, files in os.walk(BASE_DIR):
            if 'venv' in root:
                continue
            if 'migrations' in dirs:
                migrations_path = os.path.join(root, 'migrations')
                migrations_files = os.listdir(migrations_path)
                for file in migrations_files:
                    if file != '__init__.py':
                        file_path = os.path.join(migrations_path, file)
                        os.remove(file_path)
                        print(f'Removed {file_path}')

        print('Done!')
