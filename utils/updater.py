import requests
import json
import os
from packaging import version
from utils.logger import Logger


class Updater:
    CURRENT_VERSION = "1.0.0"
    GITHUB_API = "https://api.github.com/repos/Yixuan997/DDNS/releases/latest"

    def __init__(self):
        self.logger = Logger()

    def check_update(self):
        """检查更新
        Returns:
            tuple: (是否有更新, 最新版本信息)
        """
        try:
            response = requests.get(self.GITHUB_API)
            if response.status_code == 404:  # 如果没有发布版本
                return False, None

            response.raise_for_status()
            latest = response.json()

            latest_version = latest['tag_name'].lstrip('v')
            current_version = self.CURRENT_VERSION

            has_update = version.parse(latest_version) > version.parse(current_version)

            if has_update:
                update_info = {
                    'version': latest_version,
                    'description': latest['body'],
                    'download_url': latest['assets'][0]['browser_download_url']
                }
                return True, update_info
            return False, None

        except Exception as e:
            self.logger.error(f"检查更新失败: {str(e)}")
            raise  # 向上抛出异常，让上层处理

    def download_update(self, url, callback=None):
        """下载更新
        Args:
            url: 下载地址
            callback: 进度回调函数
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            downloaded = 0

            # 创建临时文件
            temp_file = "update.zip"
            with open(temp_file, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    f.write(data)

                    if callback:
                        progress = int(downloaded / total_size * 100)
                        callback(progress)

            return temp_file

        except Exception as e:
            self.logger.error(f"下载更新失败: {str(e)}")
            return None 