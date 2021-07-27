#!/usr/bin/env python
# coding=utf-8
import hmac
import json
import uuid
import time
import sys
from tornado import gen
import tornadoredis
from base import BaseHandler, APIHandler, UserAPIHandler, tornado, authenticate
import db

__author__ = 'qingfeng'


class IndexHandler(UserAPIHandler):
    def data_received(self, chunk):
        pass


class FoodsHandler(UserAPIHandler):
    SUPPORTED_METHODS = "GET"

    def data_received(self, chunk):
        pass

    @authenticate
    @gen.coroutine
    def get(self, *args, **kwargs):
        token = self.request.headers.get("token")
        c = tornadoredis.Client(connection_pool=db.REDIS_CONNECTION_POOL)
        user_id = yield gen.Task(c.zscore, 'user:token:list', token)
        c.disconnect()
        if user_id is None:
            self.send_error(status_code=401, code="INVALID_ACCESS_TOKEN", message="无效的令牌")
        else:
            cur = yield db.POOL.execute("SELECT * FROM food")
            datas = cur.fetchall()
            cur.close()
            self.finish(json.dumps(datas))


class CreateCartHandler(UserAPIHandler):
    def data_received(self, chunk):
        pass

    @authenticate
    @gen.coroutine
    def post(self, *args, **kwargs):
        token = self.request.headers.get("token")
        cart_id = hmac.new(uuid.uuid4().bytes).hexdigest()
        c = tornadoredis.Client(connection_pool=db.REDIS_CONNECTION_POOL)
        user_id = yield gen.Task(c.zscore, 'user:token:list', token)
        if user_id is None:
            self.set_status(401)
            self.finish(json.dumps({'code': "INVALID_ACCESS_TOKEN", 'message': u'无效的令牌'}))
        else:
            with c.pipeline() as pipe:
                pipe.hset("cart:%s" % cart_id, "user_id", user_id)
                pipe.sadd("cart:id", cart_id)
                yield tornado.gen.Task(pipe.execute)
            c.disconnect()
            self.finish(json.dumps({'cart_id': cart_id}))


class CartHandler(UserAPIHandler):
    def data_received(self, chunk):
        pass

    @authenticate
    @gen.coroutine
    def patch(self, cart_id, *args, **kwargs):
        if self.request.body is "":
            self.set_status(400)
            self.finish(json.dumps({'code': "EMPTY_REQUEST", 'message': u'请求体为空'}))
        token = self.request.headers.get("token")
        data = None
        c = tornadoredis.Client(connection_pool=db.REDIS_CONNECTION_POOL)
        user_id = yield gen.Task(c.zscore, 'user:token:list', token)
        if user_id is None:
            self.set_status(401)
            self.finish(json.dumps({'code': "INVALID_ACCESS_TOKEN", 'message': u'无效的令牌'}))
        else:
            try:
                data = tornado.escape.json_decode(self.request.body)
            except:
                # self.send_error(status_code=400, code="MALFORMED_JSON", message="格式错误")
                self.set_status(400)
                self.finish(json.dumps({'code': "MALFORMED_JSON", 'message': u'格式错误'}))
            else:
                if data is None:
                    self.set_status(400)
                    self.finish(json.dumps({'code': "EMPTY_REQUEST", 'message': u'请求体为空'}))
                elif "food_id" not in data.keys() or "count" not in data.keys():
                    self.set_status(400)
                    self.finish(json.dumps({'code': "MALFORMED_JSON", 'message': u'格式错误'}))
                else:
                    ismember = yield gen.Task(c.sismember, 'cart:id', cart_id)
                    if ismember == 0:
                        # self.write_error(status_code=404, message="篮子不存在", code="CART_NOT_FOUND")
                        self.set_status(404)
                        self.finish(json.dumps({'code': "CART_NOT_FOUND", 'message': u'篮子不存在'}))
                    else:
                        if data["count"] > 3:
                            self.set_status(403)
                            self.finish(json.dumps({'code': "FOOD_OUT_OF_LIMIT", 'message': u'篮子中食物数量超过了三个'}))
                        isusercart = yield gen.Task(c.hget, "cart:%s" % cart_id, "user_id")
                        if not (isusercart == str(user_id)):
                            self.set_status(401)
                            self.finish(json.dumps({'code': "NOT_AUTHORIZED_TO_ACCESS_CART", 'message': u'无权限访问指定的篮子'}))
                        cur = yield db.POOL.execute("SELECT * FROM food where id = '%s' limit 1" % data["food_id"])
                        result = cur.fetchone()
                        cur.close()
                        if result:
                            total = yield gen.Task(c.hget, "cart:%s" % cart_id, "total_items")
                            if total:
                                if (int(total) + data["count"]) > 3:
                                    self.set_status(403)
                                    self.finish(json.dumps({'code': "FOOD_OUT_OF_LIMIT", 'message': u'篮子中食物数量超过了三个'}))
                            else:
                                with c.pipeline() as pipe:
                                    pipe.sadd("cart:id", cart_id)
                                    pipe.hincrby("cart:%s" % cart_id, "total_items", data["count"])
                                    pipe.hincrby("cart:%s" % cart_id, "total", data["count"] * result["price"])
                                    pipe.hincrby("cart:%s" % cart_id, data["food_id"], data["count"])
                                    yield tornado.gen.Task(pipe.execute)
                            self.set_status(204)
                        else:
                            self.set_status(404)
                            self.finish(json.dumps({'code': "FOOD_NOT_FOUND", 'message': u'食物不存在'}))
        c.disconnect()


