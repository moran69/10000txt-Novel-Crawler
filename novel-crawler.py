# 导入所需的所有模块
import requests  # 用于发送HTTP请求
from bs4 import BeautifulSoup  # 用于解析HTML
import re  # 用于正则表达式处理
import time  # 用于时间操作
import random  # 用于生成随机数
from concurrent.futures import ThreadPoolExecutor  # 用于并发操作
import threading  # 用于线程管理
import queue  # 用于队列管理
import logging  # 用于日志记录
import json  # 用于JSON处理
from typing import List, Dict, Optional  # 用于类型注解

# config.py
"""
配置文件，包含爬虫的所有配置参数
"""

# 基础配置
BASE_URL = "https://www.10000txt.com"  # 网站的基础URL
BATCH_SIZE = 20  # 每批处理的页面数
MAX_WORKERS = 5  # 最大并发线程数
REQUEST_TIMEOUT = 10  # 请求超时时间（秒）
RETRY_DELAY = 30  # 请求失败后重试的延迟时间（秒）
MAX_RETRIES = 3  # 请求失败的最大重试次数

# 小说分类配置
CATEGORIES = {
    "都市异能": {"id": 1, "total_pages": 158},
    "奇幻玄幻": {"id": 2, "total_pages": 178},
    "武侠仙侠": {"id": 3, "total_pages": 91},
    "科幻游戏": {"id": 4, "total_pages": 93},
    "惊悚灵异": {"id": 5, "total_pages": 41},
    "历史军事": {"id": 6, "total_pages": 86}
}

# 日志配置
LOG_CONFIG = {
    "level": logging.INFO,  # 设置日志级别为INFO
    "format": "%(asctime)s - %(levelname)s - %(message)s",  # 设置日志格式
    "handlers": [
        logging.FileHandler("crawler.log", encoding="utf-8"),  # 将日志保存到文件
        logging.StreamHandler()  # 同时输出到控制台
    ]
}

class SessionManager:
    """
    会话管理器类，用于处理HTTP请求，保证会话持续性，并设置请求头
    """
    def __init__(self):
        # 创建一个会话对象
        self.session = requests.Session()
        # 设置请求头
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def get(self, url: str, timeout: int = REQUEST_TIMEOUT) -> requests.Response:
        """
        发送GET请求并返回响应
        :param url: 请求的URL
        :param timeout: 请求的超时时间
        :return: 响应对象
        """
        try:
            # 发送GET请求
            response = self.session.get(url, timeout=timeout)
            # 如果响应状态码不是200，则抛出异常
            response.raise_for_status()
            time.sleep(2 + random.uniform(1, 3))  # 随机等待2到5秒，模拟人为操作
            return response
        except requests.RequestException as e:
            logging.error(f"请求失败: {url} - {str(e)}")  # 请求失败时记录日志
            raise

class BookInfo:
    """
    图书信息类，用于存储图书的基本信息
    """
    def __init__(self, title: str, original_url: str, download_url: str = None, 
                 page_number: int = 0, index: int = 0):
        self.title = title  # 图书标题
        self.original_url = original_url  # 图书原始页面URL
        self.download_url = download_url  # 图书下载链接
        self.page_number = page_number  # 页码
        self.index = index  # 图书在页面中的索引

