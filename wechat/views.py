#-*- coding:utf-8 -*-

#导入所需包
import json, requests, traceback, urllib
from urllib.request import urlopen

from django.http.response import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from wechat_sdk import WechatConf
from wechat_sdk import WechatBasic
from wechat_sdk.exceptions import ParseError
from wechat_sdk.messages import (TextMessage, VoiceMessage, ImageMessage, VideoMessage,
                                 LinkMessage,LocationMessage, EventMessage, ShortVideoMessage)


#微信服务器初始化
conf = WechatConf(
   token='*************',
   appid='******************',
   appsecret='***************************',
   encrypt_mode='normal',
   encoding_aes_key='**********************************'
)

#图灵key和接口
tuling_key='**********************'
tuling_url='*****************************'

#图灵自动回复类
class TuLingAutoReply():
    def __init__(self, tuling_key, tuling_url):
        self.key = tuling_key
        self.url = tuling_url

    def reply(self, unicode_str):
        body = {'key': self.key, 'info': unicode_str.encode('utf-8')}
        r = requests.post(self.url, data=body)
        r.encoding = 'utf-8'
        resp = r.text
        if resp is None or len(resp) == 0:
            return None
        try:
            js = json.loads(resp)
            if js['code'] == 100000:
                return js['text'].replace('','')
            elif js['code'] == 200000:
                return js['url']
            else:
                return None
        except Exception:
            traceback.print_exc()
            return None

auto_reply = TuLingAutoReply(tuling_key, tuling_url)

#微信主要配置
@csrf_exempt
def wechat_home(request):
   signature = request.GET.get('signature')
   timestamp = request.GET.get('timestamp')
   nonce = request.GET.get('nonce')
   wechat_instance = WechatBasic(conf=conf)
   if not wechat_instance.check_signature(signature=signature, timestamp=timestamp, nonce=nonce):
       return HttpResponseBadRequest('Verify Failed')
   else:
       if request.method == 'GET':
           response = request.GET.get('echostr', 'error')
       else:
           try:
               wechat_instance.parse_data(request.body)
               message = wechat_instance.get_message()
               if isinstance(message, TextMessage):
                   content = message.content
                   if content == "音乐":
                       m = reply_music("喜欢你")
                       reply_text = ('<a href="%s">%s-%s1</a>' % (m[3], m[1], m[2]))
                   elif content[:2] == "音乐":
                       m = reply_music(content[2:])
                       reply_text = ('<a href="%s">%s-%s2</a>' % (m[3], m[1], m[2]))
                   elif content == "新闻":
                       # reply_text = "今日新闻"
                       reply_text = [{
                            'title': u'第一条新闻标题',
                            'description': u'第一条新闻描述，这条新闻没有预览图',
                            'url': u'http://www.google.com.hk/',
                        }, {
                            'title': u'第二条新闻标题, 这条新闻无描述',
                            'picurl': u'http://doraemonext.oss-cn-hangzhou.aliyuncs.com/test/wechat-test.jpg',
                            'url': u'http://www.github.com/',
                        }, {
                            'title': u'第三条新闻标题',
                            'description': u'第三条新闻描述',
                            'picurl': u'http://doraemonext.oss-cn-hangzhou.aliyuncs.com/test/wechat-test.jpg',
                            'url': u'http://www.v2ex.com/',
                        }]
                       response = wechat_instance.response_news(articles=reply_text)
                       return HttpResponse(response, content_type="application/xml")
                   else:
                       reply_text = auto_reply.reply(content)
               elif isinstance(message, VoiceMessage):
                    content = message.recognition
                    if content == "音乐":
                        m = reply_music("喜欢你")
                        reply_text = ('<a href="%s">%s-%s1</a>' % (m[3], m[1], m[2]))
                    elif content[:2] == "音乐":
                        m = reply_music(content[2:])
                        reply_text = ('<a href="%s">%s-%s2</a>' % (m[3], m[1], m[2]))
                    else:
                        reply_text = auto_reply.reply(content)
               elif isinstance(message, ImageMessage):
                   reply_text = "image 图片"#带中文就要用双引号，无语
               elif isinstance(message, LinkMessage):
                   reply_text = 'link'
               elif isinstance(message, LocationMessage):
                   reply_text = 'location'
               elif isinstance(message, VideoMessage):
                   reply_text = 'video'
               elif isinstance(message, ShortVideoMessage):
                   reply_text = 'shortvideo'
               else:
                   reply_text = 'other'
               response = wechat_instance.response_text(content=reply_text)
           except ParseError:
               return HttpResponseBadRequest('Invalid XML Data')
       return HttpResponse(response, content_type="application/xml")

#返回网易云音乐方法
def reply_music(song):
    #url中的中文要用urllib.parse.quote单独处理,replace(' ','')则是去除所有空格
    song = urllib.parse.quote(song.replace(' ',''))
    html = urlopen('http://s.music.163.com/search/get/?type=1&s=%s' % song)
    js = json.loads(html.read().decode('utf-8'))
    list = js['result']['songs'][0]
    music_url = list['audio']
    title = list['name']
    name = list['artists'][0]['name']
    page = list['page']
    return (music_url, title, name, page)


