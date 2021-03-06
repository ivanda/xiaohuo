# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
from scrapy import Selector
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError
from datetime import datetime
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from xiaoshuo.items import XiaoshuoItem


class BiqugeSpider(scrapy.Spider):
    name = "biquge"
    # allowed_domains = ["www.biquge.com.tw"]
    start_urls = ['http://www.biquge.com.tw']
    global base_url
    base_url =  'http://www.biquge.com.tw'

    def parse(self, response):
        print response
        print 'parsing ', response.url
        sel = Selector(response)
        books = sel.xpath('//a')
        for index,bookSel in enumerate(books):
            # if (index == 2):
            #     break
            bookUrl = bookSel.xpath('@href').extract_first()
            if (bookUrl.find(base_url) != -1 and bookUrl[-1].find('/') != -1 and bookUrl.find(
                    '.html') == -1 and bookUrl.find(
                'img') == -1):
                tmpItem = XiaoshuoItem()
                tmpItem['book_url'] = bookSel.xpath('@href').extract_first()
                yield Request(tmpItem['book_url'], meta={'item': tmpItem},callback=self.parse_item, dont_filter=False,errback=self.errback_httpbin)
        pass

        # 内容详情 所有图片
    def parse_item(self, response):
        print 'item_url',response.url
        sel = Selector(response)

        #目录处理
        # item = response.meta['item']
        item = XiaoshuoItem();
        item['title'] = sel.xpath('//meta[@property="og:title"]/@content').extract_first()
        item['book_url'] = response.url
        item['chapters'] = []
        item['update_time'] = datetime.now()
        item['author'] = sel.xpath('//meta[@property="og:novel:author"]/@content').extract_first()
        item['book_name'] = sel.xpath('//meta[@property="og:novel:book_name"]/@content').extract_first()
        item['description'] = sel.xpath('//meta[@property="og:description"]/@content').extract_first()
        item['catalogue'] = sel.xpath('//meta[@property="og:novel:category"]/@content').extract_first()
        item['img'] = sel.xpath('//meta[@property="og:image"]/@content').extract_first()
        item['latest_chapter'] = {
            'chapter_name':sel.xpath('//meta[@property="og:novel:latest_chapter_name"]/@content').extract_first(),
            'chapter_url':sel.xpath('//meta[@property="og:novel:latest_chapter_url"]/@content').extract_first()
        }
        item['book_update_time'] = datetime.strptime(sel.xpath('//meta[@property="og:novel:update_time"]/@content').extract_first(), '%Y-%m-%d');
        status = sel.xpath('//meta[@property="og:novel:status"]/@content').extract_first()
        if(status.find('连载中')!=-1):
            item['is_complecated'] = False
        else:
            item['is_complecated'] = True
        chapters = sel.xpath('//dl/dd/a')
        for chapter in chapters:
            url = base_url+chapter.xpath('@href').extract_first()
            title  = chapter.xpath('text()').extract_first()
            item['chapters'].append({
                'chapter_name':title,
                'chapter_url':url
            })
        #继续添加新书
        books = sel.xpath('//a')
        for bookSel in books:
            book = bookSel.extract()
            bookUrl = bookSel.xpath('@href').extract_first()
            if ( bookUrl[-1].find('/') != -1 and bookUrl.find('.html') == -1 and bookUrl.find('img') == -1):
                # print book
                tmpItem = XiaoshuoItem()
                tmpItem['book_url'] = bookSel.xpath('@href').extract_first()
                if tmpItem['book_url'].find(base_url)==-1:
                    tmpItem['book_url'] = base_url+tmpItem['book_url']
                tmpItem['book_name'] = bookSel.xpath('text()').extract_first()
                yield Request(tmpItem['book_url'], meta={'item': tmpItem}, callback=self.parse_item, dont_filter=False,
                        errback=self.errback_httpbin)
        yield item


    #错误处理
    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            # you can get the response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)
        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
