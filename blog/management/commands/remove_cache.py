from django.conf import settings
from django.core.management.base import BaseCommand


BASE_DIR = settings.BASE_DIR


class Command(BaseCommand):
    help = 'Remove __pycache__ directories'

    def handle(self, *args, **kwargs):
        import os
        import shutil

        for root, dirs, files in os.walk(BASE_DIR):
            if 'venv' in root:
                continue
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                shutil.rmtree(pycache_path)
                print(f'Removed __pycache__ in {pycache_path}')

        print('Done!') 
    