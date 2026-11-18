import socket
import pytest

def test_database_driver_blocked():
    with pytest.raises(ImportError, match='Database driver blocked'): __import__('psycopg2')

def test_socket_blocked():
    with pytest.raises(RuntimeError, match='Network connection blocked'):
        with socket.socket() as sock: sock.connect(('127.0.0.1', 5432))
