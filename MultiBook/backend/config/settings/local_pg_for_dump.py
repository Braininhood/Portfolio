"""
Use only for dumping data FROM a local PostgreSQL database.
Set LOCAL_DATABASE_URL in .env (e.g. postgresql://user:pass@localhost:5432/multibook_local).
Then: python manage.py dumpdata --settings=config.settings.local_pg_for_dump ...
"""
from .development import *  # noqa: F401, F403

import os
import re
from urllib.parse import unquote

local_url = os.environ.get('LOCAL_DATABASE_URL') or env('LOCAL_DATABASE_URL', default=None)
if not local_url or not local_url.startswith('postgresql://'):
    raise ValueError(
        'LOCAL_DATABASE_URL must be set and start with postgresql://. '
        'Example: postgresql://user:pass@localhost:5432/multibook_local'
    )

match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?\s]*)', local_url)
if match:
    db_name = match.group(5).split('?')[0]
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': match.group(1),
            'PASSWORD': unquote(match.group(2)),
            'HOST': match.group(3),
            'PORT': match.group(4),
            'OPTIONS': {'connect_timeout': 10},
        }
    }
else:
    raise ValueError('LOCAL_DATABASE_URL could not be parsed. Use postgresql://user:password@host:port/dbname')
