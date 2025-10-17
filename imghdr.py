# imghdr.py - Workaround for Python 3.13 compatibility
# This module was removed in Python 3.13, but some older packages still need it

import os

def what(file, h=None):
    """
    Simplified imghdr.what implementation for compatibility
    """
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            location = file.tell()
            h = file.read(32)
            file.seek(location)
    
    if not h:
        return None
    
    # Check for common image formats
    if h.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    elif h.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    elif h.startswith(b'GIF8'):
        return 'gif'
    elif h.startswith(b'BM'):
        return 'bmp'
    elif h.startswith(b'RIFF') and h[8:12] == b'WEBP':
        return 'webp'
    
    return None
