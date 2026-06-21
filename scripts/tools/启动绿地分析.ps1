# =========================================
# 海淀小学绿地覆盖分析 - PowerShell 启动脚本
# =========================================

# =============================================
# 在这里填入你的 DASHSCOPE_API_KEY
# =============================================
$env:DASHSCOPE_API_KEY = "sk-在这里填入你的APIKey"

if ($env:DASHSCOPE_API_KEY -eq "sk-在这里填入你的APIKey") {
    Write-Host "[错误] 请先编辑本文件，将 API Key 替换为真实值！" -ForegroundColor Red
    Write-Host "文件位置: $PSCommandPath"
    Read-Host "按 Enter 退出"
    exit 1
}

Write-Host "API Key: $($env:DASHSCOPE_API_KEY.Substring(0,8))..." -ForegroundColor Green
Write-Host ""

$scriptPath = "分析小学绿地覆盖.py"

# =============================================
# 运行模式（取消注释对应行）
# =============================================

# 测试模式 - 只分析前 3 张
# python $scriptPath --test 3

# 全量分析（156张，约30-60分钟）
python $scriptPath

# 强制重新分析所有（忽略已有结果）
# python $scriptPath --no-skip

Write-Host ""
Write-Host "结果文件: 绿地分析结果.json" -ForegroundColor Cyan
Read-Host "按 Enter 退出"
