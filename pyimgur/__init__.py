# This file is part of PyImgur.

# PyImgur is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# PyImgur is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with PyImgur.  If not, see <http://www.gnu.org/licenses/>.

'''
The easy way of using Imgur.

The default settings in PyImgur are identical with the Imgur default settings.
See https://github.com/Damgaard/PyImgur for details on how to use PyImgur.
'''

import json
import datetime
import types

import requests
import sys

from pyimgur import decorators, errors, objects
from pyimgur.errors import ImgurError
from pyimgur.helpers import _request, _test_response, _to_imgur_list
from objects import *


class Config(object):
    """A class containing the configuration for imgur"""

    API_URL = "https://api.imgur.com/3"
    OAUTH_URL = "https://api.imgur.com/oauth2"
    PUBLIC_CATCHPA = "6LeZbt4SAAAAAG2ccJykgGk_oAqjFgQ1y6daNz-H"
    API_PATHS = {'info_album':        "/album/%s.json",
                 'image':             '/image/%s',
                 'fav_image':         '/image/%s/favorite',
                 'credits':           '/credits.json',
                 'stats':             '/stats.json',
                 'upload':            '/upload.json',
                 'account':           '/account/%s',
                 'gallery_favorites': '/account/%s/gallery_favorites',
                 'account_favorites': '/account/%s/favorites',
                 'account_submissions': '/account/%s/submissions', # paginated
                 'account_settings':  '/account/%s/settings',
                 'account_stats':     '/account/%s/stats',
                 'account_gallery_profile': '/account/%s/gallery_profile',
                 'account_verified_email':  '/account/%s/verifyemail',
                 'account_albums':     '/account/%s/albums', # paginated

                 'acct_albums':       '/account/albums.json',
                 'acct_albums_edit':  '/account/albums/%s.json',
                 'albums_count':      '/account/albums_count.json',
                 'images_count':      '/account/images_count.json',
                 'albums_order':      '/account/albums_order.json',
                 'albums_img_order':  '/account/albums_order/%s.json',
                 'acct_images':       '/account/images.json',
                 'owned_image':       '/account/images/%s.json',
                  # 'oembed':            API_HOST + '/oembed?url=%s',
                 'request_token':     '/request_token',
                 'authorize':         '/authorize',
                 'token':             '/token'}
    OAUTH_PATHS = {'request_token', 'authorize', 'token'}

    def __getitem__(self, key):
        if key in self.OAUTH_PATHS:
            return self.OAUTH_URL + self.API_PATHS[key]
        return self.API_URL + self.API_PATHS[key]


