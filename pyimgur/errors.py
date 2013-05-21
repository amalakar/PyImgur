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
Custom errors in PyImgur.

LookupError is used to indicate a function was called with an invalid
argument and thus avoid API calls with undefined behavior. Read the official
imgur documentation on error handling for more information.
http://api.imgur.com/error_handling
'''

class AccessDeniedError(Exception):
    """We don't have the authorization to do that."""

class ImgurError(Exception):
    def __init__(self, method, url, status_code, error, msg=None):
        self.method = method
        self.url = url
        self.http_code = status_code
        self.error = error
        if msg is not None:
            self.msg = "Error doing {0} on url: {1}. Code: {2}. Error: {3} "\
                .format(method, url, status_code['data']['error'])


    def __str__(self):
        return self.msg

def raise_error(http_code, error):
    raise ImgurError(http_code, error)
