# coding:utf-8
__author__ = 'xxj'

# 实现了异步重试机制，但是最后的一次异常的捕抓未实现

import time
import os
import lxml.etree
import logging
import aiohttp
import asyncio
import async_timeout
from aiohttp import ClientTimeout
from asyncio import TimeoutError
from gevent_requests.retry_xxj import retry

# URL_QUEUE = asyncio.Queue()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
}


semaphore = asyncio.Semaphore(100)


async def baidu_news(index_url):
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                # try:
                html = await baidu_news_request(session, index_url)
                # except TimeoutError as e:
                #     html = ''
                #     print(time.strftime('[%Y-%m-%d %H:%M:%S]'), 'TimeoutError')
                # except BaseException as e:
                #     html = ''
                #     print(time.strftime('[%Y-%m-%d %H:%M:%S]'), 'BaseException')
                return html


@retry(asyncio.TimeoutError)
async def baidu_news_request(session, index_url):
    print(time.strftime('[%Y-%m-%d %H:%M:%S]'), index_url)
    async with session.get(url=index_url, headers=headers, timeout=0.000000000001) as response:  # 在请求内部参数中加入请求超时时间
        html = await response.text()
        return html


async def baidu_news_parse(line_index_url, file_out):
    line = line_index_url[0]  # 关键词和热度值
    index_url = line_index_url[1]  # url
    html = await baidu_news(index_url)
    if html:
        res_obj = lxml.etree.HTML(html)
        sorry = res_obj.xpath('//div[@id="noresult"]')
        # if sorry:
        #     break
        item_list = res_obj.xpath('//div[@class="result"]')
        for item in item_list:
            title = item.xpath('./h3[@class="c-title"]/a')[0].xpath('string(.)').strip()  # 新闻标题
            link = item.xpath('./h3[@class="c-title"]/a/@href')[0]  # 新闻链接
            author_time = item.xpath('.//p[@class="c-author"]/text()')[0]
            author_time = author_time.split('\t\t\t\t\n\t\t\t\t\t\t')
            if len(author_time) == 1:
                author = author_time[0].strip()  # 新闻来源
                news_time = ''
            else:
                author = author_time[0].strip()  # 新闻来源
                news_time = author_time[1].strip()  # 新闻发布时间
            # 字段：新闻搜索关键词、url、新闻标题、新闻链接、新闻来源、新闻发布时间
            content_list = [line, index_url, title, link, author, news_time]
            content = '\t'.join(content_list)
            # CONTENT_QUEUE.put(content)
            file_out.write(content)
            file_out.write('\n')
            file_out.flush()


def main():
    print(time.strftime('[%Y-%m-%d %H:%M:%S]'), 'start')
    # file_path = r'E:\ENVS\py3.6\baidu_news\wzs_keyword_20181017_1.txt'
    file_path = r'E:\ENVS\py3.6\baidu_news\search_keyword_20181023_1.txt'
    file_path = r'F:\ENVS\py3.6\baidu_news\search_keyword_20181023_1.txt'
    print('源文件路径：', file_path)
    file_obj = open(file_path, 'r', encoding='utf-8')
    line_ls = [line.strip() for line in file_obj.readlines()]    # 源数据列表

    file_dest_path = os.path.join(os.getcwd(), 'baidu')    # 数据存储文件
    file_out = open(file_dest_path, 'a', encoding='utf-8')

    loop = asyncio.get_event_loop()
    url = 'http://news.baidu.com/ns?word={keyword}&pn={pn}&cl=2&ct=1&tn=news&rn=20&ie=utf-8&bt=0&et=0'
    index_url_ls = []
    for line in line_ls:
        keyword = line.split('\t')[0]    # 关键词
        for page in range(1):
            page *= 10
            index_url = url.format(keyword=keyword, pn=page)
            line_index_url = [line, index_url]
            index_url_ls.append(line_index_url)
    print('需要抓取的url量：', len(index_url_ls))
    tasks = [asyncio.ensure_future(baidu_news_parse(line_index_url, file_out)) for line_index_url in index_url_ls[0:5]]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

    file_out.flush()
    file_out.close()


if __name__ == '__main__':
    start_time = time.time()
    main()
    end_time = time.time()
    print('spend time:', end_time - start_time)