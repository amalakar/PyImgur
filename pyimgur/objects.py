import six
from pyimgur.errors import AccessDeniedError

__author__ = 'malakar'


class ImgurObject(object):

    @classmethod
    def from_api_response(cls, imgur_session, json_dict):
        """Return an instance of the appropriate class from the json_dict."""
        return cls(imgur_session, json_dict=json_dict)

    def __init__(self, imgur_session, json_dict=None, fetch=True, underscore_names=None):
        """Create a new object from the dict of attributes returned by the API.

        The fetch parameter specifies whether to retrieve the object's
        information from the API (only matters when it isn't provided using
        json_dict).

        """

        self.imgur_session = imgur_session
        self._underscore_names = underscore_names
        self._populated = self._populate(json_dict, fetch)

    def _get_json_dict(self):
        response = self.imgur_session.request_json(self.url, type=self.__class__,
                                                   as_objects=False)
        return response['data']

    def _populate(self, json_dict, fetch):
        if json_dict is None:
            if fetch:
                json_dict = self._get_json_dict()
            else:
                json_dict = {}

        if isinstance(json_dict, list):
            json_dict = {'_tmp': json_dict}

        for name, value in six.iteritems(json_dict):
            if self._underscore_names and name in self._underscore_names:
                name = '_' + name
            setattr(self, name, value)
        return bool(json_dict) or fetch


class Image(ImgurObject):
    def delete(self):
        self.imgur_session.delete_image(self._get_id())

    def update_img_info(self,  title=None, description=None):
        self.imgur_session.update_img_info(self._get_id(), title, description)

    def fav(self):
        self.imgur_session.fav_image(self.id)

    def _get_id(self):
        if self.deletehash:
            return self.deletehash
        else:
            if self._owned:
                self.id
            else:
                self._populate(None, True)
                if self.deletehash:
                    return self.deletehash
                else:
                    raise AccessDeniedError()


class Account(ImgurObject):
    def __init__(self, imgur_session, url=None, json_dict=None, fetch=True):
        if url is not None:
            self.url = url
        super(Account, self).__init__(imgur_session, json_dict, fetch)

    def delete(self):
        pass

    def get_gallery_favs(self):
        return self.imgur_session.get_gallery_favs()

    def get_favs(self):
        return self.imgur_session.get_favs()

    def get_submissions(self):
        pass

    def get_settings(self):
        pass

    def update_settings(self):
        pass

    def get_stats(self):
        pass

    def get_gallery_profile(self):
        pass

    def verify_email(self):
        pass

    def get_albums(self):
        pass

    def get_album(self, id):
        pass

    def get_album_ids(self):
        pass

    def get_album_count(self):
        pass

    def get_comments(self):
        pass

    def get_comment_ids(self):
        pass

    def get_comment_count(self):
        pass

    def delete_comment(self):
        pass

    def get_images(self):
        pass

    def get_image(self):
        pass

    def get_image_ids(self):
        pass

    def get_image_count(self):
        pass

    def delete_image(self):
        pass

    def get_notifications(self):
        pass

    def get_messages(self):
        pass

    def send_message(self):
        pass

    def get_replies(self):
        pass


class Comment(ImgurObject):
    def delete(self):
        pass

    def get_replies(self):
        pass

    def vote(self):
        pass

    def report(self):
        pass

    def reply(self):
        pass


class Album(ImgurObject):
    def create(self):
        pass

    def delete(self):
        pass

    def get_images(self):
        pass

    def get_image(self):
        pass

    def update(self):
        pass

    def fav(self):
        pass

    def set_images(self):
        pass

    def add_image(self):
        pass

    def remove_images(self):
        pass


class Favable(Album):

    @classmethod
    def from_api_response(cls, imgur_session, json_dict):
        """Return an instance of the appropriate class from the json_dict."""
        if json_dict['is_album']:
            return Album(imgur_session, json_dict=json_dict)
        else:
            return Image(imgur_session, json_dict=json_dict)


class Notification(ImgurObject):
    pass


class Gallery(ImgurObject):
    pass