class Storage:
    """
    存储类，用于保存图书信息、下载链接以及错误信息
    """
    def __init__(self, category: str):
        self.category = category  # 分类
        self.file_lock = threading.Lock()  # 文件锁，保证文件写入的线程安全
        self.links_file = f"{category}_links.txt"  # 保存图书链接的文件
        self.download_file = f"{category}_download_links.txt"  # 保存下载链接的文件
        self.error_file = f"{category}_error_links.json"  # 保存错误信息的文件

    def save_links(self, books: List[BookInfo]):
        """
        保存图书链接到文件
        :param books: 图书信息列表
        """
        with self.file_lock:
            with open(self.links_file, "a", encoding="utf-8") as f:
                for book in books:
                    f.write(f"第 {book.page_number} 页 第 {book.index} 个: 《{book.title}》 - {book.original_url}\n")

    def save_download_link(self, book: BookInfo):
        """
        保存图书下载链接到文件
        :param book: 图书信息对象
        """
        with self.file_lock:
            with open(self.download_file, "a", encoding="utf-8") as f:
                f.write(f"第 {book.page_number} 页 第 {book.index} 个: 《{book.title}》 - "
                       f"原始链接: {book.original_url} - 下载链接: {book.download_url}\n")

    def save_error(self, book: BookInfo, error_msg: str):
        """
        保存图书错误信息到文件
        :param book: 图书信息对象
        :param error_msg: 错误信息
        """
        error_data = {
            "book_info": f"第 {book.page_number} 页 第 {book.index} 个: 《{book.title}》",
            "url": book.original_url,
            "error_msg": str(error_msg),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")  # 错误发生时间
        }
        with self.file_lock:
            try:
                with open(self.error_file, "r", encoding="utf-8") as f:
                    errors = json.load(f)  # 如果文件存在，则读取现有错误记录
            except (FileNotFoundError, json.JSONDecodeError):
                errors = []  # 如果文件不存在或解析失败，则初始化为空列表
            
            errors.append(error_data)  # 将新的错误记录添加到列表中
            
            # 保存错误信息到文件
            with open(self.error_file, "w", encoding="utf-8") as f:
                json.dump(errors, f, ensure_ascii=False, indent=2)

class Parser:
    """
    解析器类，用于解析网页内容并提取需要的信息
    """
    @staticmethod
    def parse_book_list(html: str) -> List[BookInfo]:
        """
        解析图书列表
        :param html: 网页的HTML内容
        :return: 图书信息列表
        """
        soup = BeautifulSoup(html, "html.parser")  # 使用BeautifulSoup解析HTML
        list_it = soup.find("ul", class_="list-it")  # 找到包含图书链接的列表
        books = []

        if list_it:
            links = list_it.find_all("a", href=True)  # 获取所有带有href属性的<a>标签
            for i, link in enumerate(links, 1):
                href = link.get("href")  # 获取链接地址
                match = re.search(r"\?id=(\d+)", href)  # 使用正则表达式提取图书ID
                if match:
                    books.append(BookInfo(
                        title=link.get_text(strip=True),  # 图书标题
                        original_url=f"{BASE_URL}/?id={match.group(1)}"  # 图书原始链接
                    ))

        return books

    @staticmethod
    def parse_download_link(html: str) -> Optional[str]:
        """
        解析图书下载链接
        :param html: 网页的HTML内容
        :return: 下载链接（如果找到），否则返回None
        """
        soup = BeautifulSoup(html, "html.parser")
        download_link = soup.find("a", string=lambda text: text and "下载" in text)  # 查找含有"下载"字样的链接
        return download_link.get("href") if download_link else None

