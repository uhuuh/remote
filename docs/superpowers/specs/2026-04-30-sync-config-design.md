# SyncConfig 重构设计

## 背景

将 `SyncConfig` 从单一 `enabled` 布尔值拆分为两个独立配置，实现更灵活的控制。

## 变更

### SyncConfig 新结构

```python
@dataclass
class SyncConfig:
    sync: bool = False  # 是否同步变更到远程后端
    commit: bool = False  # 是否为本地和远程创建自动 commit
```

### 行为矩阵

| sync | commit | 行为 |
|------|--------|------|
| false | false | 不同步任何内容（no-op） |
| true | false | 仅同步变更到远程，不创建 commit |
| true | true | 同步变更到远程，并在本地和远程都创建 commit |
| false | true | 无效组合，抛出配置错误 |

### 实现变更

#### 1. SyncManager.sync() 调整

```python
def sync(self, current_file: str) -> None:
    if not self.config.sync and not self.config.commit:
        return

    if self.config.commit and not self.config.sync:
        raise SyncError("commit=True requires sync=True")

    remote_path = self.backend._config.remote_path
    if not remote_path:
        raise SyncError("sync or commit requires remote_path")

    patch = self._generate_patch(current_file)
    if not patch.strip():
        return

    if self.config.sync:
        self._apply_patch(patch, remote_path)

    if self.config.commit:
        self._create_local_commit()
        self._create_remote_commit(remote_path)
```

#### 2. 调用方更新

```python
# 旧
sync=SyncConfig(enabled=True)

# 新
sync=SyncConfig(sync=True, commit=True)  # 完整同步
sync=SyncConfig(sync=True, commit=False)  # 仅同步无 commit
```

## 测试场景

1. `sync=True, commit=True` - 同步 + 两侧 commit
2. `sync=True, commit=False` - 仅同步到远程
3. `sync=False, commit=False` - no-op
4. `sync=False, commit=True` - 抛出配置错误

## 兼容性

旧代码 `enabled=True` 需迁移为 `sync=True, commit=True`