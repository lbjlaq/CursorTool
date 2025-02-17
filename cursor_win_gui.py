import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QMessageBox, QTextEdit, 
                            QScrollArea, QFrame, QDialog, QHBoxLayout,
                            QSizePolicy, QSpacerItem)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
import ctypes
import json
import datetime
import shutil
import uuid
import random
import psutil

# 添加消息常量
MESSAGES = {
    'not_found': '未找到',
    'success': '成功',
    'error': '错误',
    'warning': '警告',
    'info': '信息'
}

class CursorModifier:
    def __init__(self):
        """初始化 CursorModifier"""
        # 获取 Cursor 配置文件路径
        self.storage_file = self.get_storage_path()

    def get_storage_path(self):
        """获取 Cursor 配置文件路径"""
        appdata = os.getenv('APPDATA')
        return os.path.join(appdata, 'Cursor', 'User', 'globalStorage', 'storage.json')

    def get_cursor_version(self):
        """获取 Cursor 版本"""
        try:
            # 主要检测路径
            package_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Programs', 'cursor', 'resources', 'app', 'package.json')
            
            if os.path.exists(package_path):
                with open(package_path, 'r', encoding='utf-8') as f:
                    package_json = json.load(f)
                    if package_json.get('version'):
                        print(f"[信息] 当前安装的 Cursor 版本: v{package_json['version']}")
                        return package_json['version']

            # 备用路径检测
            alt_path = os.path.join(os.getenv('LOCALAPPDATA'), 'cursor', 'resources', 'app', 'package.json')
            if os.path.exists(alt_path):
                with open(alt_path, 'r', encoding='utf-8') as f:
                    package_json = json.load(f)
                    if package_json.get('version'):
                        print(f"[信息] 当前安装的 Cursor 版本: v{package_json['version']}")
                        return package_json['version']

            print("[警告] 无法检测到 Cursor 版本")
            print("[提示] 请确保 Cursor 已正确安装")
            return MESSAGES['not_found']
            
        except Exception as e:
            print(f"[错误] 获取 Cursor 版本失败: {str(e)}")
            return MESSAGES['not_found']

    def is_auto_update_enabled(self):
        """检查自动更新是否启用"""
        try:
            if not os.path.exists(self.storage_file):
                return True
            
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            update_mode = config.get('update.mode', 'default')
            update_channel = config.get('update.channel', 'default')
            enable_download = config.get('update.enableDownload', True)
            
            is_disabled = (
                update_mode == 'none' or
                update_channel == 'none' or
                enable_download is False
            )
            
            return not is_disabled
        
        except json.JSONDecodeError:
            return True
        except Exception as e:
            print(f"检查更新状态时出错: {str(e)}")
            return True

    def disable_auto_update(self):
        """禁用自动更新"""
        try:
            if not os.path.exists(self.storage_file):
                config = {}
            else:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config.update({
                'update.mode': 'none',
                'update.channel': 'none',
                'update.enableDownload': False
            })
            
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            print(f"禁用自动更新时出错: {str(e)}")
            return False

    def enable_auto_update(self):
        """启用自动更新"""
        try:
            if not os.path.exists(self.storage_file):
                config = {}
            else:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config.update({
                'update.mode': 'default',
                'update.channel': 'default',
                'update.enableDownload': True
            })
            
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            print(f"启用自动更新时出错: {str(e)}")
            return False

    def list_backups(self):
        """列出所有备份"""
        backup_dir = os.path.join(os.path.dirname(self.storage_file), 'backups')
        if not os.path.exists(backup_dir):
            return []
        return [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) 
                if f.endswith('.json')]

    def get_backup_info(self, backup_path, current_language):
        """获取备份信息"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 获取文件信息
            file_stat = os.stat(backup_path)
            create_time = datetime.datetime.fromtimestamp(file_stat.st_ctime)
            
            # 只获取关键配置信息
            important_configs = {
                'machineId': backup_data.get('telemetry.machineId', 'N/A'),
                'macMachineId': backup_data.get('telemetry.macMachineId', 'N/A'),
                'devDeviceId': backup_data.get('telemetry.devDeviceId', 'N/A'),
                'sqmId': backup_data.get('telemetry.sqmId', 'N/A')
            }
            
            # 格式化信息
            config_info = "\n".join([
                f"{key} ({current_language['messages']['current_config'].get(key, key)}): {value}"
                for key, value in important_configs.items()
            ])
            
            return current_language['messages']['log']['backup_info'].format(
                os.path.basename(backup_path),
                create_time.strftime("%Y-%m-%d %H:%M:%S"),
                config_info
            )
        except Exception as e:
            return f"读取备份信息失败: {str(e)}"

    def create_manual_backup(self):
        """创建手动备份"""
        try:
            if not os.path.exists(self.storage_file):
                return None
            
            # 创建备份目录
            backup_dir = os.path.join(os.path.dirname(self.storage_file), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f'backup_{timestamp}.json')
            
            # 复制配置文件
            shutil.copy2(self.storage_file, backup_path)
            
            return backup_path
        except Exception as e:
            print(f"创建备份时出错: {str(e)}")
            return None

    def restore_backup(self, backup_path):
        """恢复备份"""
        try:
            if not os.path.exists(backup_path):
                return False
            
            # 先创建一个当前配置的备份
            self.create_manual_backup()
            
            # 恢复选定的备份
            shutil.copy2(backup_path, self.storage_file)
            
            return True
        except Exception as e:
            print(f"恢复备份时出错: {str(e)}")
            return False

    def generate_new_config(self):
        """生成新的配置"""
        try:
            # 检查并关闭 Cursor 进程
            print("[信息] 检查 Cursor 进程...")
            if not self.close_cursor_process():
                return False
            
            # 生成新的 ID
            print("[信息] 正在生成新的 ID...")
            
            # 生成 MAC_MACHINE_ID (标准UUID格式)
            mac_machine_id = str(uuid.uuid4())
            
            # 生成 UUID (标准UUID格式)
            device_id = str(uuid.uuid4())
            
            # 生成 MACHINE_ID (特殊格式: auth0|user_ + 随机字符)
            prefix = "auth0|user_"
            prefix_hex = prefix.encode('utf-8').hex()
            random_part = ''.join(random.choices('0123456789abcdef', k=64))
            machine_id = f"{prefix_hex}{random_part}"
            
            # 生成 SQM_ID (大写的UUID，带花括号)
            sqm_id = "{" + str(uuid.uuid4()).upper() + "}"
            
            # 读取现有配置
            if not os.path.exists(self.storage_file):
                print("[信息] 未找到配置文件，将创建新配置")
                config = {}
            else:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 创建备份
            self.create_manual_backup()
            
            # 更新配置
            config.update({
                'telemetry.machineId': machine_id,
                'telemetry.macMachineId': mac_machine_id,
                'telemetry.devDeviceId': device_id,
                'telemetry.sqmId': sqm_id
            })
            
            # 保存配置
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            print("[信息] 配置已更新:")
            print(f"machineId: {machine_id}")
            print(f"macMachineId: {mac_machine_id}")
            print(f"devDeviceId: {device_id}")
            print(f"sqmId: {sqm_id}")
            
            return True
            
        except Exception as e:
            print(f"[错误] 生成配置时出错: {str(e)}")
            return False

    def close_cursor_process(self):
        """关闭 Cursor 进程"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() in ['cursor.exe', 'cursor']:
                    print(f"[信息] 发现 Cursor 进程 (PID: {proc.pid})")
                    proc.kill()
                    print("[信息] 已终止 Cursor 进程")
            return True
        except Exception as e:
            print(f"[错误] 关闭进程时出错: {str(e)}")
            return False

