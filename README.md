# iTab 书签迁移工具

[![Python 版本](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![许可证: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

将 iTab 新标签页的书签和图标迁移到 Chrome 浏览器，并生成精美的深色科技风导航页面。

## 功能特性

- 解析 iTab 备份文件 (`.itabdata`)
- 异步并发下载网站图标（支持进度条）
- 生成 Chrome 兼容的书签文件 (HTML 和 JSON)
- **生成精美书签导航页面**
  - 深色科技风设计（Linear / Raycast 风格）
  - 全局搜索框（支持 `Ctrl+K` 快捷键）
  - 轻量卡片式书签入口
  - 分组展示，清晰层级
  - 响应式布局，适配桌面和移动端
- 书签去重功能
- 书签 URL 验证（检测失效链接）
- 多格式导出（Chrome、Firefox、Edge、Markdown、CSV、JSON、OPML）
- 图标缓存系统（SQLite）
- 配置文件支持

## 安装

```bash
git clone https://github.com/Tatajiang/itab-migration.git
cd itab-migration
pip install -r requirements.txt
```

## 快速开始

### 命令行使用

```bash
# 基础用法
python -m itab_migration backup.itabdata

# 指定输出目录
python -m itab_migration backup.itabdata -o ./my_bookmarks

# 跳过图标下载
python -m itab_migration backup.itabdata --no-icons

# 显示详细日志
python -m itab_migration backup.itabdata -v
```

### 异步下载

默认使用异步下载器，支持并发下载图标：

```bash
# 默认异步下载（10 并发）
python -m itab_migration backup.itabdata

# 自定义并发数
python -m itab_migration backup.itabdata --concurrency 20

# 使用同步下载器（兼容模式）
python -m itab_migration backup.itabdata --sync
```

### 书签验证

检测失效链接和重定向：

```bash
# 验证书签 URL
python -m itab_migration backup.itabdata --validate

# 仅验证，不迁移
python -m itab_migration backup.itabdata --validate-only

# 自动移除失效书签
python -m itab_migration backup.itabdata --validate --remove-invalid
```

### 多格式导出

```bash
# 查看支持的格式
python -m itab_migration --list-formats

# 导出为 Firefox 书签
python -m itab_migration backup.itabdata --export firefox

# 导出为 Markdown
python -m itab_migration backup.itabdata --export markdown

# 导出为 CSV
python -m itab_migration backup.itabdata --export csv
```

### 使用配置文件

创建 `config.json` 配置文件：

```json
{
  "input_file": "backup.itabdata",
  "output_dir": "./output",
  "download_icons": true,
  "use_async": true,
  "concurrency": 10,
  "download_timeout": 10,
  "generate_html": true,
  "generate_json": true,
  "generate_mapping": true,
  "show_progress": true
}
```

然后使用配置文件运行：

```bash
python -m itab_migration -c config.json
```

### Python API

```python
from itab_migration import migrate

# 简单迁移
result = migrate("backup.itabdata", "./output")

print(f"迁移了 {result.bookmarks_count} 个书签")
print(f"下载了 {result.icons_downloaded} 个图标")
```

## 输出文件

迁移完成后会生成以下文件：

| 文件 | 说明 |
|------|------|
| `index.html` | 精美书签导航页面（深色科技风） |
| `chrome_bookmarks.html` | HTML 格式书签文件（可导入 Chrome） |
| `chrome_bookmarks.json` | Chrome 原生 JSON 格式 |
| `icon_mapping.json` | 图标与书签的映射关系 |
| `icons/` | 下载的图标文件目录 |

## 书签导航页面

生成的 `index.html` 具有以下特点：

- **深色科技风**：采用 `#0A0E17` 深蓝黑背景，克制的蓝紫点缀
- **全局搜索**：支持实时搜索，`Ctrl+K` 快捷键聚焦
- **轻量卡片**：统一的图标容器 + 下方名称显示
- **首字母回退**：无图标的书签显示首字母标识
- **分组展示**：清晰的分类标题和数量统计
- **响应式设计**：适配各种屏幕尺寸

直接在浏览器中打开 `index.html` 即可使用。

## 导入到 Chrome

### 方法一：导入 HTML 文件（推荐）

1. 打开 Chrome 浏览器
2. 点击 `书签` → `导入书签和设置`
3. 选择 `书签 HTML 文件`
4. 选择 `chrome_bookmarks.html`

### 方法二：直接替换书签文件（高级）

1. 完全关闭 Chrome
2. 备份原始书签文件：
   ```
   C:\Users\<用户名>\AppData\Local\Google\Chrome\User Data\Default\Bookmarks
   ```
3. 将 `chrome_bookmarks.json` 复制到上述位置
4. 重命名为 `Bookmarks`
5. 重新打开 Chrome

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `input` | iTab 备份文件路径 | 必填 |
| `-o, --output` | 输出目录 | `./output` |
| `-c, --config` | 配置文件路径 | 无 |
| `--no-icons` | 跳过图标下载 | `false` |
| `--no-html` | 跳过 HTML 生成 | `false` |
| `--no-json` | 跳过 JSON 生成 | `false` |
| `--no-mapping` | 跳过映射文件生成 | `false` |
| `--timeout` | HTTP 请求超时（秒） | `10` |
| `--delay` | 请求间隔（秒） | `0.1` |
| `--sync` | 使用同步下载器 | `false` |
| `--concurrency` | 最大并发下载数 | `10` |
| `--validate` | 验证书签 URL | `false` |
| `--validate-only` | 仅验证，不迁移 | `false` |
| `--remove-invalid` | 移除失效书签 | `false` |
| `--export` | 导出格式 | 无 |
| `--list-formats` | 列出支持的导出格式 | `false` |
| `--clear-cache` | 清除图标缓存 | `false` |
| `--cache-stats` | 显示缓存统计 | `false` |
| `-v, --verbose` | 显示详细日志 | `false` |

## 项目结构

```
itab-migration/
├── itab_migration/          # 核心代码
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py               # 命令行接口
│   ├── parser.py            # 备份文件解析器
│   ├── downloader.py        # 同步图标下载器
│   ├── async_downloader.py  # 异步图标下载器
│   ├── bookmark_generator.py # 书签/导航页生成器
│   ├── migrator.py          # 主迁移器
│   ├── config.py            # 配置文件支持
│   ├── deduplicator.py      # 书签去重
│   ├── validator.py         # 书签 URL 验证
│   ├── cache.py             # 图标缓存系统
│   └── exporters.py         # 多格式导出
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── pyproject.toml
└── requirements.txt
```

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)。
