import sys
import os
import json
import time
import subprocess
import cv2
import numpy as np
import urllib.request
import re
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

VERSION = "image to html V1.0.0.06 XM"
CONFIG_FILE = os.path.expanduser("~/.imagehtml_config.json")

DEFAULT_CONFIG = {
    "colors": 64,
    "smoothness": 0.0005,
    "auto_open_explorer": True
}

def is_github_reachable():
    try:
        res = subprocess.run(["ping", "github.com", "-n", "1"], capture_output=True, text=True, timeout=2)
        return res.returncode == 0
    except Exception:
        return False

def check_auto_update():
    content = None
    remote_ver = None
    url = "https://fastly.jsdelivr.net/gh/YileinaPiFa/1@main/1.py"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    for fetch_attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
                m = re.search(r'VERSION\s*=\s*"([^"]+)"', content)
                if m:
                    remote_ver = m.group(1)
                    break
        except Exception:
            time.sleep(0.3)

    if not content or not remote_ver:
        return

    if remote_ver != VERSION:
        print(f"\n检测到新版本: [{remote_ver}]，即将自动升级")
        
        upgrade_success = False
        for write_attempt in range(3):
            try:
                script_path = os.path.abspath(__file__)
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(content)
                upgrade_success = True
                break
            except Exception:
                time.sleep(0.3)
                
        if upgrade_success:
            print(f"已经升级到新版本了，当前版本号[{remote_ver}]")
        else:
            if not is_github_reachable():
                print("（升级失败了，当前无法连接到GitHub）")
            else:
                print("（升级失败了，请输入imagehtml delete卸载当前版本后重新安装）")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"保存设置失败: {e}")

def print_progress(percent, msg):
    bar_len = 25
    filled = int(bar_len * percent / 100)
    bar = '█' * filled + '░' * (bar_len - filled)
    print(f"\r进度 [{bar}] {percent:3d}% | {msg}", end="", flush=True)

def quadtree_decompose(img, x, y, width, height, min_size=2, max_var=12.0, max_block_size=24, pieces=None, depth=0, max_depth=10):
    if pieces is None:
        pieces = []

    sub_img = img[y:y+height, x:x+width]
    if sub_img.size == 0:
        return pieces

    mean_color = cv2.mean(sub_img)[:3]
    std_dev = np.std(sub_img, axis=(0, 1))
    color_var = np.mean(std_dev)

    if (width <= min_size or height <= min_size or (color_var <= max_var and width <= max_block_size and height <= max_block_size)) or depth >= max_depth:
        r, g, b = [int(c) for c in mean_color]
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        
        x1, y1 = x, y
        x2, y2 = x + width, y + height
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        
        path_d = f"M {x1} {y1} Q {mx} {y1} {x2} {y1} Q {x2} {my} {x2} {y2} Q {mx} {y2} {x1} {y2} Q {x1} {my} {x1} {y1} Z"

        pieces.append({
            "color": hex_color,
            "path": path_d,
            "area": width * height
        })
        return pieces

    w_half = width // 2
    h_half = height // 2
    w_rem = width - w_half
    h_rem = height - h_half

    quadtree_decompose(img, x, y, w_half, h_half, min_size, max_var, max_block_size, pieces, depth + 1, max_depth)
    quadtree_decompose(img, x + w_half, y, w_rem, h_half, min_size, max_var, max_depth)
    quadtree_decompose(img, x, y + h_half, w_half, h_rem, min_size, max_var, max_depth)
    quadtree_decompose(img, x + w_half, y + h_half, w_rem, h_rem, min_size, max_var, max_depth)

    return pieces

def trace_and_save(img_path, output_path, colors=32, smoothness=0.001, auto_open=True):
    start_time = time.time()

    if not os.path.exists(img_path):
        print(f"错误：找不到图片文件【{img_path}】")
        sys.exit(1)

    print_progress(5, "读取图片...")
    try:
        pil_img = Image.open(img_path).convert("RGB")
        w, h = pil_img.size
        
        target_dim = 650
        scale = target_dim / float(max(h, w))
        w = int(w * scale)
        h = int(h * scale)
        img_rgb = np.array(pil_img.resize((w, h), Image.Resampling.LANCZOS))
    except Exception as e:
        print(f"\n错误：无法读取图片【{img_path}】: {e}")
        sys.exit(1)

    print_progress(20, "启动中...")
    raw_pieces = quadtree_decompose(img_rgb, 0, 0, w, h, min_size=2, max_var=12.0, max_block_size=24)

    print_progress(75, "处理中...")
    color_map = {}
    css_vars = []
    for p in raw_pieces:
        c = p["color"]
        if c not in color_map:
            var_name = f"--c-{len(color_map)}"
            color_map[c] = f"var({var_name})"
            css_vars.append(f"    {var_name}: {c};")
        p["var"] = color_map[c]

    print_progress(90, "生成中...")
    css_vars_str = "\n".join(css_vars)
    pieces_html = [f'      <div class="piece" style="--paint: {p["var"]}; --clip: path(evenodd, \'{p["path"]}\');"></div>' for p in raw_pieces]
    pieces_str = "\n".join(pieces_html)

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vector Traced Art</title>
<style>
  :root {{
{css_vars_str}
  }}
  html, body {{
    margin: 0; padding: 0; width: 100%; min-height: 100%; background: #f8fafc; color: #0f172a;
    display: flex; justify-content: center; align-items: center; overflow-x: hidden;
  }}
  .frame {{
    position: relative; width: 100%; max-width: 600px; aspect-ratio: {w} / {h};
    overflow: hidden; background: #ffffff; border-radius: 12px;
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.08);
  }}
  .artwork {{
    position: absolute; left: 0; top: 0; width: {w}px; height: {h}px; transform-origin: 0 0;
    transition: transform 0.2s ease;
  }}
  .piece {{
    position: absolute; left: 0; top: 0; width: {w}px; height: {h}px; pointer-events: auto;
    background: var(--paint); background-size: {w}px {h}px; background-repeat: no-repeat;
    clip-path: var(--clip); transition: transform 0.3s ease;
  }}
  .piece:hover {{ filter: brightness(1.08); z-index: 99; }}