class BaseImgur(object):

    def __init__(self, client_id, client_secret, token=None, logger=None):
        self._client_id = client_id.strip()
        self._client_secret = client_secret.strip()
        self._logger = logger

        self.http = requests.Session()
        self.token = token
        self.config = Config()

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        if token is not None:
            self._token = token
            self.http.headers = {"Authorization": "Bearer {0}".format(self._token)}
        else:
            self.http.headers = {"Authorization": "Client-ID {0}".format(self._client_id)}

    def _log(self, msg):
        try:
            if self._logger:
                self._logger.write('%s   %s\n' % (datetime.now().isoformat(), msg))
        except:
            print "Caught exception [%s] while trying to log msg,  ignored: %s" % (sys.exc_info()[0], msg)

    def _request(self, url, method="get", data={}, headers={}, client=None):
        method = method.lower()
        # Remove parameters with value None
        for k in data.keys():
            if data[k] is None:
                del data[k]

        if not client:
            client = self.http

        if method is "get":
            r = client.request(method, url, params=data, headers=headers, allow_redirects=True)
        else:
            r = client.request(method, url, data=data, headers=headers, allow_redirects=True)

        self._log((r.request.method, r.url, r.status_code))
        if r.status_code < 200 or r.status_code >= 300:
            error = None
            try:
                error = json.loads(r.content or r.text)
            except:
                self._log("Couldn't jsonify error response: %s" % (r.content or r.text))
            raise ImgurError(method, r.url, r.status_code, r.content, error)
        return r

    def request_json(self, url, method='GET', data={}, headers={}, client=None, as_objects=True, type=None):
        response = self._request(url, method, data, headers, client)
        if as_objects and type:
            hook = self._json_imgur_objecter(type)
        else:
            hook = None
        return json.loads(response.text, object_hook=hook)

    def _json_imgur_objecter(self, type):
        def json_to_object(json_data):
            if 'data' in json_data:
                object_class = eval("objects." + type)
                if isinstance(json_data['data'], types.ListType):
                    object_list = []
                    for o in json_data['data']:
                        object_list.append(object_class.from_api_response(self, o))
                    return object_list
                else:
                    return object_class.from_api_response(self, json_data['data'])
            return json_data
        return json_to_object

    # @decorators.oauth_generator
    def get_content(self, url, params=None, start_page=0,
                    limit=0, paginated=True, use_oauth=False, child_type=None):
        """A generator method to return imgur content from a URL.

        Starts at the initial url, and fetches content using the `after`
        JSON data until `limit` entries have been fetched, or the
        `place_holder` has been reached.

        :param url: the url to start fetching content from
        :param params: dictionary containing extra GET data to put in the url
        :param limit: the number of content entries to fetch. If limit <= 0,
            fetch the default for your account (25 for unauthenticated
            users). If limit is None, then fetch as many entries as possible
            It would make multiple calls if necessary.
        :param paginated: This method is supposed to be used only for paginated pages. But many of
            the imgut api which may end up returning a long list is not paginated at the moment. This library
            still uses this method for those APIs, so that when imgur moves those apis to support pagination
            there would be little change here.
        :returns: a list of imgur content, of type Image, GalleryImage,
            GalleryAlbum.
        """
        objects_found = 0
        params = params or {}
        fetch_all = fetch_once = False
        if limit is None:
            fetch_all = True
            params['limit'] = 1024  # Just use a big number
        elif limit > 0:
            params['limit'] = limit
        else:
            fetch_once = True

        use_oauth_old = self._use_oauth
        currentPage = start_page

        # While we still need to fetch more content to reach our limit, do so.
        while fetch_once or fetch_all or objects_found < limit:
            self._use_oauth = use_oauth
            try:
                if paginated:
                    page_data = self.request_json(url + '/' + str(currentPage), data=params, as_objects=True,
                                                  type=child_type)
                    currentPage += 1
                else:
                    page_data = self.request_json(url, data=params, as_objects=True, type=child_type)
            finally:  # Restore _use_oauth value
                self._use_oauth = use_oauth_old
            fetch_once = False
            if len(page_data) > 0:
                for thing in page_data:
                    yield thing
                    objects_found += 1
            else:
                return

class OAuth2Imgur(BaseImgur):

    def get_auth_url(self, response="pin", state="none"):
        url = self.config['authorize'] + "?client_id={cid}&response_type={resp}&state={app_state}"
        pin_url = url.format(cid=self._client_id,resp=response, app_state=state)
        return pin_url

    def get_token(self, pin):
        params = {
            "client_id" : self._client_id,
            "client_secret" : self._client_secret,
            "grant_type" : "pin",
            "pin": pin
        }
        r = self._request(self.config['token'], "post", data=params)
        return r.json()

    def refresh_access_information(self, refresh_token):
        params = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        r = self._request(self.config['token'], 'post', data=params)
        return r.json()


class AuthenticatedImgur(OAuth2Imgur):

    def __init__(self, *args, **kwargs):
        super(AuthenticatedImgur, self).__init__(*args, **kwargs)
        self._use_oauth = False  # Updated on a request by request basis
        self.clear_authentication()

    def refresh_token(self, refresh_token=None, update_session=True):
        response = super(AuthenticatedImgur, self).refresh_access_information(
            refresh_token=refresh_token or self.refresh_token)
        if update_session:
            self.set_access_credentials(**response)

    def clear_authentication(self):
        self._authentication = None
        self.access_token = None
        self.refresh_token = None
        self.http.cookies.clear()
        self.user = None

    # @decorators.require_oauth
    def set_access_credentials(self, access_token, refresh_token=None, username=None,
                               update_user=True):
        """Set the credentials used for OAuth2 authentication.

        Calling this function will overwrite any currently existing access
        credentials.

        :param access_token: the access_token of the authentication
        :param refresh_token: the refresh token of the authentication
        :param update_user: Whether or not to set the user attribute for
            identity scopes

        """
        self.clear_authentication()
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.username = username
        # Update the user object
        if update_user and 'identity' in scope:
            self.user = self.get_account(username)

    def get_me(self):
        response = self.request_json(self.config['account'] % "me")
        user = objects.Account(self, json_dict=response['data'], fetch=False)
        return user


