#!/usr/bin/env python
# coding=utf-8

from __future__ import print_function
import os

from tornado import ioloop, gen
import tornado_mysql
__author__ = 'qingfeng'


@gen.coroutine
def main():
    conn = yield tornado_mysql.connect(host=os.getenv("DB_HOST", "localhost"), port=int(os.getenv("DB_PORT", "3306")),
         user=os.getenv("DB_USER", "root"), passwd=os.getenv("DB_PASS", "toor"),
         db=os.getenv("DB_NAME", "eleme"))
    cur = conn.cursor()
    # 创建数据表SQL语句
    sql = """CREATE TABLE `order` IF EXISTS `order` (
  `order_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned,
  `total` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
    yield cur.execute(sql)
    # 创建数据表SQL语句
    sql = """CREATE TABLE `order_item` IF NOT EXISTS `order_item` (
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