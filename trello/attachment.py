# -*- coding: utf-8 -*-
from __future__ import with_statement, print_function, absolute_import
from dateutil import parser as dateparser
from trello.attachmentpreview import AttachmentPreview

class Attachment(object):
    """
    Class representing a Trello Attachment.
    """
    def __init__(self, card, attachment_id, name=''):
        self.card = card
        self.id = attachment_id

    @classmethod
    def from_json(cls, card, json_obj):
        attachment = cls(card,
                         json_obj['id'],
                         name=json_obj['name'].encode('utf-8'))
        attachment.bytes = json_obj['bytes']
        attachment.edgeColor = json_obj['edgeColor']
        attachment.idMember = json_obj['idMember']
        attachment.isUpload = json_obj['isUpload']
        attachment.mimeType = json_obj['mimeType']
        attachment.url = json_obj['url']
        attachment.name = json_obj['name']
        try:
            attachment.date = dateparser.parse(json_obj['date'])
        except:
            attachment.date = json_obj['date']

        previewsList = []
        for preview in json_obj['previews']:
            item = AttachmentPreview(preview['_id'],
                                     preview['bytes'],
                                     preview['scaled'],
                                     preview['url'],
                                     preview['height'],
                                     preview['width'])
            previewsList.append(item)

        attachment.previews = previewsList

        return attachment


    @classmethod
    def from_json_list(cls, card, json_objs):
        return [cls.from_json(card, obj) for obj in json_objs]

    def __repr__(self):
        return '<Attachment \'%s\'>' % self.name