class ImageMixin(BaseImgur):
    def upload_image_local(self, image_path, name=None, title=None, description=None, album=None):
        if image_path:
            with open(image_path, 'rb') as image_file:
                image = image_file.read()
        return self._upload_image(image, "binary", name, title, description, album)

    def upload_image_by_url(self, url, name=None, title=None, description=None, album=None):
        return self._upload_image(url, "URL", name, title, description, album)

    def _upload_image(self, image, type=None, name=None, title=None, description=None, album=None):
        params = {'image': image,
                  'album': album,
                  'type': type,
                  'name': name,
                  'title': title,
                  'description': description}
        return self.request_json(self.config['upload'], 'POST', data=params, type="Image")

    def delete_image(self, id):
        """
        Deletes an image. For an anonymous image, {id} must be the image's deletehash. If the image belongs to
        your account then passing the ID of the image is sufficient.
        """
        return self._request(self.config['image'] % id, "delete")

    def get_image(self, id):
        """Get information about an image."""
        return self.request_json(self.config['image'] % id,  type="Image")

    def update_img_info(self, id, title=None, description=None):
        """Updates the title or description of an image. You can only update an image you own
        and is associated with your account. For an anonymous image, {id} must be the image's deletehash."""
        params = {'title': title,
                  'description': description}
        return _request('PUT', self.config['image'] % id, data=params)

    @decorators.require_authentication
    def fav_img(self, id):
        """Favorite an image with the given ID. The user is required to be logged in to favorite the image."""
        return _request('POST', self.config['fav_image'] % id)


class AccountMixin(BaseImgur):
    def get_account(self, username):
        response = self.request_json(self.config['account'] % username)
        return objects.Account(self, username, response)

    def create_account(self, username):
        params = {'captcha': Config.PUBLIC_CATCHPA}
        response = self.request_json(self.config['account']% username, "POST", data=params)
        return objects.Account(self, username, response)

    def delete_account(self, username="me"):
        self.request_json(self.config['account']% username, "DELETE")

    def get_account_gallery_favs(self, username="me", *args, **kwargs):
        """Return the images the user has favorited in the gallery."""
        return self.get_content(self.config['gallery_favorites'] % username, paginated=False, child_type="Favable",
                                *args, **kwargs)

    # oauth required
    def get_account_favs(self, username="me", *args, **kwargs):
        """Returns the users favorited images, only accessible if you're logged in as the user."""
        return self.get_content(self.config['account_favorites'] % username, paginated=False, child_type="Favable",
                                *args, **kwargs)

    def get_account_submissions(self, username="me", *args, **kwargs):
        """Return the images a user has submitted to the gallery"""
        return self.get_content(self.config['account_submissions'] % username, child_type="Favable", *args, **kwargs)

    def get_account_settings(self, username='me', *args, **kwargs):
        """Returns the account settings, only accessible if you're logged in as the user."""
        return self.request_json(self.config['account_settings'] % username, type="Account")

    def update_account_settings(self, username='me', bio=None, public_images=None, messaging_enabled=None,
                                album_privacy=None, accepted_gallery_terms=None):
        """Updates the account settings for a given user, the user must be logged in."""
        data = {'bio': bio, 'public_images': public_images, 'messaging_enabled': messaging_enabled,
                'album_privacy': album_privacy, 'accepted_gallery_terms': accepted_gallery_terms}
        return self.request_json(self.config['account_settings'] % username, "POST", data=data)

    def get_account_stats(self, username='me'):
        """Return the statistics about the account."""
        return self.request_json(self.config['account_stats'] % username, type='AccountStats')

    def get_account_gallery_profile(self, username="me"):
        return self.request_json(self.config['account_gallery_profile'] % username, type='GalleryProfile')

    def has_verified_email(self, username='me'):
        """Checks to see if user has verified their email address"""
        return self.request_json(self.config['account_verified_email'] % username)['data']

    def send_verification_email(self):
        return self.request_json(self.config['account_verified_email'] % 'me', "POST")

    def get_account_albums(self, username="me", *args, **kwargs):
        """Get all the albums associated with the account. Must be logged in as the user to see secret and hidden
         albums."""
        return self.get_content(self.config["account_albums"] % username, child_type="Album", *args, **kwargs)



class Imgur(ImageMixin, AccountMixin, AuthenticatedImgur):
    pass