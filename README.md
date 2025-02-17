# Cursor ID 修改器

一个用于管理 Cursor 编辑器配置的开源工具。

## ✨ 功能特点

- 🔄 修改设备标识
- 💾 配置备份还原
- 🚀 更新控制开关
- 🌍 中英文界面
- 💻 支持 Win/Mac

## 🚀 使用方法

### 方式一：直接运行

从 [Releases](https://github.com/lbjlaq/CursorTool/releases) 页面下载已打包好的可执行文件：
- Windows: 下载 `CursorTool-win.exe`
- macOS: 下载 `CursorTool-mac`

### 方式二：源码运行

#### 环境要求

- Windows 10+ / macOS 10.15+
- Python 3.8+
- 管理员权限

#### 安装运行

```bash
# 安装依赖
pip install -r requirements.txt

# Windows 运行
python cursor_win_gui.py

# macOS 运行
python cursor_mac_gui.py
```

#### 自行打包

如果预编译版本无法运行，可以使用 PyInstaller或者其他的方式 自行打包：



### 使用步骤

1. 关闭 Cursor 所有进程
2. 删除当前账号或准备新账号
3. 使用本工具生成新配置
4. 重启 Cursor 并登录

## ⚠️ 注意事项

- 需要管理员权限
- 修改前会自动备份
- 请勿频繁操作
- 仅供学习研究使用

## 🛠️ 开发相关

### 技术栈
- Python + PyQt6

### 依赖
```text
PyQt6>=6.4.0
psutil>=5.9.0
```

## 📝 许可证

本项目采用 MIT 协议开源。

## 👨‍💻 作者

[@lbjlaq](https://github.com/lbjlaq)

## 🙏 致谢

本项目基于 [@yuaotian](https://github.com/yuaotian) 的 [go-cursor-help](https://github.com/yuaotian/go-cursor-help) 项目实现。感谢他的开源贡献！

## 🔗 链接

- [项目主页](https://github.com/lbjlaq/CursorTool)
- [问题反馈](https://github.com/lbjlaq/CursorTool/issues)

## 📝 免责声明

本工具仅供学习研究使用，请勿用于商业用途。使用本工具所造成的任何问题由使用者自行承担。
