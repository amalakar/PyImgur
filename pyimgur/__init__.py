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
import os
import datetime

import requests
import sys

from pyimgur import decorators, errors
from pyimgur.errors import ImgurError
from pyimgur.helpers import _request, _test_response, _to_imgur_list

_API_HOST = "https://api.imgur.com"
_BASE_URL = _API_HOST + "/3"
_OAUTH_URL = _API_HOST + "/oauth2"
_API_URL = {'info_album': _BASE_URL + "/album/%s.json",
            'image': _BASE_URL + '/image/%s',
            'fav_image': _BASE_URL + '/image/%s/favorite',
            'credits': _BASE_URL + '/credits.json',
            'stats': _BASE_URL + '/stats.json',
            'upload': _BASE_URL + '/upload.json',
            'sideload': _BASE_URL + '/upload.json',
            'oembed': _API_HOST + 'oembed?url=%s',
            'request_token': _OAUTH_URL + '/request_token',
            'authorize': _OAUTH_URL + '/authorize',
            'token': _OAUTH_URL + '/token',
            'account': _BASE_URL + '/account.json',
            'acct_albums': _BASE_URL + '/account/albums.json',
            'acct_albums_edit': _BASE_URL + '/account/albums/%s.json',
            'albums_count': _BASE_URL + '/account/albums_count.json',
            'images_count': _BASE_URL + '/account/images_count.json',
            'albums_order': _BASE_URL + '/account/albums_order.json',
            'albums_img_order': _BASE_URL + '/account/albums_order/%s.json',
            'acct_images': _BASE_URL + '/account/images.json',
            'owned_image': _BASE_URL + '/account/images/%s.json'
}


class pyimgur(object):

    def __init__(self, client_id, client_secret, token=None, logger=None):
        self._client_id = client_id.strip()
        self._client_secret = client_secret.strip()
        self._logger = logger

        self._client = requests.Session()
        self.token = token

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        if token is not None:
            self._token = token
            self._client.headers = {"Authorization": "Bearer {0}".format(self._token)}
        else:
            self._client.headers = {"Authorization": "Client-ID {0}".format(self._client_id)}


    def get_auth_url(self, response="pin", state="none"):
        url = _API_URL['authorize'] + "?client_id={cid}&response_type={resp}&state={app_state}"
        pin_url = url.format(cid=self._client_id,resp=response, app_state=state)
        return pin_url

    def get_token(self, pin):
        params = {
            "client_id" : self._client_id,
            "client_secret" : self._client_secret,
            "grant_type" : "pin",
            "pin": pin
        }
        r = self._request("post", _API_URL['token'], data=params)
        resp = r.json()
        access_token = resp['access_token']
        refresh_token = resp['refresh_token']
        return access_token, refresh_token

    def upload_image_local(self, image_path, name=None, title=None, description=None, album=None):
        if image_path:
            with open(image_path, 'rb') as image_file:
                image = image_file.read()
        return self._upload_image(image, "binary", name, title, description, album)

    def upload_image_by_url(self, url, name=None, title=None, description=None, album=None):
        return self._upload_image(url, "URL",name, title, description, album)

    def _upload_image(self, image, type=None, name=None, title=None, description=None, album=None):
        params = {'image': image,
                  'album': album,
                  'type': type,
                  'name': name,
                  'title': title,
                  'description': description}
        return self._request("POST", _API_URL['upload'], data=params)

    def delete_image(self, id):
        """
        Deletes an image. For an anonymous image, {id} must be the image's deletehash. If the image belongs to
        your account then passing the ID of the image is sufficient.
        """
        return self._request("DELETE", _API_URL['image'] % id)

    def get_info(self, id):
        """Get information about an image."""
        return _request("GET", _API_URL['image'] % id)

    def update_img_info(self, id, title=None, description=None):
        """Updates the title or description of an image. You can only update an image you own
        and is associated with your account. For an anonymous image, {id} must be the image's deletehash."""
        params = {'title': title,
                  'description': description}
        return _request('PUT', _API_URL['image'] % id, data=params)

    @decorators.require_authentication
    def fav_img(self, id):
        """Favorite an image with the given ID. The user is required to be logged in to favorite the image."""
        return _request('POST', _API_URL['fav_image'] % id)

    def _log(self, msg):
        try:
            if self._logger:
                self._logger.write('%s   %s\n' % (datetime.now().isoformat(), msg))
        except:
            print "Caught exception [%s] while trying to log msg,  ignored: %s" % (sys.exc_info()[0], msg)

    def _request(self, method, url, data={}, headers={}, client=None):
        method = method.lower()
        # Remove parameters with value None
        for k in data.keys():
            if data[k] is None:
                del data[k]

        if not url.startswith('http'):
            url = "%s%s" % (_BASE_URL, url)

        if not client:
            client = self._client

        if method is "get":
            r = client.request(method, url, params=data, headers=headers, allow_redirects=True)
        else:
            r = client.request(method, url, data=data, headers=headers, allow_redirects=True)

        self._log((r.request.method, r.url, r.status_code))
        if r.status_code < 200 or r.status_code >= 300:
            error = {}
            try:
                error = json.loads(r.content or r.text)
            except:
                self._log("Couldn't jsonify error response: %s" % (r.content or r.text))
            raise ImgurError(method, r.url, r.status_code, r.content, error)
        return r

def _test_response(r):
    """
    Test if everything is okay.

    If everything isn't okay, call the appropriate error code.
    """
    if r.status_code != 200:
        pyimgur.errors.raise_error(r.status_code, r.json())
    elif content == '':
        error_message = ("Malformed json returned from Imgur. "
                         "Status_code: %d" % status_code)
        raise pyimgur.errors.imgurapiError(error_message)







