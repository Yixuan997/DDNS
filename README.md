# PyQt DDNS Client

这是一个使用PySide6开发的DDNS客户端软件，用于自动更新域名解析记录。该客户端提供了友好的图形界面，支持多个DNS平台，并能够自动管理域名解析。

## 功能特点

- 自动获取本地IPv4和IPv6地址
- 支持多个DNS平台（目前支持Cloudflare）
- 可配置的更新时间间隔
- 系统托盘运行
- 实时日志显示和记录
- 开机自启动选项
- 现代化的UI界面
- 友好的消息提示

## 项目结构

- `core/`: 核心功能实现
- `dns_platforms/`: 各DNS平台的API实现
- `ui/`: 用户界面相关组件
- `utils/`: 工具类和辅助函数
- `resources/`: 资源文件
- `tools/`: 开发工具和脚本

## 使用方法

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置说明

1. 在首次运行时，需要配置DNS平台的认证信息
2. 支持配置多个域名记录
3. 可以设置自动更新时间间隔
4. 支持开机自启动设置

### 运行程序

```bash
python main.py
```

## 日志系统

项目包含完整的日志记录系统：

- 支持多种日志级别（INFO、WARNING、ERROR、DEBUG）
- 日志界面实时更新
- 彩色显示不同级别的日志
- 支持日志清除和查看历史记录

## 开发计划

1. 添加更多DNS平台支持
2. 优化网络连接检测机制
3. 添加域名健康检查功能
4. 支持更多的域名记录类型
5. 添加数据统计和分析功能

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进这个项目。在提交代码前，请确保：

1. 代码符合项目的编码规范
2. 添加了必要的测试用例
3. 更新了相关文档

## 许可证

MIT License
