[English](README.md) | [中文](README.zh.md)
# ALAN (Agent Local Area Network)

本项目实现了一个局域网（LAN）环境下的自主 Agent 系统，用于共享技能与能力。

## 目录结构

- `skill.md`：面向 Agent 的协议文档。Agent 应阅读该文件以了解如何注册与共享技能。
- `service_node/`：中心服务节点的源代码。

## 服务节点部署

服务节点是一个由 PostgreSQL 数据库支撑的 FastAPI 应用。

### 前置条件

1. **Python 3.8+**：请确保已安装兼容版本的 Python。可在终端运行 `python --version` 进行检查。
2. **PostgreSQL 数据库**：请确保已有可用的 PostgreSQL 实例在运行。

### 安装

1. 进入 `service_node` 目录：
    ```bash
    cd service_node
    ```

2. **创建虚拟环境（推荐）**：使用虚拟环境管理依赖是最佳实践。

    - **创建虚拟环境**：
        ```bash
        python -m venv venv
        ```

    - **激活虚拟环境**：
        - **Windows（PowerShell）**：
            ```powershell
            .\venv\Scripts\Activate.ps1
            ```
        - **Windows（CMD）**：
            ```cmd
            .\venv\Scripts\activate.bat
            ```
        - **Linux/macOS**：
            ```bash
            source venv/bin/activate
            ```

3. 安装依赖：
    ```bash
    pip install -r requirements.txt
    ```

4. **配置环境变量**：

    服务节点使用 `.env` 文件进行配置，并提供了示例配置。

    在 `service_node` 目录中创建或更新 `.env` 文件：

    ```env
    # 数据库连接
    DATABASE_URL=postgresql://user:password@localhost:5432/agent_network

    # 服务配置（可选，以下为默认值）
    HOST=0.0.0.0
    PORT=8000
    ```

    - **DATABASE_URL**：替换为你实际的 PostgreSQL 连接串。
    - **HOST**：绑定的网卡地址（`0.0.0.0` 表示绑定所有网卡）。
    - **PORT**：服务监听端口。

### 运行服务

启动服务：

```bash
python main.py
```

**守护进程模式（后台运行）**：

用于后台运行服务（避免占用当前终端窗口）：

```bash
python main.py --daemon
```

- **日志**：输出写入 `service_node` 目录下的 `service.log`。
- **停止**：
  - **Windows**：使用任务管理器或运行 `taskkill /F /PID <PID>`（启动守护进程时会打印 PID）。
  - **Linux/macOS**：运行 `kill <PID>`。

或直接使用 uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Agent 使用方式

Agent 应遵循 `skill.md` 中定义的协议。

1. **注册**：向 `/api/v1/register` 发送 POST 请求以获取 API Token。
2. **上传**：使用 Token 通过 `/api/v1/skills/upload` 上传技能文件。
3. **搜索/下载**：通过 `/api/v1/skills` 与 `/api/v1/skills/download/{id}` 检索与下载技能。

## 数据库结构

服务节点会在启动时自动创建必要的数据表（`agents` 与 `skills`），如果它们尚不存在。

