import sys
import os
import json
import uuid
import shutil
import datetime
import subprocess
import ctypes
from pathlib import Path
from typing import Dict, Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QMessageBox, QTextEdit, 
                            QScrollArea, QFrame, QDialog, QHBoxLayout,
                            QLineEdit, QDialogButtonBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# 修改 MESSAGES 配置为中英文分离的格式
class Messages:
    """消息配置"""
    CHINESE = {
        'version': 'Cursor 版本: {}',
        'config_updated': '配置更新成功',
        'new_ids': '新的ID:',
        'no_backups': '未找到备份',
        'backup_restored': '备份恢复成功',
        'update_disabled': '自动更新已禁用',
        'config_not_found': '未找到配置文件',
        'kill_failed': '关闭Cursor进程失败: {}',
        'update_failed': '更新配置失败: {}',
        'process_killed': 'Cursor进程已成功关闭',
        'backup_created': '备份已创建: {}',
        'process_not_found': '未发现正在运行的Cursor进程',
        'about': '''
关于
----------------------------------------
Cursor ID 修改器 (macOS版)
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
• 需要管理员权限
• 修改前自动备份
• 支持中英双语
• 请勿频繁操作
• 仅供学习研究使用

作者: Ctrler
最后更新: 2025
----------------------------------------
''',
        'update_enabled': '自动更新已恢复',
        'backup_failed': '备份失败: {}',
        'closing_cursor': '正在关闭Cursor进程...',
    }
    
    ENGLISH = {
        'version': 'Cursor Version: {}',
        'config_updated': 'Configuration updated successfully',
        'new_ids': 'New IDs:',
        'no_backups': 'No backups found',
        'backup_restored': 'Backup restored successfully',
        'update_disabled': 'Auto-update disabled successfully',
        'config_not_found': 'Configuration file not found',
        'kill_failed': 'Failed to kill Cursor process: {}',
        'update_failed': 'Failed to update config: {}',
        'process_killed': 'Cursor process killed successfully',
        'backup_created': 'Backup created: {}',
        'process_not_found': 'No running Cursor process found',
        'about': '''
About
----------------------------------------
Cursor ID Modifier (macOS version)
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
• Requires administrator privileges
• Auto backup before modification
• Supports Chinese and English
• Do not operate frequently
• For learning and research purposes only

Author: Ctrler
Last Update: 2025
----------------------------------------
''',
        'update_enabled': 'Auto-update enabled successfully',
        'backup_failed': 'Backup failed: {}',
        'closing_cursor': 'Closing Cursor processes...',
    }

def is_admin():
    """检查是否具有管理员权限"""
    try:
        return os.geteuid() == 0
    except:
        return False

class PasswordDialog(QDialog):
    """管理员密码输入对话框"""
    def __init__(self, parent=None, language=None):
        super().__init__(parent)
        # 设置语言
        self.current_language = language or Language.CHINESE
        self.setup_ui()
    
    def setup_ui(self):
        # 根据当前语言设置标题
        title = "管理员权限" if self.current_language == Language.CHINESE else "Administrator Privileges"
        self.setWindowTitle(title)
        self.setFixedWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 图标和提示文本
        info_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setStyleSheet("""
            QLabel {
                background-image: url(':/warning.png');
                background-position: center;
                background-repeat: no-repeat;
            }
        """)
        info_layout.addWidget(icon_label)
        
        # 根据语言设置提示文本
        msg_text = ("需要管理员权限才能运行此程序。\n请输入管理员密码：" 
                   if self.current_language == Language.CHINESE 
                   else "Administrator privileges required.\nPlease enter your password:")
        msg_label = QLabel(msg_text)
        msg_label.setStyleSheet("QLabel { color: #2f3542; }")
        info_layout.addWidget(msg_label, 1)
        layout.addLayout(info_layout)
        
        # 密码输入框
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #dcdde1;
                border-radius: 5px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #4a69bd;
            }
        """)
        # 设置密码输入框的占位符文本
        placeholder = "输入密码" if self.current_language == Language.CHINESE else "Enter password"
        self.password_input.setPlaceholderText(placeholder)
        layout.addWidget(self.password_input)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        # 设置按钮文本
        ok_btn = button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if self.current_language == Language.CHINESE:
            ok_btn.setText("确定")
            cancel_btn.setText("取消")
        else:
            ok_btn.setText("OK")
            cancel_btn.setText("Cancel")
            
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 5px;
                min-width: 80px;
            }
            QPushButton[text="确定"], QPushButton[text="OK"] {
                background-color: #4a69bd;
                color: white;
                border: none;
            }
            QPushButton[text="确定"]:hover, QPushButton[text="OK"]:hover {
                background-color: #6a89cc;
            }
            QPushButton[text="取消"], QPushButton[text="Cancel"] {
                background-color: #f5f6fa;
                border: 1px solid #dcdde1;
                color: #2f3542;
            }
            QPushButton[text="取消"]:hover, QPushButton[text="Cancel"]:hover {
                background-color: #dcdde1;
            }
        """)
        layout.addWidget(button_box)
        
        # 设置回车键触发确定按钮
        self.password_input.returnPressed.connect(self.accept)
    
    def get_password(self):
        return self.password_input.text()

