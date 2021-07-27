#!/usr/bin/env python
# coding=utf-8
import functools
import json
import traceback
from tornado import gen
import tornado.web
import tornado.escape
import tornadoredis
import db

__author__ = 'qingfeng'


def authenticate(method):
    def tokeninvalid(self):
        self.set_status(401)
        self.finish(json.dumps({'code': "INVALID_ACCESS_TOKEN", 'message': u'无效的令牌'}))

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        token = None
        if "access_token" in self.request.arguments:
            token = self.get_argument('access_token', None)
        elif "Access-Token" in self.request.headers.keys():
            token = self.request.headers.get("Access-Token")
        else:
            tokeninvalid(self)
            return
        if token is not None:
            self.request.headers.add('token', token)
            return method(self, *args, **kwargs)
    return wrapper


class BaseHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass


class APIHandler(BaseHandler):
    def data_received(self, chunk):
        pass

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def write_error(self, status_code, **kwargs):
        if 'code' in kwargs:
            code = kwargs['code']
        else:
            code = status_code
        if 'message' in kwargs:
            message = kwargs['message']
        else:
            message = status_code
        self.finish(json.dumps({'code': code, 'message': message}))
        self.set_status(status_code)


class UserAPIHandler(APIHandler):
    def data_received(self, chunk):
        pass
