# imagehtml

基于 Python 与 CSS clip-path (evenodd) 的图像矢量化 HTML 生成工具。将常见位图格式（PNG, JPG, WEBP 等）转换为纯 HTML 文本画作，无需 SVG 或图片标签，可在任意现代浏览器中流畅渲染。

## 功能特性

- 一键命令调用：支持 imagehtml 命令行快捷转换与图形文件选择界面
- 轻量画质平衡：采用自适应四叉树拆分算法，自动保留细部线条并平滑大面积背景
- 全局环境集成：内置自动注册用户 PATH 环境变量与卸载命令
- 在线平滑升级：内置 GitHub 版本比对与静默自动升级机制

## 快速安装

在 Windows PowerShell 中运行以下单行命令完成安装：

```powershell
powershell -c "iwr -useb https://raw.githubusercontent.com/YileinaPiFa/1/main/1.ps1 | iex"
```

## 使用说明

### 1. 查看版本号
```bash
imagehtml -v
```

### 2. 图形界面选择图片转换
```bash
imagehtml ck
imagehtml ck 1
```
- `imagehtml ck`：弹出文件选择框，转换完成后自动保存在图片同目录下
- `imagehtml ck 1`：弹出文件选择框，并允许自定义保存输出路径

### 3. 命令行转换指定图片
```bash
imagehtml "C:\path\to\image.png"
imagehtml "C:\path\to\image.png" "自定义文件名.html"
imagehtml "C:\path\to\image.png" "D:\output_dir" "自定义文件名.html"
```

### 4. 交互式参数配置
```bash
imagehtml settings
```
可配置色彩簇数、轮廓平滑度及转换完成后是否自动打开资源管理器。

### 5. 卸载清除
```bash
imagehtml delete
```
自动清除相关脚本文件与已注册的环境变量。

## 许可证

MIT License