</style>
</head>
<body>
  <div class="frame">
    <div class="artwork">
{pieces_str}
    </div>
  </div>

  <script>
    function fitArtwork() {{
      const frame = document.querySelector('.frame');
      const artwork = document.querySelector('.artwork');
      if (frame && artwork) {{
        const scale = frame.clientWidth / {w};
        artwork.style.transform = `scale(${{scale}})`;
      }}
    }}
    window.addEventListener('resize', fitArtwork);
    document.addEventListener('DOMContentLoaded', fitArtwork);
    setTimeout(fitArtwork, 50);
    setTimeout(fitArtwork, 300);
  </script>
</body>
</html>
"""

    print_progress(98, "保存...")
    output_abs = os.path.abspath(output_path)
    out_dir = os.path.dirname(output_abs)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(output_abs, "w", encoding="utf-8") as f:
        f.write(html_template)

    print_progress(100, "完成，久久，完成！")
    print(f"\r{' '*85}\r", end="", flush=True)

    elapsed = round(time.time() - start_time, 2)
    
    win_str = ""
    if auto_open:
        try:
            subprocess.Popen(["explorer.exe", "/select,", os.path.normpath(output_abs)])
            win_str = " 窗口已打开"
        except Exception:
            pass

    print(f"Done！{elapsed}S 文件已保存在【{output_abs}】{win_str}")
    print("PS：可在配置界面关闭自动打开窗口。")

def gui_select_file(mode=0):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        img_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tiff;*.ico;*.gif"), ("所有文件", "*.*")]
        )
        if not img_path:
            sys.exit(0)

        if mode == 1:
            out_path = filedialog.asksaveasfilename(
                title="选择保存的 HTML 路径",
                defaultextension=".html",
                filetypes=[("HTML 文件", "*.html")]
            )
            if not out_path:
                sys.exit(0)
        else:
            base, _ = os.path.splitext(img_path)
            out_path = base + ".html"

        return img_path, out_path
    except Exception as e:
        print(f"错误：打开图形选择窗口失败: {e}")
        sys.exit(1)

def show_settings_menu():
    cfg = load_config()
    while True:
        print("\n修改配置")
        print(f"[1] 颜色簇数 (colors): {cfg['colors']}")
        print(f"[2] 轮廓平滑度 (smoothness): {cfg['smoothness']}")
        print(f"[3] 转换完成后自动打开资源管理器窗口: {'开启' if cfg['auto_open_explorer'] else '关闭'}")
        print("[0] 保存并退出")
        choice = input("请输入数字选择要修改的配置 (0-3): ").strip()

        if choice == "1":
            val = input("请输入新颜色簇数 (8-128, 默认 64): ").strip()
            if val.isdigit():
                cfg['colors'] = int(val)
                print(f"✓ 颜色簇数已修改为: {cfg['colors']}")
        elif choice == "2":
            val = input("请输入平滑度 (0.0005-0.01, 默认 0.0005): ").strip()
            try:
                cfg['smoothness'] = float(val)
                print(f"✓ 轮廓平滑度已修改为: {cfg['smoothness']}")
            except ValueError:
                pass
        elif choice == "3":
            cfg['auto_open_explorer'] = not cfg['auto_open_explorer']
            print(f"✓ 自动打开窗口已修改为: {'开启' if cfg['auto_open_explorer'] else '关闭'}")
        elif choice == "0":
            save_config(cfg)
            print("✓ 设置已保存！")
            break

def print_help():
    print(f"""
{VERSION} 使用帮助：

输出版本号：
   imagehtml -v

转换图片1：
   imagehtml ck             (选择图片，转换完成后自动保存在同目录下)
   imagehtml ck 1           (选择图片并选择保存位置)