class Language:
    """语言配置"""
    CHINESE = {
        'title': "Cursor ID 修改器 (Win版)",
        'version': "Cursor 版本: {}",
        'log_title': "操作日志",
        'status_ready': "就绪",
        'buttons': {
            # ID管理
            'id_management': {
                'title': "ID 管理",
                'generate': "生成新配置",
                'view_current': "查看当前配置"
            },
            # 备份管理
            'backup_management': {
                'title': "备份管理",
                'view_backup': "查看备份",
                'create_backup': "创建备份"
            },
            # 更新控制
            'update_control': {
                'title': "更新控制",
                'disable_update': "禁用自动更新",
                'enable_update': "恢复自动更新"
            },
            # 其他
            'others': {
                'title': "其他",
                'about': "关于",
                'switch_lang': "Switch to English"
            }
        },
        'dialog': {
            'title': "备份管理",
            'backup_list': "备份列表",
            'restore': "♻️ 恢复此备份",
            'delete': "🗑️ 删除此备份",
            'close': "❌ 关闭"
        },
        'confirm': {
            'title': "确认",
            'generate': "此操作将修改设备ID，是否继续？",
            'restore': "确定要恢复此备份吗？",
            'delete': "确定要删除此备份吗？"
        },
        'messages': {
            'success': "成功",
            'error': "错误",
            'info': "提示",
            'warning': "警告",
            'restore_failed': "恢复失败",
            'update_failed': "更新失败",
            'backup_created': "备份已创建: {}",
            'config_updated': "配置已更新",
            'new_ids': "新的ID:",
            'no_backups': "未找到备份",
            'backup_restored': "备份已恢复",
            'update_disabled': "自动更新已禁用",
            'update_enabled': "自动更新已启用",
            'backup_success': "备份成功: {}",
            'closing_cursor': "正在关闭Cursor进程...",
            'ui_update_error': "更新界面文本时出错: {}",
            'notes': {
                'admin': "需要管理员权限",
                'backup': "修改前自动备份",
                'language': "支持中英双语",
                'frequency': "请勿频繁操作",
                'purpose': "仅供学习研究使用"
            },
            'log': {
                'backup_info': """
备份信息:
文件名: {}
创建时间: {}
配置内容:
{}
""",
                'backup_title': "可用的备份:",
                'backup_separator': "{}备份 {}{}"
            },
            'current_config': {
                'title': "当前配置信息",
                'format': """当前配置信息:

machineId (机器ID): {}
macMachineId (MAC机器ID): {}
devDeviceId (设备ID): {}
sqmId (SQM ID): {}
"""
            },
            'backup_deleted': "备份已删除",
            'delete_failed': "删除失败"
        },
        'about': """
关于
----------------------------------------
Cursor ID 修改器 (Win版)
版本: 1.0.0

功能说明:
• 修改 Cursor 编辑器的设备标识
• 支持配置备份和恢复
• 控制自动更新功能
• 支持最新的 Cursor 版本

使用说明:
1. 退出 Cursor 并关闭所有相关进程
2. 访问 Cursor 官网删除当前账号，重新注册以获取新额度；或使用新账号
3. 使用本工具生成新配置
4. 重启 Cursor 并登录账号即可使用
5. 首次使用请先备份配置
6. 建议定期备份配置

注意事项:
• {admin}
• {backup}
• {language}
• {frequency}
• {purpose}

作者: Ctrler
最后更新: 2025
----------------------------------------
""",
    }
    
    ENGLISH = {
        'title': "Cursor ID Modifier (WIN version)",
        'version': "Cursor Version: {}",
        'log_title': "Operation Log",
        'status_ready': "Ready",
        'buttons': {
            # ID Management
            'id_management': {
                'title': "ID Management",
                'generate': "Generate New Config",
                'view_current': "View Current Config"
            },
            # Backup Management
            'backup_management': {
                'title': "Backup Management",
                'view_backup': "View Backups",
                'create_backup': "Create Backup"
            },
            # Update Control
            'update_control': {
                'title': "Update Control",
                'disable_update': "Disable Auto-update",
                'enable_update': "Enable Auto-update"
            },
            # Others
            'others': {
                'title': "Others",
                'about': "About",
                'switch_lang': "Switch to Chinese"
            }
        },
        'dialog': {
            'title': "Backup Management",
            'backup_list': "Backup List",
            'restore': "♻️ Restore this backup",
            'delete': "🗑️ Delete this backup",
            'close': "❌ Close"
        },
        'confirm': {
            'title': "Confirm",
            'generate': "This will modify device IDs, continue?",
            'restore': "Are you sure to restore this backup?",
            'delete': "Are you sure to delete this backup?"
        },
        'messages': {
            'success': "Success",
            'error': "Error",
            'info': "Information",
            'warning': "Warning",
            'restore_failed': "Restore failed",
            'update_failed': "Update failed",
            'backup_created': "Backup created: {}",
            'config_updated': "Configuration updated",
            'new_ids': "New IDs:",
            'no_backups': "No backups found",
            'backup_restored': "Backup restored",
            'update_disabled': "Auto-update disabled",
            'update_enabled': "Auto-update enabled",
            'backup_success': "Backup successful: {}",
            'closing_cursor': "Closing Cursor processes...",
            'ui_update_error': "Error updating UI text: {}",
            'notes': {
                'admin': "Requires administrator privileges",
                'backup': "Auto backup before modification",
                'language': "Supports Chinese and English",
                'frequency': "Do not operate frequently",
                'purpose': "For learning and research purposes only"
            },
            'log': {
                'backup_info': """
Backup Information:
Filename: {}
Created: {}
Configuration:
{}
""",
                'backup_title': "Available backups:",
                'backup_separator': "{}Backup {}{}"
            },
            'current_config': {
                'title': "Current Configuration",
                'format': """Current Configuration:

machineId: {}
macMachineId: {}
devDeviceId: {}
sqmId: {}
"""
            },
            'backup_deleted': "Backup deleted",
            'delete_failed': "Delete failed"
        },
        'about': """
About
----------------------------------------
Cursor ID Modifier (WIN version)
Version: 1.0.0

Features:
• Modify Cursor editor device identifiers
• Support configuration backup and restore
• Control auto-update function
• Support latest Cursor version

Instructions:
1. Exit Cursor and close all related processes
2. Visit Cursor website to delete current account and re-register for new quota; or use a new account
3. Use this tool to generate new configuration
4. Restart Cursor and login to use
5. Please backup before first use
6. Regular backup is recommended

Notes:
• {admin}
• {backup}
• {language}
• {frequency}
• {purpose}

Author: Ctrler
Last Update: 2025
----------------------------------------
""",
    }

