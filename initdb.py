#!/usr/bin/env python
# coding=utf-8

from __future__ import print_function

from tornado import ioloop, gen
import tornado_mysql
__author__ = 'qingfeng'


@gen.coroutine
def main():
    conn = yield tornado_mysql.connect(host='127.0.0.1', port=3306, user='root', passwd='', db='mysql')
    cur = conn.cursor()
    yield cur.execute("DROP TABLE IF EXISTS `order`")
    # 创建数据表SQL语句
    sql = """CREATE TABLE `order` (
  `order_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned,
  `total` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
    yield cur.execute(sql)
    yield cur.execute("DROP TABLE IF EXISTS `order_item`")
    # 创建数据表SQL语句
    sql = """CREATE TABLE `order_item` (
  `order_item_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `order_id` int(10) unsigned,
  `food_id` int(10) unsigned NOT NULL DEFAULT '0',
  `count` int(10) NOT NULL DEFAULT '0',
  PRIMARY KEY (`order_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
    yield cur.execute(sql)
    cur.close()
    conn.close()

ioloop.IOLoop.current().run_sync(main)