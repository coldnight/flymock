#-*- coding: utf-8 -*-
"""Unit tests of :class:`flymock.Loader`."""
import json
import os
import unittest

from flymock import Loader


class LoaderTestCase(unittest.TestCase):
    """Loader unit test case."""
    def setUp(self):
        super(LoaderTestCase, self).setUp()
        path = os.path.join(os.path.dirname(__file__), "__mock__")
        self.loader = Loader(path)

    def test_hosts(self):
        """Scan hosts is ok."""
        self.assertSetEqual(
            set(self.loader.iter_hosts()),
            {"example.com", "github.com"},
        )

    def test_response(self):
        """Use url to get mocked response."""
        resp = self.loader.get_response("http://example.com/demo")
        self.assertEqual(resp.code, 200)
        self.assertEqual(resp.method, "GET")
        self.assertDictEqual(
            resp.headers, {'Content-Type': 'application/json'},
        )
        self.assertEqual(resp.body, b"demo.json")

    def test_response_with_file_body(self):
        """Use file as response's body."""
        resp = self.loader.get_response("http://example.com/file")
        self.assertEqual(resp.code, 202)
        self.assertEqual(resp.method, "GET")
        self.assertDictEqual(resp.headers, {})
        self.assertEqual(resp.body, b'{"code": 1}\n')

    def test_response_with_json(self):
        """JSON format response body"""
        resp = self.loader.get_response("http://example.com/json")
        self.assertEqual(resp.body, b'{"code": 2}')
        self.assertEqual(
            resp.headers,
            {"Content-Type": "application/json; charset=UTF-8"},
        )
