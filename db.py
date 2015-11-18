import logging
import os
from tornado_mysql import pools
from tornado_mysql.cursors import DictCursor
import tornadoredis

__author__ = 'qingfeng'

pools.DEBUG = False
POOL = pools.Pool(
    dict(host=os.getenv("DB_HOST", "localhost"), port=int(os.getenv("DB_PORT", "3306")),
         user=os.getenv("DB_USER", "root"), passwd=os.getenv("DB_PASS", "toor"),
         db=os.getenv("DB_NAME", "eleme"), cursorclass=DictCursor),
    max_idle_connections=2000,
    max_recycle_sec=3,
    max_open_connections=5000,
)
REDIS_CONNECTION_POOL = tornadoredis.ConnectionPool(max_connections=3000,
                                                    wait_for_available=True)
