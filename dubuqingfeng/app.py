#!/usr/bin/env python
# coding=utf-8
import os
import tornado.ioloop
import tornado.web
from handlers import index
from handlers import login
from setting import settings

__author__ = 'qingfeng'


def make_app():
    return tornado.web.Application(
        handlers=[
            (r"/", index.IndexHandler),
            (r"/login", login.LoginHandler),
            (r"/foods", index.FoodsHandler),
            (r"/carts", index.CreateCartHandler),
            (r"/carts/(.*)", index.CartHandler),
            (r"/orders", index.OrderHandler),
            (r"/admin/orders", index.AdminOrderHandler)
        ],
        **settings
    )


if __name__ == '__main__':
    app = make_app()
    app.listen(port=int(os.getenv("APP_PORT", "8080")), address=os.getenv("APP_HOST", "0.0.0.0"))
    tornado.ioloop.IOLoop.current().start()
