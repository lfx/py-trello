from __future__ import with_statement, print_function, absolute_import

class AttachmentPreview(object):
    """
    Class representing a Trello Attachment Preview.
    """
    def __init__(self, id, bytes, scaled, url, height, width):
        self.id = id
        self.bytes = bytes
        self.scaled = scaled
        self.url = url
        self.height = height
        self.width = width

    def __repr__(self):
        return '<AttachmentPreview %s>' % self.name


