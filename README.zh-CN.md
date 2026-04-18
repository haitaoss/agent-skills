# agent-skills

面向终端 AI agent 的个人 skill 仓库。

English version: [README.md](README.md)

## 仓库定位

这个仓库用于存放可复用的 AI agent skill、脚本和工作流封装。

当前仓库内容主要是 Codex skill 格式，但仓库名刻意保持中性，不限定在某一个模型或某一个宿主工具上。长期目标是：

- 可复用的逻辑尽量保留
- 宿主工具相关的元数据和触发规则按 agent 分开管理

## 当前范围

目前仓库里只有 Codex 格式的 skill：

```text
agent-skills/
  codex/
    skills/
      commit-api-doc/
      lrc-mp3-lyrics/
```

当前已收录：

- `commit-api-doc`：根据提交和代码变更生成紧凑的中文接口文档
- `lrc-mp3-lyrics`：偏移 `.lrc`、按需裁剪 MP3 开头、清理旧 `awlrc`、同步内嵌歌词

## 目录约定

建议长期使用这样的顶层结构：

```text
agent-skills/
  codex/
    skills/
      <skill-name>/
  claude/
    skills/
      <skill-name>/
  shared/
    scripts/
    docs/
```

当前规则：

- `codex/skills/` 放 Codex 可直接识别的 skill
- 每个 skill 独立一个目录
- 宿主工具特有的元数据跟着对应 skill 走
- 以后如果多个 agent 共用同一套脚本或资料，再抽到 `shared/`

## 如何在 Codex 中使用这些 Skill

把仓库里的 skill 目录复制到本机 Codex 的 skill 目录即可。

常见目标路径：

- `$CODEX_HOME/skills/<skill-name>`
- 如果 `CODEX_HOME` 没设置，一般就是 `~/.codex/skills/<skill-name>`

例如仓库里有：

```text
agent-skills/
  codex/
    skills/
      lrc-mp3-lyrics/
```

那就把 `lrc-mp3-lyrics/` 复制到：

```text
~/.codex/skills/lrc-mp3-lyrics/
```

复制或更新后，重启 Codex，让它重新加载 skill 列表。

## Skill 更新方式

当仓库内容更新后：

1. 拉取仓库最新内容
2. 把更新后的 skill 目录重新复制到本机 Codex skill 目录，或者直接原地同步
3. 重启 Codex

## 如何往仓库里新增 Codex Skill

新的 Codex skill 统一放在：

```text
codex/skills/<skill-name>/
```

最少应包含：

```text
<skill-name>/
  SKILL.md
  agents/
    openai.yaml
```

按需增加：

```text
scripts/
references/
assets/
```

仓库层面的约定：

- skill 目录尽量自包含
- 只有当多个 skill 明确共用时，再把脚本抽成共享资源
- 双语说明只在确实有帮助时再加，不为了“看起来完整”而堆文档
- 不要默认别的 agent 工具能直接识别 Codex 的 metadata 格式

## 跨 Agent 兼容性

skill 里的这些内容通常是可迁移的：

- 脚本
- 参考资料
- 工作流逻辑
- 领域经验规则

但下面这些通常不能直接通用：

- 触发元数据
- 安装路径
- 宿主工具专属 UI 元数据
- skill 加载约定

所以这个仓库名字保持中性，但目录结构按宿主工具拆分。

## 说明

- 当前仓库优先面向 Codex
- 现在仓库还没有单独的 `LICENSE` 文件，公开仓库默认不等于已经授予开源许可证
- 如果以后支持别的 agent 格式，应该与 `codex/` 并列，而不是混在里面
