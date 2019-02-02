# -*- coding: utf-8 -*-
# 此程序用来抓取 的数据
import hashlib
import os

import requests
import time
import random
import re
from multiprocessing.dummy import Pool
import csv
import json
import sys
from fake_useragent import UserAgent, FakeUserAgentError
from selenium import webdriver


class Spider(object):
	def __init__(self):
		self.date = '2000-01-01'
		try:
			self.ua = UserAgent(use_cache_server=False).random
		except FakeUserAgentError:
			pass
	
	def get_headers(self):
		try:
			headers = {'host': "m.ac.qq.com",
					   'connection': "keep-alive",
					   'pragma': "no-cache",
					   'cache-control': "no-cache",
					   'user-agent': self.ua.chrome,
					   'accept': "*/*",
					   'referer': "http://m.ac.qq.com/comic/index/id/521825",
					   'accept-encoding': "gzip, deflate",
					   'accept-language': "zh-CN,zh;q=0.9"}
		except AttributeError:
			user_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0',
						   'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0',
						   'IBM WebExplorer /v0.94', 'Galaxy/1.0 [en] (Mac OS X 10.5.6; U; en)',
						   'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
						   'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
						   'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; TheWorld)',
						   'Opera/9.52 (Windows NT 5.0; U; en)',
						   'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.2pre) Gecko/2008071405 GranParadiso/3.0.2pre',
						   'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.458.0 Safari/534.3',
						   'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.4 Safari/532.0',
						   'Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.7.39 Version/11.00']
			user_agent = random.choice(user_agents)
			headers = {'host': "m.ac.qq.com",
					   'connection': "keep-alive",
					   'pragma': "no-cache",
					   'cache-control': "no-cache",
					   'user-agent': user_agent,
					   'accept': "*/*",
					   'referer': "http://m.ac.qq.com/comic/index/id/521825",
					   'accept-encoding': "gzip, deflate",
					   'accept-language': "zh-CN,zh;q=0.9"}
		return headers
	
	def p_time(self, stmp):  # 将时间戳转化为时间
		stmp = float(str(stmp)[:10])
		timeArray = time.localtime(stmp)
		otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
		return otherStyleTime

	def remove_emoji(self, text):
		emoji_pattern = re.compile(
			u"(\ud83d[\ude00-\ude4f])|"  # emoticons
			u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
			u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
			u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
			u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
			"+", flags=re.UNICODE)
		return emoji_pattern.sub(r'*', text)

	def replace(self, x):
		# 将其余标签剔除
		removeExtraTag = re.compile('<.*?>', re.S)
		x = re.sub(removeExtraTag, "", x)
		x = re.sub(re.compile('\s{3,}'), " ", x)
		x = re.sub(re.compile('[\n\r]'), " ", x)
		return x.strip()
	
	def GetProxies(self):
		# 代理服务器
		proxyHost = "http-dyn.abuyun.com"
		proxyPort = "9020"
		# 代理隧道验证信息
		proxyUser = "HI18001I69T86X6D"
		proxyPass = "D74721661025B57D"
		proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
			"host": proxyHost,
			"port": proxyPort,
			"user": proxyUser,
			"pass": proxyPass,
		}
		proxies = {
			"http": proxyMeta,
			"https": proxyMeta,
		}
		return proxies
	
	def get_comments(self, product_url, product_number, plat_number):  # 获取某个作品的所有评论
		pagenums = self.get_comments_total(product_url)
		print '总页数：',pagenums
		if pagenums:
			ss = []
			for page in range(1, pagenums + 1):
				ss.append([product_url, product_number, plat_number, page])
			pool = Pool(2)
			items = pool.map(self.get_comments_page, ss)
			pool.close()
			pool.join()
			mm = []
			for item in items:
				if item is not None:
					mm.extend(item)
			with open('new_data_comments.csv', 'a') as f:
				writer = csv.writer(f, lineterminator='\n')
				writer.writerows(mm)
		else:
			print '翻页结束！！！'
	
	def get_comments_total(self, product_url):  # 获取某个作品评论的总页数
		p0 = re.compile('id/(\d+)')
		product_id = ''.join(re.findall(p0, product_url))
		print 'product_id:',product_id
		url = 'http://m.ac.qq.com/comment/getCommentList/id/%s?t=1540514358186&page=1&pageSize=10' % product_id
		retry = 5
		while 1:
			try:
				text = requests.get(url, headers=self.get_headers(), timeout=10).json()
				time.sleep(0.2)
				total = str(text['data']['totalNum'])
				total = int(total)
				if total % 10 == 0:
					pagenums = total / 10
				else:
					pagenums = total / 10 + 1
				return int(pagenums)
			except Exception as e:
				retry -= 1
				if retry == 0:
					print '1',e
					return None
				else:
					continue
	
	def get_comments_page(self, ss):  # 获取某个作品每一页的评论
		product_url, product_number, plat_number, page = ss
		print '爬取页数：', page
		p0 = re.compile('id/(\d+)')
		base_url = re.findall(p0, product_url)[0]
		url = 'http://m.ac.qq.com/comment/getCommentList/id/%s?t=1540514358186&page=%d&pageSize=10' % (base_url, page)
		retry = 5
		while 1:
			try:
				text = requests.get(url, headers=self.get_headers(), proxies=self.GetProxies(), timeout=10).json()
				# print text
				time.sleep(0.2)
				items = text['data']['commentList']
				last_modify_date = self.p_time(time.time())
				results = []
				for item in items:
					nick_name = item.get('nick_name', '')
					nick_name = self.remove_emoji(nick_name)
					cmt_time = self.p_time(item['pub_time'])
					cmt_date = cmt_time.split()[0]
					if '-' not in cmt_date:
						continue
					if cmt_date < self.date:
						continue
					comments = self.replace(item['content'])
					comments = self.remove_emoji(comments)
					like_cnt = str(item['good'])
					cmt_reply_cnt = '0'
					long_comment = '0'
					src_url = product_url
					tmp = [product_number, plat_number, nick_name, cmt_date, cmt_time, comments, like_cnt,
					       cmt_reply_cnt, long_comment, last_modify_date, src_url]
					print '|'.join(tmp)
					results.append([x.encode('gbk', 'ignore') for x in tmp])
				return results
			except Exception as e:
				retry -= 1
				if retry == 0:
					print '2',e
					return None
				else:
					continue


if __name__ == "__main__":
	spider = Spider()
	ss = []
	with open('new_data.csv') as f:
		tmp = csv.reader(f)
		for i in tmp:
			if 'http' in i[2]:
				ss.append([i[0], i[2],  'P12'])
	for s in ss:
		print s[0],s[1]
		spider.get_comments(s[1], s[0], s[2])
