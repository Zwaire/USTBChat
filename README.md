USTBChat 部署与使用说明

# 一、环境准备
1. Python 3.10 或 3.11（推荐 3.11）
2. MySQL 8.x
3. Ollama（用于智能助手 lulu）
4. 操作系统：Linux / macOS / Windows 均可（以下命令以 Linux 为例）

# 二、拉起项目前的目录与依赖
1. 进入项目目录
cd ./USTBChat

2. 安装 Python 依赖
pip install -r requirements.txt

说明：
- `requirements.txt` 已包含 `ollama` Python SDK。
- AI服务 `assistant_service.py` 会通过 Python `ollama` 库连接本地或远程 Ollama。

# 三、数据库部署（首次必须执行）

1. 启动 MySQL

```
sudo systemctl start mysql
sudo systemctl enable mysql
sudo systemctl status mysql
```

若你的系统不支持 systemctl：
```sudo service mysql start```

2. 登录 MySQL:
```mysql -u root -p```

3. 在 MySQL 中执行以下 SQL（整段复制执行）

```
DROP DATABASE IF EXISTS chat;
CREATE DATABASE chat DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE chat;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    code VARCHAR(255) NOT NULL,
    seed VARCHAR(255) NOT NULL
);

CREATE TABLE user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(255),
    ip INT UNSIGNED,
    login_time DATETIME,
    time DATETIME,
    status INT
);

CREATE TABLE friends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    friend_id INT NOT NULL
);

CREATE TABLE groups_list (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE groups_member (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    user_id INT NOT NULL
);

CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    send_id INT NOT NULL,
    recive_id INT NOT NULL,
    message TEXT,
    time DATETIME
);

CREATE TABLE group_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    send_id INT NOT NULL,
    message TEXT,
    time DATETIME
);

CREATE TABLE IF NOT EXISTS group_ai_members (
    group_id INT PRIMARY KEY,
    ai_name VARCHAR(64) NOT NULL DEFAULT 'lulu'
);
```
4. 退出 MySQL:
```exit```

# 四、AI（Ollama）部署

1. 安装并启动 Ollama

    ```curl -fsSL https://ollama.com/install.sh | sh```
- 请按你的系统安装 Ollama 官方程序（ubuntu也可使用：sudo snap install ollama）
- 默认端口应为 `11434`

2. 拉取至少一个可用模型（示例）

    ```ollama pull qwen2.5:1.5b```

3. （可选）设置 Ollama 连接变量
    ```
    export USTBCHAT_OLLAMA_HOST=127.0.0.1
    export USTBCHAT_OLLAMA_PORT=11434
    export USTBCHAT_OLLAMA_MODEL=qwen2.5:1.5b
    ```
4. 运行连通性测试

    ```python AI_assistant/mylocal/ollama_connect_test.py```

    如果 Ollama 在局域网另一台机器：
    
    ```python AI_assistant/mylocal/ollama_connect_test.py --host <Ollama机器IP> --port 11434```

# 五、服务启动顺序
终端A：启动聊天服务端（服务器）
```python server_main.py```

终端B：启动 AI 接口服务
```python AI_assistant/mylocal/assistant_service.py```

终端C：启动客户端（本机）
```python client_main.py```

终端D：可再启动第二个客户端（用于双人测试）
```python client_main.py```

六、局域网跨设备部署

假设服务端机器 IP 为 `192.168.1.20`：

1. 服务端机器上启动：
- MySQL
- `python server_main.py`
- `python AI_assistant/mylocal/assistant_service.py`

2. 其他设备只启动客户端：
`python client_main.py`

3. 客户端登录页把“服务器IP”改为：
`192.168.1.20`

4. 若 AI 服务也在独立机器上，服务端机器需设置后再启动：
`export USTBCHAT_AI_URL=http://<AI服务IP>:5001`

# 七、软件功能使用

1. 登录/注册
- 在登录页面输入账号密码
- 服务器IP默认 `127.0.0.1`，跨设备请改为服务端局域网IP

2. 添加好友
- 点击左侧“加好友”
- 输入好友 UID 或用户名并添加

3. 私聊
- 点击好友会话
- 在输入框输入消息，点击“发送”

4. 建群
- 点击“建群聊”
- 输入群名，勾选成员
- 需要机器人时勾选“添加智能助手 lulu”

5. 群聊中调用 lulu
- 发送 `@lulu 你的问题`
- 或发送 `@智能助手 你的问题`

6. 列表刷新
- 点击“刷新列表”按钮可手动刷新会话/好友/群聊

# 八、常见问题排查

1. 客户端连接失败
- 检查 `server_main.py` 是否在运行
- 检查客户端填写的服务器IP
- 检查 8888 端口防火墙

2. 登录/注册失败
- 检查 MySQL 是否运行
- 检查 `chat` 数据库和表是否初始化成功

3. lulu 不回复
- 检查群创建时是否勾选“添加智能助手 lulu”
- 检查 `assistant_service.py` 是否运行
- 检查消息是否以 `@lulu` 或 `@智能助手` 开头
- 先跑测试：
  `python AI_assistant/mylocal/ollama_connect_test.py`

4. 报错“AI服务请求失败 / Connection refused”
- 说明 AI 服务不可达或未启动
- 重启 AI 服务：
  `python AI_assistant/mylocal/assistant_service.py`
- 若 AI 在远程机器，设置并重启聊天服务端：
  ```
  export USTBCHAT_AI_URL=http://<AI服务IP>:5001
  python server_main.py
  ```

5. 报错“未安装 Python ollama 库”
- 执行：
  `pip install -r requirements.txt`
