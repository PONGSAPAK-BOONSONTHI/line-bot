import json
from flask import Flask, request, abort, send_from_directory
from flask_lt import run_with_lt

import rospy
from sensor_msgs.msg import CompressedImage
from cira_msgs.srv import CiraFlowService, CiraFlowServiceRequest

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, StickerMessage, StickerSendMessage, ImageMessage, ImageSendMessage, responses
)

import signal
 
def handler(signum, frame):
    exit(1)
 
signal.signal(signal.SIGINT, handler)

# config
token = '<UgtrcaohowB40LBBJxhoYfV3S+qYFylZ+BAmSYBfRxP6LQx7ysPo8ANr8LGvEGxtX1FYmyLqvzpe11DccZsRzgw0Dspru/7N83Yw41RUPapMD5Gjd+fYELO0hHJDVmGbt6khqClCb+mPg2jP2Vm+qgdB04t89/1O/w1cDnyilFU=>'
secret = '<da6bb5d91d28cbf6875abb8e8673aad4>'
subdomain = 'example-line-bot-1234'
serviceName = "line"
port = 3000
ros_node_name = "line_bot"
########

app = Flask(__name__)
app.config['2cpEcprcKsINuKkn0p5tYIdWspn_4GCferfajAH6bfqFywFHo'] = {'ping_interval': 25}
run_with_lt(app, subdomain)

line_bot_api = LineBotApi(token) # long_live token
handler = WebhookHandler(secret) # secret

rospy.init_node(ros_node_name, anonymous=True)
# print(f"wait for service [{serviceName}]")
rospy.wait_for_service(serviceName)
ciraService = rospy.ServiceProxy(serviceName, CiraFlowService)

@app.route("/")
def index():
    return 'Success'

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@app.route('/images/<path:path>')
def send_image(path):
    return send_from_directory('images', path)

@handler.add(MessageEvent, message=TextMessage)
# def handle_message(event: MessageEvent):
#     msg: TextMessage = event.message
#     req = CiraFlowServiceRequest()
#     req.flow_in.jsonstr = json.dumps({'msg': msg.text, 'have_image': False})
#     res = ciraService.call(req)
#     jso = json.loads(res.flow_out.jsonstr)
#     text = jso['payload'].get('line_message')
#     if text is not None:
#         line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))
        
def handle_message(event):
    msg = event.message
    req = CiraFlowServiceRequest()
    req.flow_in.jsonstr = json.dumps({'msg': msg.text, 'have_image': False})
    res = ciraService.call(req)
    jso = json.loads(res.flow_out.jsonstr)
    text = jso['payload'].get('line_message')
    if text is not None:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))


@handler.add(MessageEvent, message=ImageMessage)
def handle_message(event):
    msg = event.message
    content = line_bot_api.get_message_content(msg.id)
    req = CiraFlowServiceRequest()
    req.flow_in.jsonstr = json.dumps({'have_image': True})
    cm = CompressedImage()
    cm.format = "jpg"
    for chunk in content.iter_content():
        cm.data += chunk
    req.flow_in.img = cm
    res = ciraService.call(req)
    jso = json.loads(res.flow_out.jsonstr)
    img_name = jso['payload']['img_name']
    img_url = "https://{}.loca.lt/images/{}".format(subdomain, img_name)
    line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=img_url, preview_image_url=img_url))
    if event.source.type == "group":
        line_bot_api.push_message(event.source.group_id, TextSendMessage(text=jso['payload']['name']))
    if event.source.type == "user":
        line_bot_api.push_message(event.source.user_id, TextSendMessage(text=jso['payload']['name']))

    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
