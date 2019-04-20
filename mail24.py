#encoding: utf-8
"""使用类10分钟邮箱 24mail.chacuo.net 接收邮件

Examples:
    >>> client = EmailClient()
    >>> client.name
    a1234567890
    >>> client.address
    a1234567890@chacuo.net
    >>> client.receive()
    [<mail24.EmailDataObject abcabc from foo@bar.com>]

    >>> client = EmailClient("abcabcabc1", "test_")
    >>> client.name
    test_abcabcabc1
    >>> client.address
    test_abcabcabc1@chacuo.net
    >>> client.receive()
    []
"""

import datetime
import re
from urllib.parse import urlencode

import random
import string

import requests

__all__ = ["EmailClient", "EmailDataObject"]

__author__ = "Lam.Xavier@hotmail.com"

class EmailDataObject(object):
    """邮件对象

    Attributes:
        subject (str): 邮件主题
        sendtime (datetime.datetime): 发送时间
        to_name (str): 发送者
        to_addr (str): 发送者地址
        from_name (str): 接收者
        from_addr (str): 接收者地址
        content (str): 邮件内容
        isread (bool): False未读
    """

    def __init__(self, obj, client=None):
        self.obj = obj
        self.subject = obj["SUBJECT"]
        self.sendtime = self.strptime(obj["SENDTIME"])
        self.to_name, self.to_addr = self.email_name(obj["TO"])
        self.from_name, self.from_addr = self.email_name(obj["FROM"])
        self.isread = obj["ISREAD"] != 0
        self._id = obj["MID"]
        self._content = obj.get("CONTENT")
        self._client = client

    @property
    def content(self):
        if not self._content and self._client:
            self.obj["CONTENT"] = self._content = \
                self._client.req_api("mailinfo", dict(f=self._id))[1][0]["DATA"][0]
        return self._content

    def email_name(self, name):
        match = re.search("^(.*)<(.+)>$", name)
        name, addr = match.group(1), match.group(2)
        return name or addr, addr

    def strptime(self, string):
        return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

    def __str__(self):
        return "%(subject)s - %(from_name)s<%(from_addr)s> %(sendtime)s"%dict(
            subject=self.subject,
            from_name=self.from_name,
            from_addr=self.from_addr,
            sendtime=self.sendtime
        )

    def __repr__(self):
        return "<%(classname)s %(subject)s from %(address)s>"%dict(
            classname=self.__module__ + "." + self.__class__.__name__,
            subject=self.subject,
            address=self.from_addr
        )

class EmailClient(object):
    """基于24mail.chacuo.net的一个邮件接收类

    Args:
        name (:obj:`str`, optional): 邮箱名,默认值是一个11位的随机字符串
        prefix (:obj:`str`, optional): 邮箱名前缀,默认值空串
        subfix (:obj:`str`, optional): 邮箱域名,默认chacuo.net
            请填写24mail.chacuo.net支持的域名,暂不支持自己cname解析的域名
        session (:obj:`requests.Session`, optional): 会话对象,默认新建一个会话对象
    """

    base_url = "http://24mail.chacuo.net/"

    def __init__(self, name="", prefix="", subfix="chacuo.net", session=None):
        self.session = session or requests.session()
        self._name = prefix + (name or self.random_name)
        self.subfix = subfix
        self.session.get(self.base_url)
        # 可能发生设置的name没有生效的情况 待处理
        self.req_api("set", dict(d=self.subfix))

    # def __del__(self):
    #     self.req_api("renew", dict(d=self.subfix))

    def receive(self):
        """接收邮件

        Returns:
            :obj:`list` of :obj:`EmailDataObject`: 邮件列表
        """
        data = self.req_api()
        return list(map(lambda o: EmailDataObject(o, self), data.get("list")))

    def req_api(self, type="refresh", arg=None):
        resp = self.session.post(self.base_url, dict(
            data=self.name,
            type=type,
            arg=urlencode(arg or dict()).replace("&", "_")
        ))
        return resp.json().get("data").pop()

    @property
    def name(self):
        """str: 邮箱名"""
        return self._name
    
    @property
    def address(self):
        """str: 完整邮箱地址"""
        return self.name + "@" + self.subfix

    @property
    def random_name(self):
        return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(11))

    def __str__(self):
        return self.address

    def __repr__(self):
        return "<%(classname)s %(address)s>"%dict(
            classname=self.__module__ + "." + self.__class__.__name__,
            address=self.address
        )
