"""Integrate with :class:`tornado.testing.AsyncHTTPTestCase"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from tornado import gen
from tornado import httpclient
from tornado import testing
from tornado import web

from flymock import FlyPatcher


class DemoHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        resp = yield httpclient.AsyncHTTPClient().fetch(
            "http://example.com/demo"
        )
        self.write(resp.body)

    def delete(self):
        self.set_status(204)


class IntegrateTestCase(testing.AsyncHTTPTestCase):
    """Integrate with asynchronous HTTP server."""
    def setUp(self):
        super(IntegrateTestCase, self).setUp()
        path = os.path.join(os.path.dirname(__file__), "__mock__")
        self.patcher = FlyPatcher(path)
        self.patcher.start()

    def tearDown(self):
        super(IntegrateTestCase, self).tearDown()
        self.patcher.stop()

    def get_app(self):
        return web.Application(
            [
                ('/demo', DemoHandler),
            ]
        )

    def test_ok(self):
        """Ok with fetch."""
        resp = self.fetch("/demo")
        self.assertEqual(resp.body, b"demo.json")

    def test_kwargs(self):
        """Keyword arguments is ok with fetch."""
        resp = self.fetch("/demo", method="DELETE")
        self.assertEqual(resp.code, 204)
