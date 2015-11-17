#!/usr/bin/env python
# coding=utf-8
import hmac
import json
import uuid
from tornado import gen
from tornado_json import schema
import tornadoredis
from base import APIHandler, tornado
import db

__author__ = 'qingfeng'


class LoginHandler(APIHandler):
    def data_received(self, chunk):
        pass

    @gen.coroutine
    def post(self, *args, **kwargs):
        # if "Content-type" not in self.request.headers.keys():
        #     self.set_status(400)
        #     self.finish(json.dumps({'code': "MALFORMED_JSON", 'message': u'格式错误'}))
        if self.request.body is "":
            self.set_status(400)
            self.finish(json.dumps({'code': "EMPTY_REQUEST", 'message': u'请求体为空'}))
        else:
            data = None
            try:
                data = tornado.escape.json_decode(self.request.body)
            except:
                self.send_error(status_code=400, code="MALFORMED_JSON", message="格式错误")
            else:
                if data is None:
                    self.set_status(400)
                    self.finish(json.dumps({'code': "EMPTY_REQUEST", 'message': u'请求体为空'}))
                elif "username" not in data.keys() or "password" not in data.keys():
                    self.set_status(400)
                    self.finish(json.dumps({'code': "MALFORMED_JSON", 'message': u'格式错误'}))
                else:
                    cur = yield db.POOL.execute("SELECT * FROM user where name = '%s' limit 1" % data["username"])
                    result = cur.fetchone()
                    cur.close()
                    if data["password"] == result["password"]:
                        user_id = result["id"]
                        unique = uuid.uuid4()
                        token = hmac.new(str(user_id)).hexdigest()
                        c = tornadoredis.Client(connection_pool=db.REDIS_CONNECTION_POOL)
                        res = yield gen.Task(c.zrangebyscore, 'user:token:list', user_id, user_id)
                        if res:
                            yield gen.Task(c.zremrangebyscore, "user:token:list", user_id, user_id)
                        with c.pipeline() as pipe:
                            pipe.zadd('user:token:list', user_id, token)
                            yield tornado.gen.Task(pipe.execute)
                        c.disconnect()
                        self.finish(
                            json.dumps({'user_id': user_id, 'access_token': token, 'username': result["name"]}))
                    else:
                        self.set_status(403)
                        self.finish(json.dumps({'code': "USER_AUTH_FAIL", 'message': u'用户名或密码错误'}))
