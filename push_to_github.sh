#!/bin/bash
# push_to_github.sh - 推送脚本（在项目根目录执行）
# 前置条件：已在 GitHub 手动创建公开仓库 Guluobei/family-insurance-review

set -e
cd "$(dirname "$0")"

echo "=== 1. 添加远程仓库 ==="
git remote add origin https://github.com/Guluobei/family-insurance-review.git
git remote -v

echo ""
echo "=== 2. 推送到 main 分支 ==="
git push -u origin main

echo ""
echo "=== 3. 验证 ==="
git log --oneline -5
echo ""
echo "🎉 推送完成！"
echo "访问 https://github.com/Guluobei/family-insurance-review 查看"