def run_as_admin():
    """以管理员权限运行"""
    if not is_admin():
        try:
            app = QApplication.instance()
            if not app:
                app = QApplication(sys.argv)
            
            # 显示密码输入对话框，传入当前语言设置
            dialog = PasswordDialog(language=Language.CHINESE)  # 或从配置中获取当前语言
            if dialog.exec() == QDialog.DialogCode.Accepted:
                password = dialog.get_password()
                # 使用获取的密码执行提权命令
                cmd = f'echo "{password}" | sudo -S "{sys.executable}" "{" ".join(sys.argv)}"'
                subprocess.run(cmd, shell=True, check=True)
                sys.exit(0)  # 退出当前非管理员进程
            else:
                sys.exit(1)  # 用户取消
        except subprocess.CalledProcessError:
            error_title = "错误" if Language.CHINESE else "Error"
            error_msg = ("密码错误或权限验证失败。" if Language.CHINESE 
                        else "Incorrect password or authentication failed.")
            QMessageBox.critical(None, error_title, error_msg,
                               QMessageBox.StandardButton.Ok)
            sys.exit(1)
        except Exception as e:
            error_title = "错误" if Language.CHINESE else "Error"
            error_msg = (f"获取管理员权限失败: {e}" if Language.CHINESE 
                        else f"Failed to obtain administrator privileges: {e}")
            QMessageBox.critical(None, error_title, error_msg,
                               QMessageBox.StandardButton.Ok)
            sys.exit(1)

