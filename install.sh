#!/bin/bash
# install.sh - 一键安装到 5 大 AI 编程助手
# 用法：./install.sh [trae|claude|opencode|codex|cursor|all]

set -e
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAME="family-insurance-review"

install_trae() {
    TARGET="$HOME/.trae/skills/$SKILL_NAME"
    echo "📦 安装到 TRAE: $TARGET"
    mkdir -p "$TARGET"
    cp -r "$SKILL_DIR"/* "$TARGET/"
    echo "✅ TRAE 安装完成"
}

install_claude() {
    TARGET="$HOME/.claude/skills/$SKILL_NAME"
    echo "📦 安装到 Claude Code: $TARGET"
    mkdir -p "$TARGET"
    cp -r "$SKILL_DIR"/* "$TARGET/"
    echo "✅ Claude Code 安装完成"
}

install_opencode() {
    TARGET="$HOME/.opencode/skills/$SKILL_NAME"
    mkdir -p "$TARGET"
    cp -r "$SKILL_DIR"/* "$TARGET/"
    CONFIG="$HOME/.opencode/config.toml"
    if ! grep -q "$SKILL_NAME" "$CONFIG" 2>/dev/null; then
        mkdir -p "$(dirname "$CONFIG")"
        touch "$CONFIG"
        echo -e "\n[[skills]]\nname = \"$SKILL_NAME\"\npath = \"$TARGET\"" >> "$CONFIG"
    fi
    echo "✅ OpenCode 安装完成"
}

install_codex() {
    TARGET="$HOME/.codex/skills/$SKILL_NAME"
    mkdir -p "$TARGET"
    cp -r "$SKILL_DIR"/* "$TARGET/"
    echo "✅ Codex 安装完成"
}

install_cursor() {
    TARGET=".cursor/skills/$SKILL_NAME"
    echo "📦 安装到 Cursor (项目级): $TARGET"
    mkdir -p "$TARGET"
    cp -r "$SKILL_DIR"/* "$TARGET/"
    echo "✅ Cursor 安装完成"
}

case "${1:-all}" in
    trae) install_trae ;;
    claude|claude-code) install_claude ;;
    opencode) install_opencode ;;
    codex) install_codex ;;
    cursor) install_cursor ;;
    all)
        install_trae
        install_claude
        install_opencode
        install_codex
        install_cursor
        ;;
    *) echo "用法: $0 [trae|claude|opencode|codex|cursor|all]"; exit 1 ;;
esac

echo ""
echo "🎉 安装完成！"
echo "下一步："
echo "  1. 准备 policies.json 和 family.json"
echo "  2. 运行: python insurance_review.py"
echo "  3. 查看生成的 report.html"
