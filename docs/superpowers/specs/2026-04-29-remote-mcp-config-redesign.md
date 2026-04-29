# Remote MCP 配置重构设计

## 背景

当前 `init_session` 会将配置保存到本地 `mcp-bridge-config.yaml`，下次使用时自动加载。需要改为：每次连接都需要传参，不保存本地配置。

## 变更内容

### 1. 移除配置保存

- `init_session` 不再调用 `_config_store.save()`
- 移除 `__init__.py` 中的 `_config_store` 实例

### 2. 错误分类

| 错误类型 | 触发场景 | 返回信息 |
|----------|----------|----------|
| NoSessionError | 未初始化就执行命令 | "错误: 请先调用 init_session 初始化会话" |
| ConnectionError | 网络不通、认证失败、容器不存在 | "连接失败: {具体原因}" |
| ConfigError | 必要参数缺失、参数无效 | "配置错误: {具体原因}" |
| 其他内部错误 | 意外异常 | "内部错误: {错误信息}" |

### 3. 文件变更

**remote_mcp/__init__.py**
- 删除 `ConfigStore` 导入和 `_config_store` 实例
- 删除 `init_session` 中的 `_config_store.save(config)`
- 保留 `execute_command` 的异常处理

**remote_mcp/config.py**
- 删除文件

### 4. 行为

- 用户每次调用 `init_session` 需传入完整参数
- 连接失败返回统一格式错误信息
- 命令执行失败直接返回实际输出（stdout/stderr）