class CursorModifier:
    """Cursor配置修改器类 (macOS版)"""
    def __init__(self):
        self.home = str(Path.home())
        self.storage_file = Path(f"{self.home}/Library/Application Support/Cursor/User/globalStorage/storage.json")
        self.backup_dir = Path(f"{self.home}/Library/Application Support/Cursor/User/globalStorage/backups")
        self.cursor_app = Path("/Applications/Cursor.app")
        self.current_language = Messages.CHINESE  # 默认中文
        self.log_callback = lambda x: None  # 默认空日志回调

    def set_language(self, language):
        """设置语言"""
        self.current_language = language

    def get_cursor_version(self) -> Optional[str]:
        """获取Cursor版本"""
        try:
            package_path = self.cursor_app / "Contents/Resources/app/package.json"
            if package_path.exists():
                with open(package_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('version')
        except Exception as e:
            print(f"读取版本出错: {e}")
        return None

    def close_cursor_processes(self):
        """关闭所有Cursor进程"""
        try:
            result = subprocess.run(['pgrep', '-f', 'Cursor'], capture_output=True)
            if result.returncode == 0:
                subprocess.run(['pkill', '-f', 'Cursor'], check=True)
                return True
            return False
        except Exception as e:
            print(f"关闭进程失败: {e}")
            return False

    def backup_config(self, auto_backup: bool = False) -> Optional[Path]:
        """备份当前配置"""
        try:
            if not self.backup_dir.exists():
                os.makedirs(self.backup_dir, mode=0o755, exist_ok=True)
            
            if not self.storage_file.exists():
                return None
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f"storage.json.backup_{timestamp}"
            
            # 使用 sudo 复制文件
            subprocess.run(['sudo', 'cp', str(self.storage_file), str(backup_path)], check=True)
            subprocess.run(['sudo', 'chmod', '644', str(backup_path)], check=True)
            
            return backup_path
        except Exception as e:
            error_msg = (f"备份失败: {e}" if self.current_language == Messages.CHINESE 
                        else f"Backup failed: {e}")
            print(error_msg)
            return None

    def generate_ids(self) -> Dict[str, str]:
        """生成新的设备ID"""
        def get_random_hex(length: int) -> str:
            return os.urandom(length).hex()

        prefix = "auth0|user_"
        prefix_hex = ''.join(f'{ord(c):02x}' for c in prefix)
        random_part = get_random_hex(32 - len(prefix_hex) // 2)
        machine_id = f"{prefix_hex}{random_part}"

        return {
            'machineId': machine_id,
            'macMachineId': str(uuid.uuid4()),
            'devDeviceId': str(uuid.uuid4()).lower(),
            'sqmId': f"{{{str(uuid.uuid4()).upper()}}}"
        }

    def update_system_uuid(self) -> bool:
        """更新系统UUID"""
        try:
            new_uuid = str(uuid.uuid4())
            subprocess.run(['sudo', 'nvram', f'SystemUUID={new_uuid}'], check=True)
            return True
        except Exception as e:
            print(f"更新系统UUID失败: {e}")
            return False

    def update_config(self, new_ids: Dict[str, str]) -> bool:
        """更新配置文件"""
        try:
            if not self.storage_file.exists():
                return False

            # 1. 读取当前配置
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 2. 更新配置
            for key, value in new_ids.items():
                config[f'telemetry.{key}'] = value

            # 3. 使用临时文件进行写入
            temp_file = self.storage_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            # 4. 替换原文件
            subprocess.run(['sudo', 'mv', str(temp_file), str(self.storage_file)], check=True)
            subprocess.run(['sudo', 'chmod', '444', str(self.storage_file)], check=True)  # 设置为只读

            # 5. 更新 state.json
            state_file = self.storage_file.parent / "state.json"
            if state_file.exists():
                try:
                    with open(state_file, 'r', encoding='utf-8') as f:
                        state = json.load(f)
                    state['machineId'] = new_ids['machineId']
                    
                    temp_state = state_file.with_suffix('.tmp')
                    with open(temp_state, 'w', encoding='utf-8') as f:
                        json.dump(state, f, indent=2)
                    
                    subprocess.run(['sudo', 'mv', str(temp_state), str(state_file)], check=True)
                    subprocess.run(['sudo', 'chmod', '444', str(state_file)], check=True)
                except Exception as e:
                    print(f"更新 state.json 失败: {e}")

            # 6. 清理缓存
            cache_dirs = [
                Path(f"{self.home}/Library/Caches/Cursor"),
                Path(f"{self.home}/Library/Application Support/Cursor/Cache"),
                Path(f"{self.home}/Library/Application Support/Cursor/Code Cache"),
                Path(f"{self.home}/Library/Application Support/Cursor/Session Storage"),
            ]
            
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    try:
                        subprocess.run(['sudo', 'rm', '-rf', str(cache_dir)], check=True)
                    except Exception as e:
                        print(f"清理缓存失败 {cache_dir}: {e}")

            return True
        except Exception as e:
            print(f"更新配置失败: {e}")
            return False

    def disable_auto_update(self) -> bool:
        """禁用自动更新"""
        updater_path = Path(f"{self.home}/Library/Application Support/Caches/cursor-updater")
        try:
            # 1. 如果更新器文件存在，先删除它
            if updater_path.exists():
                self.log_callback(f"正在删除更新器文件: {updater_path}")
                subprocess.run(['sudo', 'rm', '-rf', str(updater_path)], check=True)
                self.log_callback("更新器文件删除成功")
            
            # 2. 创建一个空文件
            self.log_callback(f"正在创建空文件: {updater_path}")
            subprocess.run(['sudo', 'touch', str(updater_path)], check=True)
            self.log_callback("空文件创建成功")
            
            # 3. 将文件设置为只读，防止被修改
            self.log_callback("正在设置文件权限为只读(444)")
            subprocess.run(['sudo', 'chmod', '444', str(updater_path)], check=True)
            self.log_callback("文件权限设置成功")
            
            return True
        except Exception as e:
            error_msg = f"禁用自动更新失败: {e}"
            self.log_callback(error_msg)
            return False

    def enable_auto_update(self) -> bool:
        """恢复自动更新"""
        updater_path = Path(f"{self.home}/Library/Application Support/Caches/cursor-updater")
        try:
            # 删除更新器文件
            if updater_path.exists():
                self.log_callback(f"正在删除更新器文件: {updater_path}")
                subprocess.run(['sudo', 'rm', '-f', str(updater_path)], check=True)
                self.log_callback("更新器文件删除成功")
            else:
                self.log_callback("更新器文件不存在，无需删除")
            return True
        except Exception as e:
            error_msg = f"恢复自动更新失败: {e}"
            self.log_callback(error_msg)
            return False

    def list_backups(self) -> list:
        """列出所有备份"""
        if not self.backup_dir.exists():
            return []
        
        backups = sorted(self.backup_dir.glob('storage.json.backup_*'))
        return backups

    def restore_backup(self, backup_path: Path) -> bool:
        """恢复备份"""
        try:
            if backup_path.exists():
                shutil.copy2(backup_path, self.storage_file)
                os.chmod(self.storage_file, 0o444)
                return True
            return False
        except Exception as e:
            print(f"恢复备份失败: {e}")
            return False

    def get_backup_info(self, backup_path: Path) -> str:
        """获取备份信息"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                telemetry_config = {k: v for k, v in config.items() if k.startswith('telemetry.')}
                
            created_time = datetime.datetime.fromtimestamp(backup_path.stat().st_mtime)
            
            if self.current_language == Messages.CHINESE:
                return f"""
备份信息:
文件名: {backup_path.name}
创建时间: {created_time.strftime('%Y-%m-%d %H:%M:%S')}
配置内容:
{json.dumps(telemetry_config, indent=2, ensure_ascii=False)}
"""
            else:
                return f"""
Backup Information:
Filename: {backup_path.name}
Created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}
Configuration:
{json.dumps(telemetry_config, indent=2, ensure_ascii=False)}
"""
        except Exception as e:
            return (f"读取备份失败: {e}" if self.current_language == Messages.CHINESE 
                   else f"Failed to read backup: {e}")

    def view_current_config(self) -> Optional[Dict[str, str]]:
        """查看当前配置"""
        try:
            if not self.storage_file.exists():
                return None

            # 使用 sudo 读取文件
            result = subprocess.run(['sudo', 'cat', str(self.storage_file)], 
                                  capture_output=True, text=True, check=True)
            config = json.loads(result.stdout)
            telemetry_config = {k: v for k, v in config.items() if k.startswith('telemetry.')}
            return telemetry_config
        except Exception as e:
            error_msg = (f"读取配置失败: {e}" if self.current_language == Messages.CHINESE 
                        else f"Failed to read configuration: {e}")
            print(error_msg)
            return None

    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.log_callback = callback

class Language:
    """语言配置"""
    CHINESE = {
        'title': "Cursor ID 修改器 (macOS)",
        'version': "Cursor 版本: {}",
        'log_title': "操作日志",
        'status_ready': "就绪",
        'buttons': {
            'id_management': {
                'title': "ID 管理",
                'generate': "生成新配置",
                'view_current': "查看当前配置"
            },
            'backup_management': {
                'title': "备份管理",
                'view_backup': "查看备份",
                'create_backup': "创建备份"
            },
            'update_control': {
                'title': "更新控制",
                'disable_update': "禁用自动更新",
                'enable_update': "恢复自动更新"
            },
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
            'close': "❌ 关闭",
            'config_title': "当前配置"
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
            'backup_deleted': "备份已删除",
            'delete_failed': "删除失败: {}"
        },
        'status': {
            'disabled': " (当前已禁用)",
            'enabled': " (当前已启用)"
        }
    }
    
    ENGLISH = {
        'title': "Cursor ID Modifier (macOS)",
        'version': "Cursor Version: {}",
        'log_title': "Operation Log",
        'status_ready': "Ready",
        'buttons': {
            'id_management': {
                'title': "ID Management",
                'generate': "Generate New Config",
                'view_current': "View Current Config"
            },
            'backup_management': {
                'title': "Backup Management",
                'view_backup': "View Backups",
                'create_backup': "Create Backup"
            },
            'update_control': {
                'title': "Update Control",
                'disable_update': "Disable Auto-update",
                'enable_update': "Enable Auto-update"
            },
            'others': {
                'title': "Others",
                'about': "About",
                'switch_lang': "Switch to Chinese"
            }
        },
        'dialog': {
            'title': "Backup Management",
            'backup_list': "Backup List",
            'restore': "♻️ Restore Backup",
            'delete': "🗑️ Delete Backup",
            'close': "❌ Close",
            'config_title': "Current Configuration"
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
            'backup_deleted': "Backup deleted",
            'delete_failed': "Delete failed: {}"
        },
        'status': {
            'disabled': " (Currently Disabled)",
            'enabled': " (Currently Enabled)"
        }
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
        padding: 0px;  /* 移除内边距 */
        border-radius: 5px;
        font-size: 14px;
        min-width: 200px;
        height: 42px;  /* 固定高度 */
    }
    
    QPushButton:hover {
        background-color: #6a89cc;
    }
    
    QPushButton:pressed {
        background-color: #3c55a5;
    }
    
    QPushButton:disabled {
        background-color: #95afc0;  /* 禁用状态的颜色 */
    }
    
    QTextEdit {
        background-color: #ffffff;
        border: 1px solid #dcdde1;
        border-radius: 5px;
        padding: 5px;
        font-family: Menlo;
        color: #1e3799;
    }
    
    QLabel#version_label {
        color: #2f3542;
        padding: 10px;
        background-color: #ffffff;
        border-radius: 5px;
        border: 1px solid #dcdde1;
    }
    """

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.modifier = CursorModifier()
        self.current_language = Language.CHINESE
        self.modifier.set_language(Messages.CHINESE)
        # 设置日志回调
        self.modifier.set_log_callback(self.log)
        self.setup_ui()
        
    def setup_ui(self):
        """设置主界面"""
        self.setWindowTitle(self.current_language['title'])
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(StyleSheet.MAIN)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 左侧面板
        left_panel = self.create_left_panel()
        left_panel.setFixedWidth(300)  # 固定左侧面板宽度
        
        # 右侧日志区域
        right_panel = self.create_right_panel()
        
        # 添加到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # 状态栏
        self.statusBar().showMessage(self.current_language['status_ready'])
        
    def create_left_panel(self):
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 版本信息
        version = self.modifier.get_cursor_version()
        version_label = QLabel(self.current_language['version'].format(
            version or "未找到"
        ))
        version_label.setObjectName("version_label")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setFixedHeight(42)  # 设置固定高度
        layout.addWidget(version_label)
        
        # 添加功能按钮
        self.create_buttons(layout)
        
        # 添加底部弹簧
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self):
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建顶部容器用于对齐
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # 日志标题
        log_title = QLabel(self.current_language['log_title'])
        log_title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        log_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        log_title.setStyleSheet("""
            QLabel {
                color: #1e3799;
                padding: 5px;
                background-color: #ffffff;
                border-radius: 5px;
                border: 1px solid #dcdde1;
            }
        """)
        log_title.setObjectName("log_title")
        log_title.setFixedHeight(42)  # 设置固定高度，与版本标签对齐
        top_layout.addWidget(log_title)
        
        layout.addWidget(top_container)
        
        # 日志显示区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont('Menlo', 10))
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #1e3799;
                border: 1px solid #dcdde1;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.log_area)
        
        # 添加初始日志
        self.log("程序启动...")
        
        return panel
    
    def create_buttons(self, layout):
        """创建功能按钮"""
        button_frame = QFrame()
        button_layout = QVBoxLayout(button_frame)
        button_layout.setSpacing(10)  # 设置按钮间距
        button_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        
        # 创建分组按钮
        groups = [
            ('id_management', [
                ('generate', self.generate_new_config),
                ('view_current', self.view_current_config)
            ]),
            ('backup_management', [
                ('view_backup', self.view_backups),
                ('create_backup', self.create_backup)
            ]),
            ('update_control', [
                ('disable_update', self.disable_auto_update),
                ('enable_update', self.enable_auto_update)
            ]),
            ('others', [
                ('about', self.show_about),
                ('switch_lang', self.switch_language)
            ])
        ]
        
        for group_name, buttons in groups:
            # 添加按钮
            for btn_name, handler in buttons:
                btn = QPushButton(self.current_language['buttons'][group_name][btn_name])
                btn.setObjectName(f"{group_name}_{btn_name}")
                btn.clicked.connect(handler)
                btn.setFixedHeight(42)  # 设置按钮固定高度
                
                # 为更新控制按钮添加状态文字
                if group_name == 'update_control':
                    # 检查更新器状态
                    updater_path = Path(f"{self.modifier.home}/Library/Application Support/Caches/cursor-updater")
                    is_update_disabled = updater_path.exists() and updater_path.stat().st_size == 0
                    
                    if btn_name == 'disable_update':
                        if is_update_disabled:
                            btn.setText(self.current_language['buttons'][group_name][btn_name] + 
                                      self.current_language['status']['disabled'])
                            btn.setEnabled(False)
                    elif btn_name == 'enable_update':
                        if not is_update_disabled:
                            btn.setText(self.current_language['buttons'][group_name][btn_name] + 
                                      self.current_language['status']['enabled'])
                            btn.setEnabled(False)
                
                button_layout.addWidget(btn)
            
            # 添加分组间距
            if group_name != 'others':
                button_layout.addSpacing(15)  # 增加组间距
        
        layout.addWidget(button_frame)

    def log(self, message):
        """添加日志"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_area.append(f'<span style="color: #1e3799;">[{timestamp}] {message}</span>')
        
    # 实现功能按钮的处理方法
    def generate_new_config(self):
        """生成新配置"""
        if QMessageBox.question(
            self,
            self.current_language['confirm']['title'],
            self.current_language['confirm']['generate'],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.log("正在关闭Cursor进程...")
            self.modifier.close_cursor_processes()
            backup_path = self.modifier.backup_config(auto_backup=True)
            if backup_path:
                self.log(f"已创建备份: {backup_path}")
                new_ids = self.modifier.generate_ids()
                if self.modifier.update_system_uuid() and self.modifier.update_config(new_ids):
                    # 在日志区域显示
                    self.log("配置已更新")
                    self.log("\n新的ID:")
                    formatted_ids = "\n".join([f"{k}: {v}" for k, v in new_ids.items()])
                    self.log(formatted_ids)
                    
                    # 同时弹出消息框显示
                    QMessageBox.information(
                        self,
                        self.current_language['messages']['success'],
                        f"""配置已更新成功！

