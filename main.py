#!/usr/bin/env python
# coding: utf-8
import os
import flask
from flask import request, Flask, g
from wechat_sdk import WechatBasic
import datetime
import random
import bunch
from models import *

TOKEN = os.environ.get('TOKEN', 'abcd4321')
app = Flask(__name__)
wechat = WechatBasic(token=TOKEN)

LEVEL_NEED_PASS = 10
LEVEL_MAX_RETRY = 3


RES_RIGHT = 1
RES_WRONG = 2
RES_TLE_PASS = 3
# RES_TLE_FAIL = 4
RES_WRONG_OVERFLOW = 5
RES_UPGRADE = 6

@app.before_request
def before_request():
    g.db = db
    g.db.connect()

@app.after_request
def after_request(response):
    if hasattr(g, 'db'):
        if not g.db.is_closed():
            g.db.close()
    return response

@app.route('/weixin_hook')
def weixin_hook():
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    echostr = request.args.get('echostr')
    if not wechat.check_signature(signature=signature, timestamp=timestamp, nonce=nonce) and 0:
        return 'no pass signature'
    return echostr


@app.route('/weixin_hook', methods=['POST'])
def weixin_hook_message():
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')

    # print request.data
    wechat.parse_data(request.data)
    message = wechat.get_message()

    user, created = User.get_or_create(id=message.source)
    # if created:
    #   return wechat.response_text(u'欢迎')

    body = message.content.strip()
    print '接收到的内容:', body

    if body == u'help' or body == 'h' or body == u'帮助':
        return wechat.response_text(wechat_help())
    if body == 'top' or body == 't' or body == u'排名':
        return wechat.response_text(top(user.id))
    if body == 'show' or body == 's' or body == u'查看':
        return wechat.response_text(show(user))

    if body.isdigit():
        return wechat.response_text(
            question_answer(user, int(body)))

    response = wechat.response_text(u'新来的吧,输入"帮助" 查看指引吧, 输入1开始游戏')
    return response

def level_info(level):
    lvs = [
        dict(name='渣渣', number_min=1, number_max=5, time_limit=10),
        dict(name='青铜', number_min=5, number_max=10, time_limit=15),
        dict(name='白银1', number_min=10, number_max=50, time_limit=10),
        dict(name='白银2', number_min=10, number_max=50, time_limit=10),
        dict(name='黄金1', number_min=50, number_max=100, time_limit=10),
        dict(name='黄金2', number_min=100, number_max=500, time_limit=15),
        dict(name='黄金3', number_min=500, number_max=999, time_limit=15),
        dict(name='黄金4', number_min=500, number_max=999, time_limit=10),
        dict(name='钻石1', number_min=1000, number_max=5000, time_limit=15),
        dict(name='钻石2', number_min=5000, number_max=9999, time_limit=10),
        dict(name='钻石3', number_min=10000, number_max=50000, time_limit=10),
        dict(name='钻石4', number_min=50000, number_max=99999, time_limit=10)
    ]

    if level < len(lvs):
        info = lvs[level]
    else:
        number_min=10**level
        number_max=10**(level+1)-1
        info = dict(name='王者', number_min=number_min, number_max=number_max, time_limit=15)
    return bunch.bunchify(info)


def wechat_help():
    return u'''这是一个限时计算的游戏

常用指令:
1: 开始
[help|h|帮助]: 显示帮助内容
[show|s|查看]: 查看当前等级信息
[top|t|排名]: 查看排名信息'''

def check_answer(user, result):
    ''' return RES_* '''

    duration = datetime.datetime.now() - user.update_time
    print datetime.datetime.now()
    print user.update_time
    linfo = level_info(user.level)
    time_limit_err = (duration.total_seconds() >= linfo.time_limit)
    print duration.total_seconds(), 'TLE:', time_limit_err

    user.update_time = datetime.datetime.now()
    user.save()

    # time_limit_err = False

    is_res_ok = False
    if user.a + user.b == result:
        is_res_ok = True

    if is_res_ok:
        next_question(user)
        print 'NEXT QUES'
        if not time_limit_err:
            user.good_count += 1
        else:
            user.fail_count += 1
        user.save()
    else:
        user.fail_count += 1
        user.save()

    if user.good_count >= LEVEL_NEED_PASS:
        user.level += 1
        user.save()
        return RES_UPGRADE

    if user.fail_count >= LEVEL_MAX_RETRY:
        reset_level(user)
        return RES_WRONG_OVERFLOW

    if is_res_ok:
        if not time_limit_err:
            return RES_RIGHT
        else:
            return RES_TLE_PASS

    return RES_WRONG

