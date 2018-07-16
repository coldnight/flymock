"""Integrate with Tornado testing: mock external HTTP request.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import copy
import glob
import importlib
import json
import os

from io import BytesIO

import mock
import six
import yaml

from six.moves.urllib import parse as urlparse   # pylint: disable=E0401
from tornado import concurrent
from tornado import escape
from tornado import httpclient


__version = "0.0.4"


class Response(object):
    """Represents a mocked response load from config file.

    .. attribute:: url

        URL

    .. attribute:: code

        Status code of HTTP response.

    .. attribute:: method

        HTTP request method.

    .. attribute:: body

        Response body in bytes.

    .. attribute:: headers

        Response headers with dict type.
    """
    def __init__(self, url, code, method, body, headers):
        self.url = url
        self.code = code
        self.method = method
        self.body = body
        self.headers = headers

    def patch_json(self, data):
        """Use given ``data`` to patch the response body, if body is not a JSON
        string, raises a :exception:`ValueError`.
        """
        body_data = json.loads(escape.to_unicode(self.body))
        body_data.update(data)
        self.body = escape.utf8(json.dumps(body_data))

    @classmethod
    def make(cls, url, code, method, body_type, body, headers):
        """Make a Response."""

        if body_type == "file":
            with open(body, 'rb') as f:
                body = f.read()
        elif isinstance(body, (dict, list)):
            headers.setdefault(
                "Content-Type", "application/json; charset=UTF-8",
            )
            body = json.dumps(body)

        body = escape.utf8(body)

        new_headers = {}
        for k, v in headers.items():
            key = "-".join(map(lambda x: x.title(), k.split("-")))
            if isinstance(v, six.binary_type):
                v = v.decode('utf8')   # pragma: no cover

            new_headers[key] = v

        return cls(url, code, method, body, new_headers)


class Loader(object):
    """Load mock data."""
    def __init__(self, path):
        self.path = path
        self._pattern = os.path.join(self.path, '*.yaml')
        self._cnfs_by_host = {}
        self._do_scan()

    def _do_scan(self):
        cnfs = self._scan_hosts()
        for c in cnfs:
            with open(c, 'r') as f:
                paths = yaml.load(f)

            self._cnfs_by_host[self._get_host(c)] = [
                {
                    "path": x["path"],
                    "method": x.get("method", "GET").upper(),
                    "code": x.get("code", 200),
                    "headers": x.get("headers", {}),
                    "body": x["body"],
                    "body_type": x.get('body_type', 'string'),
                    "cwd": os.path.dirname(c),
                }
                for x in paths
            ]

    @staticmethod
    def _get_host(cnf_file):
        """Split host from config file path."""
        return os.path.split(cnf_file)[1][:-5]

    def iter_hosts(self):
        """Iterates hosts."""
        for h in self._cnfs_by_host:
            yield h

    def _scan_hosts(self):
        """Scan hosts in mock data directory."""
        results = []
        for item in glob.glob(self._pattern):
            results.append(item)
        return results

    def find_response(self, url, method="GET"):
        """Returns mocked response with url. Returns None if not matched any
        data.
        """
        parsed = urlparse.urlparse(url)
        if parsed.netloc not in self._cnfs_by_host:
            return None

        method = method.upper()
        for item in self._cnfs_by_host[parsed.netloc]:
            if item["path"] == parsed.path and item["method"] == method:

                if item["body_type"] == "file":
                    item["body"] = os.path.join(item["cwd"], item["body"])

                return Response.make(
                    url, item["code"], item["method"], item["body_type"],
                    item["body"], item["headers"],
                )

        return None


class FlyPatcher(object):
    """Mock :method:`tornado.httpclient.HTTPClient.fetch` on fly."""
    def __init__(self, data_dir, fetch_spec=None):
        """Initialize

        :param data_dir: Mock data directory.
        :param fetch_spec:

            Spec of fetch, default: tornado.httpclient.AsyncHTTPClient.fetch
        """
        self.loader = Loader(data_dir)

        if fetch_spec is None:
            fetch_spec = "tornado.httpclient.AsyncHTTPClient.fetch"

        _spec_parts = fetch_spec.split(".")
        module = importlib.import_module('.'.join(_spec_parts[:2]))

        self._original = getattr(
            getattr(module, _spec_parts[2]), _spec_parts[3],
        )
        self.patcher = mock.patch(
            fetch_spec, side_effect=self.mock_fetch, autospec=True,
        )

        self._dynamic_hooks = []

    def start(self):
        return self.patcher.start()

    def stop(self):
        self.patcher.stop()

    @contextlib.contextmanager
    def dynamic_hook(self, hook):
        """Register hook to adjust response dynamic.

        Usage::

            patcher = FlyPatcher("/path/to/__mock__")
            def hook(response):
                response.patch_json({"a": 1})

            with patcher.dynamic_hook(hook):
                # code goes here
                pass

        :param hook:

           A callable object receives a argument of :class:`.Response`

        :type hook: callable
        """
        assert callable(hook)
        self._dynamic_hooks.append(hook)
        try:
            yield
        finally:
            self._dynamic_hooks.remove(hook)

    def patch_json(self, data):
        """Use ``data`` to patch response body, if response body is not JSON
        content that will raise a :exception:`ValueError`.

        Usage::

            patcher = FlyPatcher("/path/to/__mock__")
            with patcher.patch_json({"a": 1}):
                # code goes here
                pass
        """
        def hook(response):
            response.patch_json(data)
        return self.dynamic_hook(hook)

    def mock_fetch(self, ins, request, *args, **kwargs):
        """Mock fetch."""
        if isinstance(request, (six.binary_type, six.text_type)):
            kwargs_copy = copy.deepcopy(kwargs)
            kwargs_copy.pop("raise_error")  # Add in Tornado 5.1
            _request = httpclient.HTTPRequest(request, **kwargs_copy)

            url = _request.url
            method = _request.method
        else:
            url = request.url
            method = request.method

        response = self.loader.find_response(url, method)
        if response is None:
            return self._original(ins, request, *args, **kwargs)

        for hook in self._dynamic_hooks:
            hook(response)

        ret = httpclient.HTTPResponse(
            request,
            response.code,
            response.headers or None,
            BytesIO(response.body),
            response.url,
        )

        future = concurrent.Future()
        future.set_result(ret)
        return future
