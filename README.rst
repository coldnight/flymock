.. image:: https://travis-ci.org/coldnight/flymock.svg?branch=master
    :target: https://travis-ci.org/coldnight/flymock
.. image:: https://codecov.io/gh/coldnight/flymock/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/coldnight/flymock
.. image:: https://img.shields.io/pypi/v/flymock.svg
    :target: https://pypi.python.org/pypi/flymock
    :alt: PyPI

flymock
=======

Easy to mock external HTTP request in Tornado.

Installation
------------

.. code-block:: shell

    $ pip install --upgrade flymock

Create mock data
----------------

Make a directory in your tests package:

.. code-block:: shell

    $ mkdir __mock__

Use the hostname as the config filename, assume the url is ``http://example.com/demo``,
the config filename should be ``example.com.yaml``, the config see below:

.. code-block:: yaml

    - path: /demo    # path of the request to match
      method: GET    # method of the request to match
      headers:       # Response headers
        Content-Type: application/json
      body: Hello world # Response body
      code: 200      # Response status code

    - path: /file
      body_type: file     # Use a file content as the response
      body: demo.json     # Filename(same path of the config file)
      code: 202

    - path: /json
      body:               # If body is an object, that will response JSON content.
       code: 2


Usage
-----

.. code-block:: python

    import os

    from tornado import httpclient
    from tornado import testing

    from flymock import FlyPatcher


    class DemoTestCase(testing.AsyncTestCase):
        def setUp(self):
            super(DemoTestCase, self).setUp()
            path = os.path.join(os.path.dirname(__file__), "__mock__")
            self.patcher = FlyPatcher(path)
            self.http_client = httpclient.AsyncHTTPClient()
            self.patcher.start()

        def tearDown(self):
            super(DemoTestCase, self).tearDown()
            self.patcher.stop()

        @testing.gen_test
        def test_mocked(self):
            resp = yield self.http_client.fetch("http://example.com/demo")
            self.assertEqual(resp.code, 200)


Adjust response dynamic:

.. code-block:: python

    patcher = FlyPatcher("/path/to/__mock__")
    def hook(response):
       response.patch_json({"a": 1})

    with patcher.dynamic_hook(hook):
        # code goes here
        pass

    # shortcut to adjust JSON
    with patcher.patch_json({"a": 1}):
       # code goes here
       pass