def reset_level(user):
    user.good_count = 0
    user.fail_count = 0
    user.save()

def next_question(user):
    lv = level_info(user.level)
    user.a = random.randint(lv.number_min, lv.number_max) #10**base, 10**(base+1)-1)
    user.b = random.randint(lv.number_min, lv.number_max)
    # user.b = random.randint(10**base, 10**(base+1)-1)
    user.update_time = datetime.datetime.now() + datetime.timedelta(seconds=0.5)
    print 'UPP:', user.update_time
    user.save()
    if user.a + user.b == 1:
        next_question(user)


def question_answer(user, res):
    lv = level_info(user.level)
    update_time = user.update_time
    if res == 1:
        reset_level(user)
        next_question(user)
        return '\n'.join([
                u'准备好了吗',
                u'当前等级 {level}'.format(level=user.level), 
                u'距离升级还有 {} 题'.format(LEVEL_NEED_PASS-user.good_count),
                u'剩余失败次数 {}'.format(LEVEL_MAX_RETRY-user.fail_count),
                u'限时 {}s'.format(lv.time_limit),
                u'Question: {a} + {b} = ?'.format(a=user.a, b=user.b)
            ])

    ret = check_answer(user, res)
    if ret == RES_RIGHT:
        return '\n'.join([
                u'回答正确',
                u'当前等级 {level}'.format(level=user.level), 
                u'距离升级还有 {} 题'.format(LEVEL_NEED_PASS-user.good_count),
                u'剩余失败次数 {}'.format(LEVEL_MAX_RETRY-user.fail_count),
                u'限时 {}s'.format(lv.time_limit),
                u'下一题: {a} + {b} = ?'.format(a=user.a, b=user.b)
            ])
    elif ret == RES_WRONG:
        return '\n'.join([
                u'回答错误',
                u'当前等级 {level}'.format(level=user.level), 
                u'距离升级还有 {} 题'.format(LEVEL_NEED_PASS-user.good_count),
                u'剩余失败次数 {}'.format(LEVEL_MAX_RETRY-user.fail_count),
                u'再来一次: {a} + {b} = ?'.format(a=user.a, b=user.b)
            ])
    elif ret == RES_UPGRADE:
        if user.level > 12:
            return '\n'.join([
                u'恭喜能通关了',
                u'联系作者 codeskyblue@gmail.com 获取神秘礼品',
                u'该信息只显示一次',
            ])  
        return '\n'.join([
                u'回答正确',
                u'恭喜您顺利晋级(最高级12级)',
                u'当前等级 {}'.format(user.level),
                u'输入 1, 继续闯关'
            ])
    elif ret == RES_TLE_PASS:
        return '\n'.join([
                u'回答超时',
                u'用时 {:.2f}s'.format((datetime.datetime.now()-update_time).total_seconds()),
                u'当前等级 {}'.format(user.level),
                u'距离升级还有 {} 题'.format(LEVEL_NEED_PASS-user.good_count),
                u'剩余失败次数 {}'.format(LEVEL_MAX_RETRY-user.fail_count),
                u'限时 {}s'.format(lv.time_limit),
                u'下一题: {a} + {b} = ?'.format(a=user.a, b=user.b)
            ])
    elif ret == RES_WRONG_OVERFLOW:
        return '\n'.join([
                u'失败太多, 挑战已重置',
                u'当前等级 {}'.format(user.level),
                u'输入1 重新开始'
            ])

def show(user):
    lv = level_info(user.level)
    return '\n'.join([
        '等级 {}'.format(user.level),
        # '称号 {}'.format(linfo.name)
    ])

def top(user_id):
    res = []
    for user in User.select().order_by(User.level.desc()).limit(10):
        # user.nickname
        if user_id == user.id:
            nickname = u'我自己'
        else:
            nickname = str(user.id)[-5:]

        res.append(u'{} 等级 {}'.format(
            nickname, user.level))
    return '\n'.join(res)


@app.route('/', methods=['GET', 'POST'])
def homepage():
    print request.data
    return 'good'


@app.route('/api/tops')
def api_top():
    res = []
    for user in User.select().order_by(User.level.desc()).limit(10):
        res.append(user.to_json())
    return res

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