class OrderHandler(UserAPIHandler):
    def data_received(self, chunk):
        pass

    @authenticate
    @gen.coroutine
    def get(self, *args, **kwargs):
        token = self.request.headers.get("token")
        c = tornadoredis.Client(connection_pool=db.REDIS_CONNECTION_POOL)
        user_id = yield gen.Task(c.zscore, 'user:token:list', token)
        c.disconnect()
        if user_id is None:
            self.set_status(401)
            self.finish(json.dumps({'code': "INVALID_ACCESS_TOKEN", 'message': u'无效的令牌'}))
        else:
            # 根据id
            order_item = yield db.POOL.execute(
                "SELECT order_id,total FROM `order` where user_id = '%s' limit 1" % user_id)
            order_item_id = order_item.fetchone()
            order_item.close()
            if order_item_id:
                order_item_item = yield db.POOL.execute(
                    "SELECT food_id,count FROM `order_item` where order_id = '%s'" % order_item_id["order_id"])
                order_item_items = order_item_item.fetchall()
                order_item_item.close()

                result = {'id': str(order_item_id["order_id"]), 'total': order_item_id["total"],
                          'items': order_item_items}
                result_list = (result,)
                self.set_status(200)
                self.finish(json.dumps(result_list))
            else:
                #
                self.set_status(200)
                self.finish(json.dumps([]))

    @authenticate
    @gen.coroutine
    def post(self, *args, **kwargs):
        if self.request.body is "":
            self.set_status(400)
            self.finish(json.dumps({'code': "EMPTY_REQUEST", 'message': u'请求体为空'}))
        token = self.request.headers.get("token")
        data = None
        c = tornadoredis.Client(connection_pool=db.REDIS_CONNECTION_POOL)
        user_id = yield gen.Task(c.zscore, 'user:token:list', token)
        if user_id is None:
            self.set_status(401)
            self.finish(json.dumps({'code': "INVALID_ACCESS_TOKEN", 'message': u'无效的令牌'}))
        else:
            try:
                data = tornado.escape.json_decode(self.request.body)
            except:
                self.set_status(400)
                self.finish(json.dumps({'code': "MALFORMED_JSON", 'message': u'格式错误'}))
            else:
                if data is None:
                    self.set_status(400)
                    self.finish(json.dumps({'code': "EMPTY_REQUEST", 'message': u'请求体为空'}))
                elif "cart_id" not in data.keys():
                    self.set_status(400)
                    self.finish(json.dumps({'code': "MALFORMED_JSON", 'message': u'格式错误'}))
                else:
                    ismember = yield gen.Task(c.sismember, 'cart:id', data["cart_id"])
                    if ismember == 0:
                        self.set_status(404)
                        self.finish(json.dumps({'code': "CART_NOT_FOUND", 'message': u'篮子不存在'}))
                    else:
                        isusercart = yield gen.Task(c.hget, "cart:%s" % data["cart_id"], "user_id")
                        if not (isusercart == str(user_id)):
                            self.set_status(401)
                            self.finish(json.dumps({'code': "NOT_AUTHORIZED_TO_ACCESS_CART", 'message': u'无权限访问指定的篮子'}))
                        cur = yield db.POOL.execute("SELECT * FROM `order` where user_id = '%d' limit 1" % user_id)
                        result = cur.fetchone()
                        cur.close()
                        if result:
                            self.set_status(403)
                            self.finish(json.dumps({'code': "ORDER_OUT_OF_LIMIT", 'message': u'每个用户只能下一单'}))
                        else:
                            with c.pipeline() as pipe:
                                pipe.hget("cart:%s" % data["cart_id"], "total")
                                pipe.hgetall("cart:%s" % data["cart_id"])
                                order = yield tornado.gen.Task(pipe.execute)
                            if order[0]:
                                order_id = None
                                del order[1]["total"]
                                del order[1]["user_id"]
                                del order[1]["total_items"]
                                for key in order[1]:
                                    food_item = yield db.POOL.execute(
                                        "SELECT stock FROM `food` where id = '%s' limit 1" % key)
                                    food_item_result = food_item.fetchone()
                                    if (int(food_item_result["stock"]) - int(order[1][key])) < 0:
                                        self.set_status(403)
                                        self.finish(json.dumps({'code': "FOOD_OUT_OF_STOCK", 'message': u'食物库存不足'}))
                                    else:
                                        cur = yield db.POOL.execute(
                                            "INSERT INTO `order` (user_id, total) VALUES (%d,%d)" % (user_id, int(order[0])))
                                        cur.close()
                                        order_item = yield db.POOL.execute(
                                            "SELECT order_id FROM `order` where user_id = '%s' limit 1" % user_id)
                                        order_item_id = order_item.fetchone()
                                        order_id = str(order_item_id["order_id"])
                                        order_item.close()
                                        order_item_item = yield db.POOL.execute(
                                            "INSERT INTO `order_item` (order_id, food_id, count) VALUES (%d,%d,%d)" % (
                                                int(order_item_id["order_id"]), int(key), int(order[1][key])))
                                        yield db.POOL.execute("UPDATE `food` SET stock = stock - %d where id = '%s'" % (
                                            int(order[1][key]), key))
                                        order_item_item.close()
                                    food_item.close()
                                if order_id is not None:
                                    self.set_status(200)
                                    self.finish(json.dumps({'id': order_id}))
                            else:
                                # 购物车无内容
                                self.set_status(200)
                                self.finish(json.dumps({'id': "3"}))
        c.disconnect()


class AdminOrderHandler(UserAPIHandler):
    def data_received(self, chunk):
        pass

    @authenticate
    @gen.coroutine
    def get(self, *args, **kwargs):
        token = self.request.headers.get("token")
        c = tornadoredis.Client(connection_pool=db.REDIS_CONNECTION_POOL)
        user_id = yield gen.Task(c.zscore, 'user:token:list', token)
        c.disconnect()
        if user_id is None:
            self.set_status(401)
            self.finish(json.dumps({'code': "INVALID_ACCESS_TOKEN", 'message': u'无效的令牌'}))
        else:
            # 根据id
            order_item = yield db.POOL.execute(
                "SELECT order_id,total,user_id FROM `order`")
            order_item_id = order_item.fetchall()
            order_item.close()
            result_list = []
            for key in order_item_id:
                order_item_item = yield db.POOL.execute(
                    "SELECT food_id,count FROM `order_item` where order_id = '%s'" % key["order_id"])
                order_item_items = order_item_item.fetchall()
                order_item_item.close()
                result = {'id': key["order_id"], 'user_id': key["user_id"], 'total': key["total"],
                          'items': order_item_items}
                result_list.append(result)
            self.set_status(200)
            self.finish(json.dumps(result_list))