class NovelCrawler:
    """
    小说爬虫类，用于抓取小说数据
    """
    
    def __init__(self, category: str):
        """
        初始化爬虫
        :param category: 小说分类
        """
        self.category = category  # 分类
        self.session = SessionManager()  # 会话管理器
        self.storage = Storage(category)  # 存储管理器
        self.parser = Parser()  # 解析器
        self.result_queue = queue.Queue()  # 结果队列
        
        # 初始化统计信息
        self.stats = {
            'total_pages': CATEGORIES[category]['total_pages'],  # 总页数
            'processed_pages': 0,  # 已处理页数
            'total_books': 0,  # 图书总数
            'processed_books': 0,  # 已处理图书数
            'successful_downloads': 0,  # 成功下载的数量
            'failed_downloads': 0  # 下载失败的数量
        }

    def print_progress(self):
        """
        打印当前进度统计
        """
        print("\n=== 爬取进度统计 ===")
        print(f"分类: {self.category}")
        print(f"页面进度: {self.stats['processed_pages']}/{self.stats['total_pages']} ({(self.stats['processed_pages']/self.stats['total_pages']*100):.1f}%)")
        print(f"图书总数: {self.stats['total_books']}")
        print(f"已处理图书: {self.stats['processed_books']}")
        print(f"下载链接获取成功: {self.stats['successful_downloads']}")
        print(f"下载链接获取失败: {self.stats['failed_downloads']}")
        print("="*20)

    def crawl_page(self, page: int) -> List[BookInfo]:
        """
        爬取单个页面的图书列表
        :param page: 页码
        :return: 图书信息列表
        """
        logging.info(f"开始爬取 {self.category} 分类第 {page} 页")
        url = f"{BASE_URL}/?cate={CATEGORIES[self.category]['id']}&page={page}"  # 生成该页的URL
        response = self.session.get(url)  # 发送请求
        books = self.parser.parse_book_list(response.text)  # 解析图书列表
        
        # 设置页码和索引信息
        for i, book in enumerate(books, 1):
            book.page_number = page
            book.index = i

        self.storage.save_links(books)  # 保存图书链接
        
        # 更新统计信息
        self.stats['processed_pages'] += 1
        self.stats['total_books'] += len(books)
        
        logging.info(f"第 {page} 页爬取完成，获取到 {len(books)} 本书")
        #更新进度
        self.print_progress()
            
        return books

    def get_download_link(self, book: BookInfo) -> bool:
        """
        获取图书下载链接
        :param book: 图书信息对象
        :return: 如果成功获取下载链接，则返回True，否则返回False
        """
        logging.info(f"正在获取《{book.title}》的下载链接...")
        try:
            response = self.session.get(book.original_url)  # 发送请求
            download_url = self.parser.parse_download_link(response.text)  # 解析下载链接
            
            if download_url:
                book.download_url = download_url  # 如果找到下载链接，保存
                self.storage.save_download_link(book)
                self.stats['successful_downloads'] += 1
                logging.info(f"成功获取《{book.title}》的下载链接")
                return True
            else:
                # 如果未找到下载链接，保存错误信息
                self.storage.save_error(book, "未找到下载链接")
                self.stats['failed_downloads'] += 1
                logging.warning(f"未找到《{book.title}》的下载链接")
                return False

        except Exception as e:
            self.storage.save_error(book, str(e))  # 保存错误信息
            self.stats['failed_downloads'] += 1
            return False

    def process_batch(self, start_page: int, end_page: int):
        """
        处理一批页面
        :param start_page: 批次开始的页码
        :param end_page: 批次结束的页码
        """
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 使用线程池并发处理每一页
            futures = [executor.submit(self.crawl_page, page)
                      for page in range(start_page, end_page + 1)]
            
            for future in futures:
                try:
                    books = future.result()  # 获取每页的结果
                    for book in books:
                        self.stats['processed_books'] += 1
                        self.get_download_link(book)  # 获取每本书的下载链接
                except Exception as e:
                    logging.error(f"批处理失败: {str(e)}")
                    self.stats['failed_downloads'] += 1

    def run(self):
        """
        运行爬虫
        """
        print(f"\n开始爬取 {self.category} 分类的小说")
        print(f"总页数: {self.stats['total_pages']}")
        print("="*50)
        
        total_pages = CATEGORIES[self.category]["total_pages"]  # 获取该分类的总页数
        
        for start_page in range(1, total_pages + 1, BATCH_SIZE):
            end_page = min(start_page + BATCH_SIZE - 1, total_pages)  # 计算当前批次的最后一页
            logging.info(f"\n开始处理第 {start_page} 到 {end_page} 页")
            self.process_batch(start_page, end_page)  # 处理当前批次的页面
            # 打印阶段性统计
            self.print_progress()
            print(f"\n等待 5 秒后继续处理下一批...")
            time.sleep(5)  # 批次间隔
            
        # 打印最终统计信息
        print("\n=== 爬取完成统计 ===")
        print(f"分类: {self.category}")
        print(f"总页数: {self.stats['total_pages']}")
        print(f"总图书数: {self.stats['total_books']}")
        print(f"成功获取下载链接: {self.stats['successful_downloads']}")
        print(f"获取失败: {self.stats['failed_downloads']}")
        success_rate = (self.stats['successful_downloads'] / self.stats['total_books'] * 100
                       if self.stats['total_books'] > 0 else 0)  # 计算成功率
        print(f"成功率: {success_rate:.1f}%")
        print("="*20)

def main():
    """
    主函数
    """
    # 配置日志
    logging.basicConfig(**LOG_CONFIG)

    # 处理所有分类
    for category in CATEGORIES:
        logging.info(f"\n开始处理分类: {category}")
        crawler = NovelCrawler(category)
        crawler.run()

if __name__ == "__main__":
    main()  # 运行主程序
