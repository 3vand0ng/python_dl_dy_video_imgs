# DY 视频或图文下载工具

这是一个简单的 Python 工具，可以将分享链接中的视频或图文下载到本地。

## 功能特点

- **去 Watermark**：下载的视频没有 Watermark。
- **高清画质**：默认尝试下载1080p画质。
- **自动保存**：视频自动保存到 `output` 文件夹。

## 环境要求

- Python 3.6 或更高版本

## 安装步骤

1. **创建虚拟环境**（推荐）：
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # 或者 Windows: venv\Scripts\activate
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

### 方式一：直接运行脚本并输入链接

运行脚本后，根据提示输入分享的文本或链接：

```bash
python python_downloader.py
```

### 方式二：通过命令行参数传入链接

你也可以直接将分享文本作为参数传给脚本（记得给文本加上引号）：

```bash
python python_downloader.py "xxxxxxx"
```

## 输出

下载成功的视频将保存在 `output` 文件夹中，文件名为 `Video_{video_id}.mp4`。

下载成功的图片将保存在 `output` 文件夹中，文件名为 `Img_{img_id}_{idx+1}.{ext}`。

## 📈 Stars 趋势

[![Star History Chart](https://api.star-history.com/svg?repos=3vand0ng/python_dl_dy_video_imgs&type=Date)](https://star-history.com/#3vand0ng/python_dl_dy_video_imgs&Date)
