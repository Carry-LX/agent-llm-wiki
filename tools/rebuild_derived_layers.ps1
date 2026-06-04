$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PythonExe = "python"

Set-Location $ProjectRoot

Write-Host "=== 重建派生层 ===" -ForegroundColor Cyan

# 1. 从 corpus 构建 claims
Write-Host "[1/3] 构建 claims..." -ForegroundColor Yellow
& $PythonExe ".\tools\build_claims_from_corpus.py"

# 2. 标签富化与交叉回填
Write-Host "[2/3] 标签富化..." -ForegroundColor Yellow
& $PythonExe ".\tools\enrich_asset_labels.py"

# 3. 健康检查
Write-Host "[3/4] 健康检查..." -ForegroundColor Yellow
& $PythonExe ".\tools\lint_agent_wiki.py"

# 4. 构建 wiki 浏览器内容
Write-Host "[4/4] 构建 wiki 浏览器内容..." -ForegroundColor Yellow
& $PythonExe ".\tools\build_wiki_content.py"

Write-Host ""
Write-Host "Derived layers rebuilt." -ForegroundColor Green
Write-Host "Claims: data\claims.jsonl"
Write-Host "Report: reports\wiki_health_report.md"
Write-Host "Wiki content: app\wiki_content.js"
