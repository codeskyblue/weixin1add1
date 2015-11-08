#!/usr/bin/env python
# coding: utf-8
import os
import flask
from flask import request, Flask
from wechat_sdk import WechatBasic


TOKEN = os.environ.get('TOKEN', 'abcd4321')
app = Flask(__name__)
wechat = WechatBasic(token=TOKEN)

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
	print request.data
	wechat.parse_data(request.data)
	message = wechat.get_message()
	response = wechat.response_text(u'^_^')
	print response
	return response

@app.route('/', methods=['GET', 'POST'])
def homepage():
    print request.data
    return 'good'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
