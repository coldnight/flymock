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


Create mock data
----------------

Make a directory in your tests package:

.. codeblock:: shell

   $ mkdir __mock__

Use the hostname as the config filename, assume the url is ``http://example.com/demo``,
the config filename should be ``example.com.yaml``, the config see below:

.. codeblock:: yaml

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