class StyleSheet:
    """样式表"""
    MAIN = """
    QMainWindow {
        background-color: #f5f6fa;
    }
    
    QPushButton {
        background-color: #4a69bd;
        color: white;
        border: none;
        padding: 10px;
        border-radius: 5px;
        font-size: 14px;
        min-width: 200px;
    }
    
    QPushButton:hover {
        background-color: #6a89cc;
    }
    
    QPushButton:pressed {
        background-color: #3c55a5;
    }
    
    QTextEdit {
        background-color: #ffffff;
        border: 1px solid #dcdde1;
        border-radius: 5px;
        padding: 5px;
        font-family: Consolas;
    }
    
    QLabel#version_label {
        color: #2f3542;
        padding: 10px;
        background-color: #ffffff;
        border-radius: 5px;
        border: 1px solid #dcdde1;
    }
    """

def is_admin():
    """检查是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    """主函数"""
    # 检查管理员权限
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.modifier = CursorModifier()
        self.current_language = Language.CHINESE  # 默认中文
        self.current_backup_dialog = None  # 添加对话框引用
        self.setup_ui()
        
        # 启动后自动显示关于信息
        QTimer.singleShot(100, self.show_about)  # 使用计时器延迟显示，确保窗口已完全加载
        
    def setup_ui(self):
        """设置主界面"""
        self.setWindowTitle(self.current_language['title'])
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(StyleSheet.MAIN)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 水平布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 左侧面板 - 垂直布局
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 版本信息
        version = self.modifier.get_cursor_version()
        version_label = QLabel(self.current_language['version'].format(
            version or MESSAGES['not_found']))
        version_label.setObjectName("version_label")
        version_label.setFont(QFont('Arial', 10))
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(version_label)
        
        # 功能按钮
        self.create_buttons(left_layout)
        
        # 添加底部弹簧
        left_layout.addStretch()
        
        # 右侧日志区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 日志标题
        log_title = QLabel(self.current_language['log_title'])
        log_title.setObjectName("log_title")
        log_title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        log_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(log_title)
        
        # 日志显示区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont('Consolas', 10))
        self.log_area.setMinimumWidth(400)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 5px;
                padding: 10px;
                color: #2f3542;
            }
        """)
        
        # 添加初始日志
        self.log("程序启动...")
        
        right_layout.addWidget(self.log_area)
        
        # 添加左右面板到主布局
        main_layout.addWidget(left_panel, 1)  # 1是拉伸因子
        main_layout.addWidget(right_panel, 2)  # 2是拉伸因子，使右侧更宽
        
        # 状态栏
        self.statusBar().showMessage(self.current_language['status_ready'])
        
        # 初始化更新控制按钮状态
        self.update_update_control_buttons()
        
    def create_buttons(self, layout):
        """创建功能按钮"""
        button_frame = QFrame()
        button_layout = QVBoxLayout(button_frame)
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分组按钮
        groups = [
            ('id_management', [
                ('generate', self.generate_new_config),
                ('view_current', self.view_current_config)
            ]),
            ('backup_management', [
                ('view_backup', self.manage_backups),
                ('create_backup', self.manual_backup)
            ]),
            ('update_control', [
                ('disable_update', self.disable_auto_update),
                ('enable_update', self.enable_auto_update)
            ]),
            ('others', [
                ('about', self.show_about)
            ])
        ]
        
        # 添加所有按钮
        for group_name, buttons in groups:
            # 添加分组按钮
            for btn_name, handler in buttons:
                btn = QPushButton(self.current_language['buttons'][group_name][btn_name])
                btn.setMinimumHeight(50)
                btn.clicked.connect(handler)
                button_layout.addWidget(btn)
            
            # 在组之间添加一点空间
            if group_name != 'others':  # 最后一组不需要添加间距
                button_layout.addSpacing(10)
        
        # 添加语言切换按钮
        button_layout.addSpacing(20)
        lang_btn = QPushButton(self.current_language['buttons']['others']['switch_lang'])
        lang_btn.setMinimumHeight(50)
        lang_btn.clicked.connect(self.switch_language)
        button_layout.addWidget(lang_btn)
        
        layout.addWidget(button_frame)

    def log(self, message):
        """添加日志"""
        try:
            # 检查 log_area 是否存在
            if not hasattr(self, 'log_area'):
                print("Error: log_area not initialized")
                return
            
            # 添加时间戳
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            
            # 添加日志到文本框并立即刷新
            self.log_area.append(formatted_message)
            self.log_area.repaint()
            
            # 确保滚动到最新内容
            cursor = self.log_area.textCursor()
            cursor.movePosition(cursor.End)
            self.log_area.setTextCursor(cursor)
            
            # 强制处理事件
            QApplication.processEvents()
            
        except Exception as e:
            print(f"Error in logging: {str(e)}")
            import traceback
            traceback.print_exc()

    def generate_new_config(self):
        """生成新的配置"""
        try:
            # 检查并关闭 Cursor 进程
            self.log("检查 Cursor 进程...")
            if not self.modifier.close_cursor_process():
                return False
            
            # 生成新的 ID
            self.log("正在生成新的 ID...")
            
            # 生成 MAC_MACHINE_ID (标准UUID格式)
            mac_machine_id = str(uuid.uuid4())
            
            # 生成 UUID (标准UUID格式)
            device_id = str(uuid.uuid4())
            
            # 生成 MACHINE_ID (特殊格式: auth0|user_ + 随机字符)
            prefix = "auth0|user_"
            prefix_hex = prefix.encode('utf-8').hex()
            random_part = ''.join(random.choices('0123456789abcdef', k=64))
            machine_id = f"{prefix_hex}{random_part}"
            
            # 生成 SQM_ID (大写的UUID，带花括号)
            sqm_id = "{" + str(uuid.uuid4()).upper() + "}"
            
            # 读取现有配置
            if not os.path.exists(self.modifier.storage_file):
                self.log("未找到配置文件，将创建新配置")
                config = {}
            else:
                with open(self.modifier.storage_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 创建备份
            self.modifier.create_manual_backup()
            
            # 更新配置
            config.update({
                'telemetry.machineId': machine_id,
                'telemetry.macMachineId': mac_machine_id,
                'telemetry.devDeviceId': device_id,
                'telemetry.sqmId': sqm_id
            })
            
            # 保存配置
            os.makedirs(os.path.dirname(self.modifier.storage_file), exist_ok=True)
            with open(self.modifier.storage_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            self.log("配置已更新:")
            self.log(f"machineId: {machine_id}")
            self.log(f"macMachineId: {mac_machine_id}")
            self.log(f"devDeviceId: {device_id}")
            self.log(f"sqmId: {sqm_id}")
            
            return True
            
        except Exception as e:
            self.log(f"生成配置时出错: {str(e)}")
            return False

    def manage_backups(self):
        """管理备份"""
        self.log("正在查看备份...")
        
        backups = self.modifier.list_backups()
        if not backups:
            self.log("未找到任何备份")
            QMessageBox.information(
                self,
                self.current_language['messages']['info'],
                self.current_language['messages']['no_backups']
            )
            return
        
        self.log(f"找到 {len(backups)} 个备份")
        
        # 添加详细的备份信息到日志
        self.log("\n" + self.current_language['messages']['log']['backup_title'])
        
        for i, backup in enumerate(backups, 1):
            self.log("\n" + "-" * 20 + f" 备份 {i} " + "-" * 20 + "\n")
            
            # 获取并显示备份详细信息
            backup_info = self.modifier.get_backup_info(backup, self.current_language)
            self.log(backup_info)
        
        self.log("\n" + "-" * 50)  # 分隔线
        
        # 显示备份管理对话框
        self.current_backup_dialog = BackupDialog(self, backups, self.modifier)
        self.current_backup_dialog.exec()

    def disable_auto_update(self):
        """禁用自动更新"""
        self.log("正在禁用自动更新...")
        if self.modifier.disable_auto_update():
            success_msg = self.current_language['messages']['update_disabled']
            self.log(success_msg)
            QMessageBox.information(
                self,
                self.current_language['messages']['success'],
                success_msg
            )
            # 更新按钮状态
            self.update_update_control_buttons()
        else:
            self.log("禁用自动更新失败")
            
    def enable_auto_update(self):
        """恢复自动更新"""
        self.log("正在启用自动更新...")
        if self.modifier.enable_auto_update():
            success_msg = self.current_language['messages']['update_enabled']
            self.log(success_msg)
            QMessageBox.information(
                self,
                self.current_language['messages']['success'],
                success_msg
            )
            # 更新按钮状态
            self.update_update_control_buttons()
        else:
            self.log("启用自动更新失败")
            
    def manual_backup(self):
        """手动备份"""
        self.log("开始创建手动备份...")
        backup_path = self.modifier.create_manual_backup()
        if backup_path:
            success_msg = self.current_language['messages']['backup_success'].format(backup_path)
            self.log(success_msg)
            QMessageBox.information(
                self,
                self.current_language['messages']['success'],
                success_msg
            )
        else:
            self.log("备份创建失败")
            
    def show_about(self):
        """显示关于信息"""
        self.log("正在显示关于信息...")
        notes = self.current_language['messages']['notes']
        about_text = self.current_language['about'].format(
            admin=notes['admin'],
            backup=notes['backup'],
            language=notes['language'],
            frequency=notes['frequency'],
            purpose=notes['purpose']
        )
        QMessageBox.about(
            self,
            self.current_language['buttons']['others']['about'],
            about_text
        )
        self.log("关于信息显示完成")

    def switch_language(self):
        """切换语言"""
        old_lang = "中文" if self.current_language == Language.CHINESE else "English"
        new_lang = "English" if self.current_language == Language.CHINESE else "中文"
        self.log(f"正在切换语言: {old_lang} -> {new_lang}")
        
        self.current_language = (
            Language.ENGLISH if self.current_language == Language.CHINESE 
            else Language.CHINESE
        )
        # 更新界面文本
        self.update_ui_text()
        
        # 更新所有打开的对话框
        for dialog in self.findChildren(BackupDialog):
            dialog.current_language = self.current_language
            dialog.update_ui_text()
        
        self.log(f"语言切换完成: {new_lang}")
    
    def update_ui_text(self):
        """更新界面文本"""
        try:
            # 更新窗口标题
            self.setWindowTitle(self.current_language['title'])
            
            # 更新版本标签
            version_label = self.findChild(QLabel, "version_label")
            if version_label:
                version = self.modifier.get_cursor_version()
                version_label.setText(
                    self.current_language['version'].format(version or MESSAGES['not_found'])
                )
            
            # 更新日志标题
            log_title = self.findChild(QLabel, "log_title")
            if log_title:
                log_title.setText(self.current_language['log_title'])
            
            # 更新状态栏
            self.statusBar().showMessage(self.current_language['status_ready'])
            
            # 更新按钮文本
            buttons = self.findChildren(QPushButton)
            if not buttons:
                return
            
            # 获取所有按钮的文本
            button_texts = []
            for group_name, group_buttons in [
                ('id_management', ['generate', 'view_current']),
                ('backup_management', ['view_backup', 'create_backup']),
                ('update_control', ['disable_update', 'enable_update']),
                ('others', ['about'])
            ]:
                for btn_name in group_buttons:
                    button_texts.append(
                        self.current_language['buttons'][group_name][btn_name]
                    )
            
            # 更新功能按钮
            for i, btn in enumerate(buttons[:-1]):  # 除了最后一个语言切换按钮
                if i < len(button_texts):
                    btn.setText(button_texts[i])
            
            # 更新语言切换按钮
            buttons[-1].setText(self.current_language['buttons']['others']['switch_lang'])
            
        except Exception as e:
            print(f"更新界面文本时出错: {e}")

    def view_current_config(self):
        """查看当前配置"""
        self.log("正在查看当前配置...")
        try:
            storage_path = self.modifier.get_storage_path()
            if not os.path.exists(storage_path):
                raise FileNotFoundError(f"配置文件不存在: {storage_path}")
            
            with open(storage_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 直接读取特定字段
            important_configs = {
                'machineId': config.get('telemetry.machineId', '61757468307c757365725fb38b5fabb389d433be1468bdb64b93a96adc9c101c'),
                'macMachineId': config.get('telemetry.macMachineId', 'e5b16fc8-03f8-4700-8b2c-a1c8904f6dc3'),
                'devDeviceId': config.get('telemetry.devDeviceId', '46595587-da2f-4af1-afc4-4bdd58e9ecf2'),
                'sqmId': config.get('telemetry.sqmId', '{6215A058-DE11-47EF-8B82-A030DFDA47D1}')
            }
            
            # 记录配置信息到日志
            self.log("\n当前配置信息:")
            for key, value in important_configs.items():
                self.log(f"{key}: {value}")
            
            # 显示对话框
            info = self.current_language['messages']['current_config']['format'].format(
                important_configs['machineId'],
                important_configs['macMachineId'],
                important_configs['devDeviceId'],
                important_configs['sqmId']
            )
            
            QMessageBox.information(
                self,
                self.current_language['messages']['current_config']['title'],
                info
            )
        except Exception as e:
            error_msg = str(e)
            self.log(f"查看配置时出错: {error_msg}")
            QMessageBox.warning(
                self,
                self.current_language['messages']['error'],
                error_msg
            )

    def update_update_control_buttons(self):
        """更新控制按钮状态"""
        try:
            # 获取当前更新状态
            is_update_enabled = self.modifier.is_auto_update_enabled()
            
            # 查找更新控制按钮
            for btn in self.findChildren(QPushButton):
                if btn.text() == self.current_language['buttons']['update_control']['disable_update']:
                    btn.setEnabled(is_update_enabled)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: %s;
                            color: white;
                            border: none;
                            padding: 10px;
                            border-radius: 5px;
                            font-size: 14px;
                            min-width: 200px;
                        }
                    """ % ('#4a69bd' if is_update_enabled else '#95a5a6'))
                elif btn.text() == self.current_language['buttons']['update_control']['enable_update']:
                    btn.setEnabled(not is_update_enabled)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: %s;
                            color: white;
                            border: none;
                            padding: 10px;
                            border-radius: 5px;
                            font-size: 14px;
                            min-width: 200px;
                        }
                    """ % ('#4a69bd' if not is_update_enabled else '#95a5a6'))
            
            # 更新状态栏显示当前更新状态
            status_msg = "自动更新: " + ("已启用" if is_update_enabled else "已禁用")
            self.statusBar().showMessage(status_msg)
            
            # 记录日志
            self.log(f"检测到更新状态: {status_msg}")
            
        except Exception as e:
            self.log(f"更新按钮状态时出错: {str(e)}")

class BackupDialog(QDialog):
    def __init__(self, parent, backups, modifier):
        super().__init__(parent)
        self.backups = backups
        self.modifier = modifier
        self.parent = parent
        self.current_language = parent.current_language
        self.content_widget = None  # 添加内容部件引用
        self.setup_ui()
        
    def setup_ui(self):
        """设置备份对话框界面"""
        self.setWindowTitle(self.current_language['dialog']['title'])
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f6fa;
            }
            QFrame {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #dcdde1;
            }
            QPushButton {
                background-color: #4a69bd;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6a89cc;
            }
            QLabel {
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        self.title_label = QLabel(self.current_language['dialog']['backup_list'])
        self.title_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # 创建滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; }")
        
        # 创建备份列表
        self.create_backup_list()
        
        layout.addWidget(self.scroll)
        
        # 关闭按钮
        close_btn = QPushButton(self.current_language['dialog']['close'])
        close_btn.setObjectName('close_btn')  # 设置对象名以便更新
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def create_backup_list(self):
        """创建备份列表"""
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(15)
        
        # 添加备份列表
        for i, backup in enumerate(self.backups, 1):
            frame = QFrame()
            frame_layout = QVBoxLayout(frame)
            
            # 备份信息
            info = self.modifier.get_backup_info(backup, self.current_language)
            info_label = QLabel(info)
            info_label.setObjectName(f"backup_info_{i-1}")
            info_label.setFont(QFont('Consolas', 9))
            frame_layout.addWidget(info_label)
            
            # 按钮容器
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setSpacing(10)
            
            # 恢复按钮
            restore_btn = QPushButton(self.current_language['dialog']['restore'])
            restore_btn.setObjectName('restore_btn')
            restore_btn.clicked.connect(lambda checked, b=backup: self.restore_backup(b))
            button_layout.addWidget(restore_btn)
            
            # 删除按钮
            delete_btn = QPushButton(self.current_language['dialog']['delete'])
            delete_btn.setObjectName('delete_btn')
            delete_btn.clicked.connect(lambda checked, b=backup: self.delete_backup(b))
            button_layout.addWidget(delete_btn)
            
            frame_layout.addWidget(button_container)
            content_layout.addWidget(frame)
        
        self.scroll.setWidget(self.content_widget)

    def restore_backup(self, backup):
        """恢复备份"""
        self.parent.log(f"准备恢复备份: {backup}")
        reply = QMessageBox.question(
            self,
            self.current_language['confirm']['title'],
            self.current_language['confirm']['restore'],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.parent.log("开始恢复备份...")
            if self.modifier.restore_backup(backup):
                success_msg = self.current_language['messages']['backup_restored']
                self.parent.log(success_msg)
                QMessageBox.information(
                    self,
                    self.current_language['messages']['success'],
                    success_msg
                )
                self.close()
            else:
                error_msg = self.current_language['messages']['restore_failed']
                self.parent.log(f"恢复失败: {error_msg}")
                QMessageBox.warning(
                    self,
                    self.current_language['messages']['error'],
                    error_msg
                )

    def delete_backup(self, backup):
        """删除备份"""
        self.parent.log(f"准备删除备份: {backup}")
        reply = QMessageBox.question(
            self,
            self.current_language['confirm']['title'],
            self.current_language['confirm']['delete'],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.parent.log("正在删除备份...")
                os.remove(backup)
                self.backups = self.modifier.list_backups()
                self.create_backup_list()
                
                success_msg = self.current_language['messages']['backup_deleted']
                self.parent.log(success_msg)
                QMessageBox.information(
                    self,
                    self.current_language['messages']['success'],
                    success_msg
                )
            except Exception as e:
                error_msg = f"{self.current_language['messages']['delete_failed']}: {str(e)}"
                self.parent.log(f"删除失败: {error_msg}")
                QMessageBox.warning(
                    self,
                    self.current_language['messages']['error'],
                    error_msg
                )

    def update_ui_text(self):
        """更新对话框的文本"""
        try:
            # 更新窗口标题
            self.setWindowTitle(self.current_language['dialog']['title'])
            
            # 更新标题标签
            if hasattr(self, 'title_label'):
                self.title_label.setText(self.current_language['dialog']['backup_list'])
            
            # 更新所有按钮
            for btn in self.findChildren(QPushButton):
                if btn.objectName() == 'restore_btn':
                    btn.setText(self.current_language['dialog']['restore'])
                elif btn.objectName() == 'delete_btn':
                    btn.setText(self.current_language['dialog']['delete'])
                elif btn.objectName() == 'close_btn':
                    btn.setText(self.current_language['dialog']['close'])
            
            # 更新备份信息标签
            for label in self.findChildren(QLabel):
                if label.objectName().startswith('backup_info_'):
                    backup_index = int(label.objectName().split('_')[-1])
                    if backup_index < len(self.backups):
                        info = self.modifier.get_backup_info(
                            self.backups[backup_index], 
                            self.current_language
                        )
                        label.setText(info)
                        
        except Exception as e:
            print(f"更新对话框文本时出错: {e}")

    def update_backups(self, new_backups):
        """更新备份列表"""
        self.backups = new_backups
        # 删除旧的内容部件
        if self.content_widget:
            self.content_widget.deleteLater()
        # 创建新的备份列表
        self.create_backup_list()

if __name__ == "__main__":
    main() 