from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from tornado import httpclient
from tornado import testing

from flymock import FlyPatcher


class FlyPatcherTestCase(testing.AsyncTestCase):
    """FlyPatcher unit test case."""
    def setUp(self):
        super(FlyPatcherTestCase, self).setUp()
        path = os.path.join(os.path.dirname(__file__), "__mock__")
        self.patcher = FlyPatcher(
            path, 'tornado.httpclient.AsyncHTTPClient.fetch',
        )
        self.http_client = httpclient.AsyncHTTPClient()
        self.patcher.start()

    def tearDown(self):
        super(FlyPatcherTestCase, self).tearDown()
        self.patcher.stop()

    @testing.gen_test
    def test_mocked(self):
        """Mocked fetch."""
        resp = yield self.http_client.fetch("http://example.com/demo")
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.body, b"demo.json")

    @testing.gen_test
    def test_patch_json(self):
        """Dynmatic hook to adjust response."""
        resp = yield self.http_client.fetch("http://example.com/json")
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.body, b'{"code": 2}')

        with self.patcher.patch_json({"code": 3}):
            resp = yield self.http_client.fetch("http://example.com/json")
            self.assertEqual(resp.code, 200)
            self.assertEqual(resp.body, b'{"code": 3}')

    @testing.gen_test
    def test_not_mocked(self):
        """Not mocked fetch."""
        resp = yield self.http_client.fetch("https://github.com")
        self.assertEqual(resp.code, 200)
        self.assertIn(b"GitHub", resp.body)

    @testing.gen_test
    def test_request_ok(self):
        """Use :class:`tornado.httpclient.HTTPRequest` as argument."""
        resp = yield self.http_client.fetch(
            httpclient.HTTPRequest('http://example.com/json'),
        )
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.body, b'{"code": 2}')
