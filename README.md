# 10000txt-Novel-Crawler
# 小说爬虫

这是一个用于爬取小说下载链接的 Python 爬虫脚本，支持多个小说分类，能够并发地抓取每一页的图书信息，并解析每本书的下载链接。爬虫使用了多线程和异步机制，能有效提高抓取效率。
适用网站：https://www.10000txt.com/

1.爬取网站所有分类所有页面的小说标题-页面链接-城通网盘链接
该步骤由Novel-Crawler.py完成
![image](https://github.com/user-attachments/assets/4404a1df-4fd3-42c8-b0d6-7bbaed568c19)
2.自动化下载城通网盘链接
![image](https://github.com/user-attachments/assets/bf2089ff-f4f8-4393-9466-a588beb2696f)

由于网盘限制，每次只能够下载一个文件


## 项目特点
- 支持多个小说分类：都市异能、奇幻玄幻、武侠仙侠、科幻游戏、惊悚灵异、历史军事。
- 通过线程池和队列管理实现并发抓取，提高效率。
- 配备日志记录功能，能够追踪和排查爬虫过程中的错误。
- 自动保存图书链接和下载链接。
- 支持失败重试机制，可以在请求失败时自动重试。

## 安装

1. 克隆本仓库：

    ```bash
    git clone https://github.com/zhaoyanxue666/10000txt-novel-crawler.git
    ```

2. 进入项目目录：

    ```bash
    cd novel-crawler
    ```

3. 安装依赖库：

    ```bash
    pip install -r requirements.txt
    ```

   依赖包括 `requests`、`beautifulsoup4` 等。

## 配置

爬虫的配置文件 `config.py` 包含了基础的配置参数，如请求超时、并发线程数、每批处理的页面数等。可以根据需要调整这些配置以优化爬虫性能或适应不同网站的需求。

- `BASE_URL`: 网站的基础 URL。
- `BATCH_SIZE`: 每批处理的页面数。
- `MAX_WORKERS`: 最大并发线程数。
- `REQUEST_TIMEOUT`: 请求的超时时间。
- `RETRY_DELAY`: 请求失败后的重试延迟。

## 使用

1. 直接运行 `main.py`，爬虫会开始抓取所有分类的小说信息并获取下载链接。

    ```bash
    python main.py
    ```

2. 爬虫会按分类依次爬取，每爬取一批页面后，会输出当前的进度和抓取统计信息，包括成功获取的下载链接数量和失败的下载链接数量。

3. 最终，所有获取的图书链接和下载链接将被保存在相应的文本文件中：
    - 图书链接保存在 `category_links.txt` 文件中。
    - 下载链接保存在 `category_download_links.txt` 文件中。
    - 错误信息保存在 `category_error_links.json` 文件中。

## 日志

所有爬虫过程中的日志信息将记录在 `crawler.log` 文件中，方便后续查看和调试。

## 贡献

欢迎贡献代码，您可以通过 Fork 本项目并提交 Pull Request。任何问题或改进建议请提交 Issue。

## 许可证

MIT 许可证，详见 `LICENSE` 文件。