# Maybe some loading of stored access from an ini file
_client = None

########################
# Functions not requirering or related to any authentication
########################

def credits():
    """Returns information about our API credits."""
    return _request(_API_URL['credits'], locals())['credits']



def download_image(img_hash, size='original'):
    """
    Download the image.

    The first that exists of title, caption or hash on imgur will be used as
    the new local name of the image. Overwrites any existing file of the same
    name.
    """
    if size not in ['original', 'small_square', 'large_thumbnail']:
        raise LookupError('Size must be original, small_square or '
                          'large_thumbnail')
    info = info_image(img_hash)
    path = info['links'][size]
    _, file_extension = os.path.splitext(path)
    name = (info['image']['title'] or info['image']['caption'] or
            info['image']['hash'])
    full_name = name + file_extension
    with open(full_name, 'wb') as local_file:
        request_result = requests.get(path)
        local_file.write(request_result.content)
    return full_name

def info_album(album_id):
    """
    Return information about an album.

    Note that privacy setting is not exposed via this command.
    """
    return _request(_API_URL['info_album'] % album_id, locals())['album']

def oembed(url, maxheight=None, maxwidth=None):
    """Return embed code as well as additional information."""
    format = 'json'
    return _request(_API_URL['oembed'], locals())

def sideload(url, edit=False):
    """Return an url that sideloads the image at url."""
    if not url.startswith('http'):
        raise LookupError('Url must start with http')
    if edit:
        return _API_URL['sideload'] + '?edit&url=%s' % url
    return _API_URL['sideload'] + '?url=%s' % url

def stats(view='month'):
    """Return imgur-wide statistics."""
    if view not in ('', 'today', 'week', 'month'):
        raise LookupError('View must be today, week or month')
    return _request(_API_URL['stats'], locals())['stats']


########################
# Authenticated Application
########################

@decorators.require_authentication
def account_images(noalbum=False):
    """
    Return a list of images uploaded to this account.

    If noalbum is True, only return images that doesn't belong to any album.
    """
    kwargs = locals()
    if not noalbum:
        del kwargs['noalbum']
    return _request(_API_URL['acct_images'], kwargs)['images']


@decorators.require_authentication
def count_albums():
    """
    Returns the number of albums.

    Note, this returns an integer. Not a dict.
    """
    return (_request(_API_URL['albums_count'], locals())['albums_count']
                                                         ['count'])

@decorators.require_authentication
def count_images():
    """
    Returns the number of images belonging to the account.

    Note, this returns an integer. Not a dict.
    """
    return (_request(_API_URL['images_count'], locals())
                                                ['images_count']['count'])

@decorators.require_authentication
def create_album(title='', description='', privacy='public', layout = 'blog'):
    """Create a new album for the authenticated account."""
    if layout not in ('', 'blog', 'horizontal', 'vertical', 'grid'):
        raise LookupError('Layout must be blog, horizontal, vertical or grid')
    elif privacy not in ('', 'public', 'hidden', 'secret'):
        raise LookupError('Privacy must be public, hidden or secret')
    return (_request(_API_URL['acct_albums'], locals(), method='POST')
                                                        ['albums'])

@decorators.require_authentication
def delete_album(album_id):
    """Delete the album."""
    return _request(_API_URL['acct_albums_edit'] % album_id, locals(),
            method='DELETE')['albums']

# BUG. Doesn't work with images or del_images
# It doesn't come with an error message. Nothing just happens
# Appears to be upstream bug, as add_images can be made to work with a hack.
@decorators.require_authentication
def edit_album(album_id, title='', description='', cover='', privacy='',
               layout='', images=[], add_images=[], del_images=[]):
    """Edit the variables for the album."""
    add_images = [''] + add_images
    images     = _to_imgur_list(images)
    add_images = _to_imgur_list(add_images)
    del_images = _to_imgur_list(del_images)
    if layout not in ('', 'blog', 'horizontal', 'vertical', 'grid'):
        raise LookupError('Layout must be blog, horizontal, vertical or grid')
    elif privacy not in ('', 'public', 'hidden', 'secret'):
        raise LookupError('Privacy must be public, hidden or secret')
    return _request(_API_URL['acct_albums_edit'] % album_id, locals(),
                                                    method='POST')['albums']

@decorators.require_authentication
def edit_image(img_hash, title='', caption=''):
    """Edit an image belonging to an authenticated account."""
    return _request(_API_URL['owned_image'] % img_hash, locals(),
                                               method='POST')['images']

@decorators.require_authentication
def info_account():
    """Return information about the account."""
    return _request(_API_URL['account'], locals())['account']

@decorators.require_authentication
def info_albums(count=30, page=1):
    """List information about albums."""
    return _request(_API_URL['acct_albums'], locals())['albums']

@decorators.require_authentication
def order_albums(ids):
    """
    Re-order albums.

    Note any misspelling will cause a silent falling. Upstream bug cause it to
    deadlock after enough changes and prevent any further online change.
    Making a single manuel change restes this and allow further api reordering.
    """
    ids = _to_imgur_list(ids)
    return (_request(_API_URL['albums_order'], locals(), method='POST')
                                                          ['albums_order'])

# BUG. it cannot find the album with json
# Can find the album, but won't update if I just go with xml
# The following is how it should be if everything worked upstream
'''
@decorators.require_authentication
def order_album_images(album_id, hashes):
    """Reorder the images within an album."""
    hashes = _to_imgur_list(hashes)
    return _request(_API_PATH['albums_img_order'] % album_id, locals(),
                                                              method='POST')
'''
