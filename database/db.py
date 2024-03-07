import os
from hyperdiv.sqlite import sqlite, migrate, sql



db = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "resound.db",
    )
)




