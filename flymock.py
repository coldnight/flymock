"""Integrate with Tornado testing: mock external HTTP request.

Create mock data
----------------

Directory structure of mock data:

"""
import glob
import json
import os

import six
import yaml

from six.moves.urllib import parse as urlparse


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

        if isinstance(body, six.text_type):
            body = body.encode("utf8")

        new_headers = {}
        for k, v in headers.items():
            key_parts = map(lambda x: x.title(), k.split("-"))
            key = "-".join(key_parts)
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

    def get_response(self, url, method="GET"):
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


class FlyMock(object):
    def __init__(self, data_dir):
        pass
