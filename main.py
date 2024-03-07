import hyperdiv as hd
import os

from router import router

from dotenv import load_dotenv

# route won't be found unless file is read...
from index import home
from auth.auth_views import oauth_google_authorization

load_dotenv()

def main():
    
    router.run()


index_page = hd.index_page(
    title="Resound",
    description="Contribute to Resound Reaction Concerts",
    keywords=("resound", "reaction", "reaction concert"),
    favicon="/assets/resound_logo.svg",
)


if __name__ == "__main__":
    from database.migrations import migrate_db
    migrate_db()

    hd.run(main, index_page = index_page)
