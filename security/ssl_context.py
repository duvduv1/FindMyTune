# security/ssl_context.py

import ssl
from settings import SSL_CERT_PATH, SSL_KEY_PATH

def create_ssl_context() -> ssl.SSLContext:
    """
    Build an SSLContext for server-side TLS using your cert and key.
    """
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=SSL_CERT_PATH, keyfile=SSL_KEY_PATH)
    return context