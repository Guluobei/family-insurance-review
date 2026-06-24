# Claude Code 适配说明

## 安装

将本目录复制到 `~/.claude/skills/family-insurance-review/`

## 调用

在 Claude Code 中输入：
```
/skill family-insurance-review
```

或通过自然语言触发：
- "保单检视"
- "家庭保险"
- "policy review"

## 特殊说明

Claude Code 支持通过 `Bash` 工具直接执行 Python 脚本。

```bash
cd ~/.claude/skills/family-insurance-review
python insurance_review.py
```
