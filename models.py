#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx
# Created: 2015-011-08

import os
import json
import datetime
from peewee import *
from playhouse.db_url import connect
from playhouse.shortcuts import *

# database connect-url
# ref: https://peewee.readthedocs.org/en/latest/peewee/playhouse.html#db-url
# - sqlite:///test.db
# - mysql://user:passwd@ip:port/dbname
_dburl = os.getenv('DB_URL', 'mysql://wechat:wechat@localhost:3306/wechat?charset=utf8')
db = connect(_dburl)


class JSONField(Field):
    db_field = 'text'

    def coerce(self, value):
        return json.loads(value)

    def db_value(self, value):
        return value if value is None else json.dumps(value)

def _jsonify(v):
    if isinstance(v, datetime.datetime):
        return str(v)
    return v

def _tojson(v):
    return json.loads(json.dumps(v, default=_jsonify))

class BaseModel(Model):
    class Meta:
        database = db

    def to_dict(self):
        return self._data

    def to_json(self):
        return _tojson(model_to_dict(self, False))

# class Question(BaseModel):
# 	param_a = CharField(default='')
# 	param_b = CharField(default='')
# 	operation = CharField(default='+')

class User(BaseModel):
    id = CharField(primary_key=True)
    level = IntegerField(default=0)

    a = IntegerField(default=0)
    b = IntegerField(default=0)

    good_count = IntegerField(default=0)
    fail_count = IntegerField(default=0)
    create_time = DateTimeField(default=datetime.datetime.now)
    update_time = DateTimeField(default=datetime.datetime.now)
    
    admin = BooleanField(default=False)
    username = CharField(default='')
    

def create_tables():
    db.create_tables([User], safe=True)

if __name__ == '__main__':
	create_tables()