转换图片2：
   imagehtml "C:\\path\\to\\image.png"
   imagehtml "C:\\path\\to\\image.png" "自定义文件名.html"
   imagehtml "C:\\path\\to\\image.png" "保存位置的路径" "自定义文件名.html"

打开配置界面：
   imagehtml settings/setting/set

卸载清除工具：
   imagehtml delete
""")

def install_to_path():
    try:
        import winreg
        import ctypes
        
        win_apps_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps")
        cmd_path = os.path.join(win_apps_dir, "imagehtml.cmd")
        script_path = os.path.abspath(__file__)
        
        cmd_content = f'@echo off\npython "{script_path}" %*\n'
        
        if os.path.exists(win_apps_dir):
            with open(cmd_path, "w", encoding="utf-8") as f:
                f.write(cmd_content)
        
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""
            
        paths = [p.strip() for p in current_path.split(";") if p.strip()]
        if win_apps_dir not in paths:
            paths.append(win_apps_dir)
            new_path = ";".join(paths)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 0x0002, 5000, None
            )
            print(f"✓ 已成功自动将【{win_apps_dir}】写入用户 PATH 环境变量！")
        else:
            print(f"✓ 环境变量 PATH 已包含可执行路径【{win_apps_dir}】。")
            
        winreg.CloseKey(key)
        print("✓ imagehtml 自动注册全局 PATH 成功！全新终端打开后即可在任意位置直接调用 imagehtml 指令。")
    except Exception as e:
        print(f"错误：自动注册 PATH 环境变量失败: {e}")

def uninstall():
    try:
        script_path = os.path.abspath(__file__)
        win_apps_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps")
        cmd_path = os.path.join(win_apps_dir, "imagehtml.cmd")
        py_path = os.path.join(win_apps_dir, "1.py")

        if os.path.exists(cmd_path):
            try:
                os.remove(cmd_path)
            except Exception:
                pass
                
        if os.path.exists(py_path):
            try:
                os.remove(py_path)
            except Exception:
                pass

        if os.path.exists(script_path) and script_path not in [cmd_path, py_path]:
            try:
                os.remove(script_path)
            except Exception:
                pass

        print("已成功卸载 imagehtml 并清理相关系统变量与文件！")
    except Exception as e:
        print(f"卸载过程中发生错误: {e}")

def parse_cli_args():
    if len(sys.argv) > 1 and sys.argv[1] in ["delete", "uninstall", "remove"]:
        uninstall()
        sys.exit(0)

    check_auto_update()
    cfg = load_config()
    args = sys.argv[1:]

    if not args:
        print_help()
        sys.exit(0)

    if args[0] in ["install", "setup"]:
        install_to_path()
        sys.exit(0)

    if args[0] == "-v":
        print(VERSION)
        sys.exit(0)

    if args[0] in ["help", "-h", "--help"]:
        print_help()
        sys.exit(0)

    if args[0] in ["settings", "setting", "set"]:
        show_settings_menu()
        sys.exit(0)

    if args[0] == "ck":
        mode = 1 if len(args) > 1 and args[1] == "1" else 0
        img_p, out_p = gui_select_file(mode)
        trace_and_save(img_p, out_p, cfg['colors'], cfg['smoothness'], cfg['auto_open_explorer'])
        sys.exit(0)

    raw_str = " ".join(args)
    
    custom_name = None
    quoted = re.findall(r'"([^"]+)"', raw_str)
    
    unquoted_parts = []
    for arg in args:
        if not arg.startswith('"') and not arg.endswith('"'):
            unquoted_parts.append(arg)

    img_path = None
    out_dir = None

    for q in quoted:
        if os.path.isfile(q):
            img_path = q
        elif os.path.isdir(q):
            out_dir = q
        elif q.endswith(".html") or "." not in os.path.basename(q):
            custom_name = q

    for p in unquoted_parts:
        if not img_path and os.path.isfile(p):
            img_path = p
        elif not out_dir and os.path.isdir(p):
            out_dir = p
        elif not custom_name and (p.endswith(".html") or "." not in os.path.basename(p)):
            custom_name = p

    if not img_path and len(args) >= 1:
        img_path = args[0].strip('"')

    if not img_path or not os.path.exists(img_path):
        print(f"错误：无法找到指定的图片文件【{img_path}】")
        sys.exit(1)

    img_dir = os.path.dirname(os.path.abspath(img_path))
    img_name = os.path.splitext(os.path.basename(img_path))[0]

    target_dir = out_dir if out_dir else img_dir

    if custom_name:
        if not custom_name.endswith(".html"):
            custom_name += ".html"
        target_filename = custom_name
    else:
        target_filename = img_name + ".html"

    final_out_path = os.path.join(target_dir, target_filename)
    trace_and_save(img_path, final_out_path, cfg['colors'], cfg['smoothness'], cfg['auto_open_explorer'])

if __name__ == "__main__":
    parse_cli_args()
