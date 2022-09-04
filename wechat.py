# 微信推送消息类
import http
import json
import sys
import urllib
from datetime import datetime, date
import random
from time import localtime, time

from requests import get, post

import cityinfo


def get_color():
    # 获取随机颜色
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)


def get_weather(province, city):
    # 城市id
    try:
        city_id = cityinfo.cityInfo[province][city]["AREAID"]
    except KeyError:
        print("推送消息失败，请检查省份或城市是否正确")
        sys.exit(1)
    # city_id = 101280101
    # 毫秒级时间戳
    t = (int(round(time() * 1000)))
    headers = {
        "Referer": "http://www.weather.com.cn/weather1d/{}.shtml".format(city_id),
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    url = "http://d1.weather.com.cn/dingzhi/{}.html?_={}".format(city_id, t)
    response = get(url, headers=headers)
    response.encoding = "utf-8"
    response_data = response.text.split(";")[0].split("=")[-1]
    response_json = eval(response_data)
    # print(response_json)
    weatherinfo = response_json["weatherinfo"]
    # 天气
    weather = weatherinfo["weather"]
    # 最高气温
    temp = weatherinfo["temp"]
    # 最低气温
    tempn = weatherinfo["tempn"]
    return weather, temp, tempn


def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    # 判断是否为农历生日
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        # 今年生日
        birthday = ZhDate(year, r_mouth, r_day).to_datetime().date()
        year_date = birthday


    else:
        # 获取国历生日的今年对应月和日
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
    # 计算生日年份，如果还没过，按当年减，如果过了需要+1
    if today > year_date:
        if birthday_year[0] == "r":
            # 获取农历明年生日的月和日
            r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
            birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
        else:
            birth_date = date((year + 1), birthday_month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day


class WeChat:
    config: map

    def __init__(self, config_pah):
        try:
            with open(config_pah, encoding="utf-8") as f:
                self.config = eval(f.read(), {"true": True, "false": False, "null": None})
        except FileNotFoundError:
            print("没有找到指定文件,请确认路径正确")
            sys.exit(1)
        except SyntaxError:
            print("请检查配置文件格式是否正确")
            sys.exit(1)

    def get_access_token(self):
        # appId

        app_id = self.config["app_id"]
        # appSecret
        app_secret = self.config["app_secret"]
        post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                    .format(app_id, app_secret))
        try:
            access_token = get(post_url).json()['access_token']
        except KeyError:
            print("获取access_token失败，请检查app_id和app_secret是否正确")
            sys.exit(1)
        return access_token

    # 词霸每日一句
    def get_ciba(self):
        if self.config["Whether_Eng"]:
            try:
                url = "http://open.iciba.com/dsapi/"
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
                }
                r = get(url, headers=headers)
                note_en = r.json()["content"]
                note_ch = r.json()["note"]
                return note_en, note_ch
            except:
                return "词霸API调取错误"

    def tip(self):
        if self.config["Whether_tip"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"], 'city': self.config["city"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/tianqi/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                pop = data["newslist"][0]["pop"]
                tips = data["newslist"][0]["tips"]
                return pop, tips
            except:
                return "天气预报API调取错误，请检查API是否正确申请或是否填写正确", ""

    # 励志名言
    def lizhi(self):
        if self.config["Whether_lizhi"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/lzmy/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                return data["newslist"][0]["saying"]
            except:
                return "励志古言API调取错误，请检查API是否正确申请或是否填写正确"

    #  情话
    def lover_prattle(self):
        if self.config["lovers_prattle"]:
            conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
            params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
            conn.request('POST', '/saylove/index', params, headers)
            res = conn.getresponse()
            data = res.read()
            data = json.loads(data)
            return data["newslist"][0]["content"]

    # 星座运势
    def lucky(self):
        if self.config["Whether_lucky"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"], 'astro': self.config["astro"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/star/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                data = "爱情指数：" + str(data["newslist"][1]["content"]) + "   工作指数：" + str(
                    data["newslist"][2]["content"]) + "\n今日概述：" + str(data["newslist"][8]["content"])
                return data
            except:
                return "星座运势API调取错误，请检查API是否正确申请或是否填写正确"

    # 健康小提示API
    def health(self):
        if self.config["Whether_health"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/healthtip/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                data = data["newslist"][0]["content"]
                return data
            except:
                return "健康小提示API调取错误，请检查API是否正确申请或是否填写正确"

    # 彩虹屁
    def caihongpi(self):
        if self.config["Whether_caihongpi"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/caihongpi/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                data = data["newslist"][0]["content"]
                if "XXX" in data:
                    data.replace("XXX", "宝贝")
                return data
            except:
                return "彩虹屁API调取错误，请检查API是否正确申请或是否填写正确"

    def send_message(self):
        access_token = self.get_access_token()
        pipi = self.caihongpi()
        lizhi = self.lizhi()
        # 下雨概率和建议
        pop, tips = self.tip()
        health_tip = self.health()
        lucky_ = self.lucky()
        weather, max_temperature, min_temperature = get_weather(self.config["province"], self.config["city"])
        note_ch, note_en = self.get_ciba()
        url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
        week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
        year = localtime().tm_year
        month = localtime().tm_mon
        day = localtime().tm_mday
        today = datetime.date(datetime(year=year, month=month, day=day))
        week = week_list[today.isoweekday() % 7]
        love = self.lover_prattle()
        # 获取在一起的日子的日期格式
        love_year = int(self.config["love_date"].split("-")[0])
        love_month = int(self.config["love_date"].split("-")[1])
        love_day = int(self.config["love_date"].split("-")[2])
        love_date = date(love_year, love_month, love_day)
        # 获取在一起的日期差
        love_days = str(today.__sub__(love_date)).split(" ")[0]
        # 获取所有生日数据
        birthdays = {}

        users = self.config["user"]
        for k, v in self.config.items():
            if k[0:5] == "birth":
                birthdays[k] = v

        for user in users:
            data = {
                "touser": user,
                "template_id": self.config["template_id"],
                "url": "http://weixin.qq.com/download",
                "topcolor": "#FF0000",
                "data": {
                    "date": {
                        "value": "{} {}".format(today, week),
                        "color": get_color()
                    },
                    "city": {
                        "value": self.config["city"],
                        "color": get_color()
                    },
                    "weather": {
                        "value": weather,
                        "color": get_color()
                    },
                    "min_temperature": {
                        "value": min_temperature,
                        "color": get_color()
                    },
                    "max_temperature": {
                        "value": max_temperature,
                        "color": get_color()
                    },
                    "love_day": {
                        "value": love_days,
                        "color": get_color()
                    },
                    "love": {
                        "value": love,
                        "color": get_color()
                    },
                    "note_ch": {
                        "value": note_ch,
                        "color": get_color()
                    },
                    "note_ch": {
                        "value": note_ch,
                        "color": get_color()
                    },

                    "pipi": {
                        "value": pipi,
                        "color": get_color()
                    },

                    "lucky": {
                        "value": lucky_,
                        "color": get_color()
                    },

                    "lizhi": {
                        "value": lizhi,
                        "color": get_color()
                    },

                    "pop": {
                        "value": pop,
                        "color": get_color()
                    },

                    "health": {
                        "value": health_tip,
                        "color": get_color()
                    },

                    "tips": {
                        "value": tips,
                        "color": get_color()
                    }
                }
            }
            for key, value in birthdays.items():
                # 获取距离下次生日的时间
                birth_day = get_birthday(value, year, today)
                # 将生日数据插入data
                data["data"][key] = {"value": birth_day, "color": get_color()}
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
            }
            response = post(url, headers=headers, json=data).json()
            if response["errcode"] == 40037:
                print("推送消息失败，请检查模板id是否正确")
            elif response["errcode"] == 40036:
                print("推送消息失败，请检查模板id是否为空")
            elif response["errcode"] == 40003:
                print("推送消息失败，请检查微信号是否正确")
            elif response["errcode"] == 0:
                print("推送消息成功")
            else:
                print(response)

    pass
