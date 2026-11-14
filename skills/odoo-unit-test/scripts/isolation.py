"""Process-local network/database tripwire. Not a security sandbox."""
import importlib.abc
import socket
import sys

DRIVERS = {'psycopg2', 'psycopg', 'pg8000', 'asyncpg'}
class BlockDrivers(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in DRIVERS: raise ImportError('Database driver blocked: ' + fullname)
        return None

def denied(*args, **kwargs): raise RuntimeError('Network connection blocked by isolation guard')

def install():
    if any(name.split('.')[0] in DRIVERS for name in sys.modules):
        raise RuntimeError('Database driver already imported before isolation guard')
    sys.meta_path.insert(0, BlockDrivers())
    socket.socket.connect = denied
    socket.socket.connect_ex = denied
    socket.create_connection = denied

def self_check():
    try: __import__('psycopg2')
    except ImportError as exc:
        if 'Database driver blocked' not in str(exc): raise
    else: raise AssertionError('Database driver guard failed')
    try: socket.create_connection(('127.0.0.1', 5432))
    except RuntimeError: pass
    else: raise AssertionError('Network guard failed')
