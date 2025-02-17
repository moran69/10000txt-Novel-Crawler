import requests
import random
import string
import re
import os
import chardet
from urllib.parse import urlparse, parse_qs  # 导入urlparse和parse_qs

def build_token():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))

def extract_file_info(url):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    
    # file_id is the last part of the path
    file_id = path_parts[-1]
    
    # password is a query parameter 'p'
    query_params = parse_qs(parsed_url.query)
    password = query_params.get('p', [None])[0]
    
    return file_id, password

def get_file_info(file_id, password, token=None):
    if token is None:
        token = build_token()
    
    origin = "https://ctfile.qinlili.workers.dev"
    path = "file" if len(file_id.split("-")) == 2 else "f"
    
    # 获取文件信息
    response = requests.get(f"https://webapi.ctfile.com/getfile.php?path={path}&f={file_id}&passcode={password}&token={token}&r={random.random()}&ref={origin}", headers={"origin": origin, "referer": origin})
    file_info = response.json()
    
    if file_info['code'] == 200:
        file_name = file_info['file']['file_name']
        file_size = file_info['file']['file_size']
        file_time = file_info['file']['file_time']
        
        # 获取下载链接
        response = requests.get(f"https://webapi.ctfile.com/get_file_url.php?uid={file_info['file']['userid']}&fid={file_info['file']['file_id']}&file_chk={file_info['file']['file_chk']}&app=0&acheck=2&rd={random.random()}", headers={"origin": origin, "referer": origin})
        download_info = response.json()
        
        if download_info['code'] == 200:
            return {"success": True, "name": file_name, "size": file_size, "time": file_time, "link": download_info['downurl']}
        else:
            errormsg = download_info['message'] if download_info['code'] != 302 else "需要登录！"
            return {"success": False, "name": file_name, "size": file_size, "time": file_time, "errormsg": errormsg}
    else:
        return {"success": False, "errormsg": file_info['file']['message']}

def download_file(download_url, file_name, category):
    """根据下载链接下载文件并保存到指定的分类文件夹"""
    try:
        # 创建分类文件夹，如果文件夹不存在则创建
        directory = category  # 这里是分类文件夹名，比如 "都市"
        os.makedirs(directory, exist_ok=True)  # 如果目录不存在，则创建
        
        print(f"开始下载文件: {file_name}")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        # 检测文件编码（自动选择最可能的编码），默认设置为'GB2312'
        detected_encoding = chardet.detect(response.content)
        encoding = 'gb2312'  # 强制设置为GB2312编码

        # 判断文件类型，使用二进制方式下载（常见二进制文件如图片、压缩文件）
        if 'application' in response.headers['Content-Type'] or 'image' in response.headers['Content-Type']:
            file_path = os.path.join(directory, file_name)  # 保存路径
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"文件下载完成: {file_path}")
        else:
            # 对于文本文件（如 .txt），强制使用GB2312编码保存
            file_path = os.path.join(directory, file_name)  # 保存路径
            with open(file_path, 'w', encoding=encoding) as file:
                file.write(response.text)
            print(f"文件下载完成: {file_path}")
    except Exception as e:
        print(f"下载失败: {file_name}，错误: {str(e)}")


def process_file_links(file_path):
    """
    读取txt文件，提取下载链接信息，并获取文件信息并下载
    :param file_path: 存储URL链接的txt文件路径
    """
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            # 使用正则表达式提取“下载链接”
            match = re.search(r"下载链接:\s*(https?://[^\s]+)", line)
            if match:
                download_url = match.group(1)
                
                # 获取文件ID和密码（用于构造下载链接）
                file_id, password = extract_file_info(download_url)
                print(f"file_id: {file_id}, password: {password}")
                
                # 获取文件信息
                file_info = get_file_info(file_id, password)
                
                # 打印文件信息
                if file_info["success"]:
                    print(f"文件名称: {file_info['name']}")
                    print(f"文件大小: {file_info['size']}")
                    print(f"文件上传时间: {file_info['time']}")
                    print(f"下载链接: {file_info['link']}")
                    
                    # 假设文件的分类信息在文件名中，如果没有你可以自行指定
                    category = "都市"  # 你可以修改这里的分类
                    download_file(file_info['link'], file_info['name'], category)
                else:
                    print(f"错误信息: {file_info.get('errormsg', '未知错误')}")
                print("="*50)

# 使用示例，传入存储URL链接的txt文件路径
category = "都市"  # 分类名称
process_file_links("都市异能download_links.txt")
