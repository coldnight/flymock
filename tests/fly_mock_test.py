import os

from tornado import testing
from tornado import httpclient

from flymock import FlyPatcher


class FlyPatcherTestCase(testing.AsyncTestCase):
    """FlyPatcher unit test case."""
    def setUp(self):
        super(FlyPatcherTestCase, self).setUp()
        path = os.path.join(os.path.dirname(__file__), "__mock__")
        self.patcher = FlyPatcher(path)
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
    def test_not_mocked(self):
        """Not mocked fetch."""
        resp = yield self.http_client.fetch("https://github.com")
        self.assertEqual(resp.code, 200)
        self.assertIn(b"GitHub", resp.body)
