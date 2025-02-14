# -*- coding: utf-8 -*-
from __future__ import with_statement, print_function, absolute_import
import json
import requests
from requests_oauthlib import OAuth1
from trello.board import Board
from trello.card import Card
from trello.trellolist import List
from trello.organization import Organization
from trello.member import Member
from trello.webhook import WebHook
from trello.exceptions import *
from trello.label import Label

try:
    # PyOpenSSL works around some issues in python ssl modules
    # In particular in python < 2.7.9 and python < 3.2
    # It is not a hard requirement, so it's not listed in requirements.txt
    # More info https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()
except:
    pass


class TrelloClient(object):
    """ Base class for Trello API access """

    def __init__(self, api_key, api_secret=None, token=None, token_secret=None):
        """
        Constructor

        :api_key: API key generated at https://trello.com/1/appKey/generate
        :api_secret: the secret component of api_key
        :token_key: OAuth token generated by the user in
                    trello.util.create_oauth_token
        :token_secret: the OAuth client secret for the given OAuth token
        """

        # client key and secret for oauth1 session
        if api_key or token:
            self.oauth = OAuth1(client_key=api_key, client_secret=api_secret,
                                resource_owner_key=token, resource_owner_secret=token_secret)
        else:
            self.oauth = None

        self.public_only = token is None
        self.api_key = api_key
        self.api_secret = api_secret
        self.resource_owner_key = token
        self.resource_owner_secret = token_secret

    def info_for_all_boards(self, actions):
        """
        Use this if you want to retrieve info for all your boards in one swoop
        """
        if self.public_only:
            return None
        else:
            json_obj = self.fetch_json(
                '/members/me/boards/all',
                query_params={'actions': actions})
            self.all_info = json_obj

    def logout(self):
        """Log out of Trello."""
        # TODO: This function.
        raise NotImplementedError()

    def list_boards(self, board_filter="all"):
        """
        Returns all boards for your Trello user

        :return: a list of Python objects representing the Trello boards.
        :rtype: Board

        Each board has the following noteworthy attributes:
            - id: the board's identifier
            - name: Name of the board
            - desc: Description of the board (optional - may be missing from the
                    returned JSON)
            - closed: Boolean representing whether this board is closed or not
            - url: URL to the board
        """
        json_obj = self.fetch_json('/members/me/boards/?filter=%s' % board_filter)
        return [Board.from_json(self, json_obj=obj) for obj in json_obj]

    def list_organizations(self):
        """
        Returns all organizations for your Trello user

        :return: a list of Python objects representing the Trello organizations.
        :rtype: Organization

        Each organization has the following noteworthy attributes:
            - id: the organization's identifier
            - name: Name of the organization
            - desc: Description of the organization (optional - may be missing from the
                    returned JSON)
            - closed: Boolean representing whether this organization is closed or not
            - url: URL to the organization
        """
        json_obj = self.fetch_json('members/me/organizations')
        return [Organization.from_json(self, obj) for obj in json_obj]

    def get_organization(self, organization_id):
        '''Get organization

        :rtype: Organization
        '''
        obj = self.fetch_json('/organizations/' + organization_id)

        return Organization.from_json(self, obj)

    def get_board(self, board_id):
        '''Get board

        :rtype: Board
        '''
        obj = self.fetch_json('/boards/' + board_id)
        return Board.from_json(self, json_obj=obj)

    def add_board(self, board_name, source_board=None):
        '''Create board
        :param board_name: Name of the board to create
        :param source_board: Optional Board to copy
        :rtype: Board
        '''
        post_args={'name': board_name}
        if source_board is not None:
            post_args['idBoardSource'] = source_board.id

        obj = self.fetch_json('/boards', http_method='POST',
                              post_args=post_args)
        return Board.from_json(self, json_obj=obj)

    def get_member(self, member_id):
        '''Get member

        :rtype: Member
        '''
        return Member(self, member_id).fetch()

    def get_card(self, card_id):
        '''Get card

        :rtype: Card
        '''
        card_json = self.fetch_json('/cards/' + card_id)
        list_json = self.fetch_json('/lists/' + card_json['idList'])
        board = self.get_board(card_json['idBoard'])
        return Card.from_json(List.from_json(board, list_json), card_json)

    def get_label(self, label_id, board_id):
        '''Get Label

        Requires the parent board id the label is on

        :rtype: Label
        '''
        board = self.get_board(board_id)
        label_json = self.fetch_json('/labels/' + label_id)
        return Label.from_json(board, label_json)

    def fetch_json(
            self,
            uri_path,
            http_method='GET',
            headers=None,
            query_params=None,
            post_args=None,
            files=None):
        """ Fetch some JSON from Trello """

        # explicit values here to avoid mutable default values
        if headers is None:
            headers = {}
        if query_params is None:
            query_params = {}
        if post_args is None:
            post_args = {}

        # if files specified, we don't want any data
        data = None
        if files is None:
            data = json.dumps(post_args)

        # set content type and accept headers to handle JSON
        if http_method in ("POST", "PUT", "DELETE") and not files:
            headers['Content-Type'] = 'application/json; charset=utf-8'

        headers['Accept'] = 'application/json'

        # construct the full URL without query parameters
        if uri_path[0] == '/':
            uri_path = uri_path[1:]
        url = 'https://api.trello.com/1/%s' % uri_path

        # perform the HTTP requests, if possible uses OAuth authentication
        response = requests.request(http_method, url, params=query_params,
                                    headers=headers, data=data,
                                    auth=self.oauth, files=files)

        if response.status_code == 401:
            raise Unauthorized("%s at %s" % (response.text, url), response)
        if response.status_code != 200:
            raise ResourceUnavailable("%s at %s" % (response.text, url), response)

        return response.json()

    def list_hooks(self, token=None):
        """
        Returns a list of all hooks associated with a specific token. If you don't pass in a token,
        it tries to use the token associated with the TrelloClient object (if it exists)
        """
        token = token or self.resource_owner_key

        if token is None:
            raise TokenError("You need to pass an auth token in to list hooks.")
        else:
            url = "/tokens/%s/webhooks" % token
            return self._existing_hook_objs(self.fetch_json(url), token)

    def _existing_hook_objs(self, hooks, token):
        """
        Given a list of hook dicts passed from list_hooks, creates
        the hook objects
        """
        all_hooks = []
        for hook in hooks:
            new_hook = WebHook(self, token, hook['id'], hook['description'],
                               hook['idModel'],
                               hook['callbackURL'], hook['active'])
            all_hooks.append(new_hook)
        return all_hooks

    def create_hook(self, callback_url, id_model, desc=None, token=None):
        """
        Creates a new webhook. Returns the WebHook object created.

        There seems to be some sort of bug that makes you unable to create a
        hook using httplib2, so I'm using urllib2 for that instead.
        """
        token = token or self.resource_owner_key

        if token is None:
            raise TokenError("You need to pass an auth token in to create a hook.")

        url = "https://trello.com/1/tokens/%s/webhooks/" % token
        data = {'callbackURL': callback_url, 'idModel': id_model,
                'description': desc}

        response = requests.post(url, data=data, auth=self.oauth)

        if response.status_code == 200:
            hook_id = response.json()['id']
            return WebHook(self, token, hook_id, desc, id_model, callback_url, True)
        else:
            return False