新的ID:
{formatted_ids}

请按以下步骤操作：
1. 立即关闭 Cursor
2. 清除浏览器中 Cursor 网站的所有数据
3. 重启电脑
4. 使用新账号登录 Cursor"""
                    )
                else:
                    QMessageBox.warning(
                        self,
                        self.current_language['messages']['error'],
                        "更新配置失败"
                    )
    
    def view_current_config(self):
        """查看当前配置"""
        viewing_msg = ("正在查看当前配置..." if self.current_language == Language.CHINESE 
                      else "Viewing current configuration...")
        self.log(viewing_msg)
        
        config = self.modifier.view_current_config()
        if config:
            # 在日志中显示
            current_config = ("当前配置:" if self.current_language == Language.CHINESE 
                             else "Current configuration:")
            self.log(current_config)
            for key, value in config.items():
                self.log(f"{key}: {value}")
            
            # 显示配置对话框
            dialog = ConfigViewDialog(self, config)
            dialog.exec()
        else:
            not_found = ("未找到配置" if self.current_language == Language.CHINESE 
                        else "Configuration not found")
            self.log(not_found)
    
    def view_backups(self):
        """查看备份"""
        self.log("正在查看备份...")
        backups = self.modifier.list_backups()
        if not backups:
            self.log("未找到备份")
            return
        
        dialog = BackupDialog(self, backups, self.modifier)
        dialog.exec()
    
    def create_backup(self):
        """创建备份"""
        creating_msg = ("正在创建备份..." if self.current_language == Language.CHINESE 
                       else "Creating backup...")
        self.log(creating_msg)
        backup_path = self.modifier.backup_config()
        if backup_path:
            success_msg = (f"备份创建成功: {backup_path}" if self.current_language == Language.CHINESE 
                          else f"Backup created successfully: {backup_path}")
            self.log(success_msg)
    
    def disable_auto_update(self):
        """禁用自动更新"""
        disabling_msg = ("正在禁用自动更新..." if self.current_language == Language.CHINESE 
                        else "Disabling auto-update...")
        self.log(disabling_msg)
        
        # 检查更新器状态
        updater_path = Path(f"{self.modifier.home}/Library/Application Support/Caches/cursor-updater")
        if updater_path.exists() and updater_path.stat().st_size == 0:
            # 已经是禁用状态
            status_msg = ("自动更新已经处于禁用状态" if self.current_language == Language.CHINESE 
                         else "Auto-update is already disabled")
            self.log(status_msg)
            QMessageBox.information(
                self,
                self.current_language['messages']['info'],
                status_msg
            )
            return
        
        if self.modifier.disable_auto_update():
            disabled_msg = ("自动更新已成功禁用" if self.current_language == Language.CHINESE 
                           else "Auto-update has been disabled successfully")
            self.log(disabled_msg)
            QMessageBox.information(
                self,
                self.current_language['messages']['success'],
                disabled_msg
            )
            self.update_update_control_buttons()  # 更新按钮状态

    def enable_auto_update(self):
        """恢复自动更新"""
        enabling_msg = ("正在恢复自动更新..." if self.current_language == Language.CHINESE 
                       else "Enabling auto-update...")
        self.log(enabling_msg)
        
        # 检查更新器状态
        updater_path = Path(f"{self.modifier.home}/Library/Application Support/Caches/cursor-updater")
        if not updater_path.exists() or updater_path.stat().st_size > 0:
            # 已经是启用状态
            status_msg = ("自动更新已经处于启用状态" if self.current_language == Language.CHINESE 
                         else "Auto-update is already enabled")
            self.log(status_msg)
            QMessageBox.information(
                self,
                self.current_language['messages']['info'],
                status_msg
            )
            return
        
        if self.modifier.enable_auto_update():
            enabled_msg = ("自动更新已成功恢复" if self.current_language == Language.CHINESE 
                          else "Auto-update has been enabled successfully")
            self.log(enabled_msg)
            QMessageBox.information(
                self,
                self.current_language['messages']['success'],
                enabled_msg
            )
            self.update_update_control_buttons()  # 更新按钮状态
    
    def show_about(self):
        """显示关于信息"""
        QMessageBox.about(
            self,
            self.current_language['buttons']['others']['about'],
            self.modifier.current_language['about']
        )
    
    def switch_language(self):
        """切换语言"""
        self.current_language = (
            Language.ENGLISH if self.current_language == Language.CHINESE 
            else Language.CHINESE
        )
        self.modifier.set_language(
            Messages.ENGLISH if self.current_language == Language.ENGLISH 
            else Messages.CHINESE
        )
        self.update_ui_text()
        
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
                    self.current_language['version'].format(version or "N/A")
                )
            
            # 更新日志标题
            log_title = self.findChild(QLabel, "log_title")
            if log_title:
                log_title.setText(self.current_language['log_title'])
            
            # 更新状态栏
            self.statusBar().showMessage(self.current_language['status_ready'])
            
            # 更新所有按钮
            for group_name, buttons in [
                ('id_management', ['generate', 'view_current']),
                ('backup_management', ['view_backup', 'create_backup']),
                ('update_control', ['disable_update', 'enable_update']),
                ('others', ['about', 'switch_lang'])
            ]:
                # 更新按钮文本
                for btn_name in buttons:
                    btn = self.findChild(QPushButton, f"{group_name}_{btn_name}")
                    if btn and group_name != 'update_control':  # 跳过更新控制按钮，由专门的方法处理
                        btn.setText(self.current_language['buttons'][group_name][btn_name])
            
            # 更新更新控制按钮的状态和文字
            self.update_update_control_buttons()
            
        except Exception as e:
            print(f"更新界面文本时出错: {e}")

    def update_update_control_buttons(self):
        """更新控制按钮状态"""
        updater_path = Path(f"{self.modifier.home}/Library/Application Support/Caches/cursor-updater")
        is_update_disabled = updater_path.exists() and updater_path.stat().st_size == 0
        
        disable_btn = self.findChild(QPushButton, "update_control_disable_update")
        enable_btn = self.findChild(QPushButton, "update_control_enable_update")
        
        if disable_btn and enable_btn:
            if is_update_disabled:
                # 更新已禁用
                disable_btn.setText(self.current_language['buttons']['update_control']['disable_update'] + 
                                  self.current_language['status']['disabled'])
                disable_btn.setEnabled(False)
                
                enable_btn.setText(self.current_language['buttons']['update_control']['enable_update'])
                enable_btn.setEnabled(True)
            else:
                # 更新已启用
                enable_btn.setText(self.current_language['buttons']['update_control']['enable_update'] + 
                                 self.current_language['status']['enabled'])
                enable_btn.setEnabled(False)
                
                disable_btn.setText(self.current_language['buttons']['update_control']['disable_update'])
                disable_btn.setEnabled(True)

class BackupDialog(QDialog):
    """备份管理对话框"""
    def __init__(self, parent, backups, modifier):
        super().__init__(parent)
        self.backups = backups
        self.modifier = modifier
        self.parent = parent
        self.current_language = parent.current_language
        self.setup_ui()
    
    def setup_ui(self):
        """设置对话框界面"""
        self.setWindowTitle(self.current_language['dialog']['title'])
        self.setMinimumWidth(800)  # 增加最小宽度
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 添加备份列表标题
        title_label = QLabel(self.current_language['dialog']['backup_list'])
        title_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 添加备份列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(400)  # 增加最小高度
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)
        
        for backup in self.backups:
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #dcdde1;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
            frame_layout = QVBoxLayout(frame)
            frame_layout.setSpacing(10)
            
            # 备份信息
            info_area = QTextEdit()
            info_area.setReadOnly(True)
            info_area.setFont(QFont('Menlo', 10))
            info_area.setStyleSheet("""
                QTextEdit {
                    background-color: transparent;
                    border: none;
                    color: #2f3542;
                }
            """)
            info_area.setText(self.modifier.get_backup_info(backup))
            info_area.document().adjustSize()
            doc_height = info_area.document().size().height()
            info_area.setFixedHeight(min(doc_height + 20, 200))
            
            frame_layout.addWidget(info_area)
            
            # 按钮
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(10)
            
            restore_btn = QPushButton(self.current_language['dialog']['restore'])
            restore_btn.setFixedWidth(150)
            restore_btn.clicked.connect(lambda checked, b=backup: self.restore_backup(b))
            btn_layout.addWidget(restore_btn)
            
            delete_btn = QPushButton(self.current_language['dialog']['delete'])
            delete_btn.setFixedWidth(150)
            delete_btn.clicked.connect(lambda checked, b=backup: self.delete_backup(b))
            btn_layout.addWidget(delete_btn)
            
            btn_layout.addStretch()
            frame_layout.addLayout(btn_layout)
            content_layout.addWidget(frame)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # 关闭按钮
        close_btn = QPushButton(self.current_language['dialog']['close'])
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignCenter)
    
    def restore_backup(self, backup):
        """恢复备份"""
        reply = QMessageBox.question(
            self,
            self.current_language['confirm']['title'],
            self.current_language['confirm']['restore'],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.modifier.restore_backup(backup):
                QMessageBox.information(
                    self,
                    self.current_language['messages']['success'],
                    self.current_language['messages']['backup_restored']
                )
                self.close()
            else:
                QMessageBox.warning(
                    self,
                    self.current_language['messages']['error'],
                    self.current_language['messages']['restore_failed']
                )
    
    def delete_backup(self, backup):
        """删除备份"""
        reply = QMessageBox.question(
            self,
            self.current_language['confirm']['title'],
            self.current_language['confirm']['delete'],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(backup)
                self.backups.remove(backup)
                QMessageBox.information(
                    self,
                    self.current_language['messages']['success'],
                    self.current_language['messages']['backup_deleted']
                )
                
                if not self.backups:  # 如果没有备份了，关闭对话框
                    self.close()
                else:
                    # 清除当前内容
                    scroll_area = self.findChild(QScrollArea)
                    if scroll_area:
                        old_widget = scroll_area.widget()
                        if old_widget:
                            old_widget.deleteLater()
                        
                        # 创建新的内容部件
                        content = QWidget()
                        content_layout = QVBoxLayout(content)
                        content_layout.setSpacing(10)
                        
                        # 重新添加剩余的备份
                        for backup in self.backups:
                            frame = QFrame()
                            frame.setStyleSheet("""
                                QFrame {
                                    background-color: #ffffff;
                                    border: 1px solid #dcdde1;
                                    border-radius: 5px;
                                }
                            """)
                            frame_layout = QVBoxLayout(frame)
                            frame_layout.setSpacing(10)
                            
                            # 备份信息
                            info_area = QTextEdit()
                            info_area.setReadOnly(True)
                            info_area.setFont(QFont('Menlo', 10))
                            info_area.setStyleSheet("""
                                QTextEdit {
                                    background-color: transparent;
                                    border: none;
                                    color: #2f3542;
                                }
                            """)
                            info_area.setText(self.modifier.get_backup_info(backup))
                            info_area.document().adjustSize()
                            doc_height = info_area.document().size().height()
                            info_area.setFixedHeight(min(doc_height + 20, 200))
                            
                            frame_layout.addWidget(info_area)
                            
                            # 按钮
                            btn_layout = QHBoxLayout()
                            btn_layout.setSpacing(10)
                            
                            restore_btn = QPushButton(self.current_language['dialog']['restore'])
                            restore_btn.setFixedWidth(150)
                            restore_btn.clicked.connect(lambda checked, b=backup: self.restore_backup(b))
                            btn_layout.addWidget(restore_btn)
                            
                            delete_btn = QPushButton(self.current_language['dialog']['delete'])
                            delete_btn.setFixedWidth(150)
                            delete_btn.clicked.connect(lambda checked, b=backup: self.delete_backup(b))
                            btn_layout.addWidget(delete_btn)
                            
                            btn_layout.addStretch()
                            frame_layout.addLayout(btn_layout)
                            content_layout.addWidget(frame)
                        
                        content_layout.addStretch()
                        scroll_area.setWidget(content)
                    
            except Exception as e:
                QMessageBox.warning(
                    self,
                    self.current_language['messages']['error'],
                    self.current_language['messages']['delete_failed'].format(e)
                )

class ConfigViewDialog(QDialog):
    """配置查看对话框"""
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.current_language = parent.current_language
        self.setup_ui()
    
    def setup_ui(self):
        """设置对话框界面"""
        self.setWindowTitle(self.current_language['dialog']['config_title'])
        self.setMinimumWidth(500)  # 只设置最小宽度
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 配置显示区域
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setFont(QFont('Menlo', 12))
        text_area.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #2f3542;
                border: 1px solid #dcdde1;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        # 格式化配置内容
        formatted_config = json.dumps(self.config, indent=2, ensure_ascii=False)
        text_area.setText(formatted_config)
        
        # 根据内容设置合适的大小
        text_area.document().adjustSize()
        doc_height = text_area.document().size().height()
        text_area.setMinimumHeight(min(int(doc_height + 40), 400))  # 使用 int() 转换
        
        layout.addWidget(text_area)
        
        # 关闭按钮
        close_btn = QPushButton(self.current_language['dialog']['close'])
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        # 调整对话框大小以适应内容
        self.adjustSize()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 在创建主窗口前检查权限
    if not is_admin():
        run_as_admin()
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 