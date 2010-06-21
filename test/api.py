"""
TODO: http://blog.appenginefan.com/2008/06/unit-tests-for-google-app-engine-apps.html
"""
import _conf
import mocker


class APITest(mocker.MockerTestCase):

    def setUp(self):
        self.request = self.mocker.mock()
        self.response = self.mocker.mock()
        # TODO
        self.handler1 = helloworld.MainPage()
        self.handler2 = helloworld.Guestbook()
        self.handler1.request = self.request
        self.handler1.response = self.response
        self.handler2.request = self.request
        self.handler2.response = self.response
        self.Greeting = self.mocker.replace('helloworld.Greeting')
        self.users = self.mocker.replace('google.appengine.api.users')
        self.template = self.mocker.replace('google.appengine.ext.webapp.template')

