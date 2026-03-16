"""
Use only for dumping data FROM the local SQLite database.
Run: python manage.py dumpdata --settings=config.settings.sqlite_for_dump ...
Then load into Supabase with: python manage.py loaddata ... --settings=config.settings.development
"""
from .development import *  # noqa: F401, F403

# Force SQLite so dumpdata reads from local db.sqlite3 (ignore DATABASE_URL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
