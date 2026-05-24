# LLM-WIKI 完整重建脚本
# 从 OneNote 同步 → OCR 富化 → 构建 wiki → 健康检查
#
# 用法: & .\tools\rebuild_agent_wiki.ps1
# 也可以分步运行:
#   & .\tools\sync_onenote_agent.ps1
#   python .\tools\enrich_agent_ocr.py
#   python .\tools\build_agent_wiki.py
#   python .\tools\lint_agent_wiki.py

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot | Split-Path -Parent

Write-Host "=== LLM-WIKI 完整重建 ===" -ForegroundColor Cyan
Write-Host "项目根目录: $ProjectRoot" -ForegroundColor Cyan

# Step 1: OneNote 同步
Write-Host "`n[1/4] OneNote 同步..." -ForegroundColor Yellow
$syncScript = Join-Path $ProjectRoot "tools\sync_onenote_agent.ps1"
if (Test-Path $syncScript) {
    & $syncScript
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "OneNote 同步返回非零退出码 $LASTEXITCODE，继续后续步骤。"
    }
} else {
    Write-Warning "sync_onenote_agent.ps1 不存在，跳过同步步骤。"
}

# Step 2: OCR 富化
Write-Host "`n[2/4] OCR 富化..." -ForegroundColor Yellow
$enrichScript = Join-Path $ProjectRoot "tools\enrich_agent_ocr.py"
if (Test-Path $enrichScript) {
    python $enrichScript
    if ($LASTEXITCODE -ne 0) {
        Write-Error "OCR 富化失败，退出。"
        exit 1
    }
} else {
    Write-Warning "enrich_agent_ocr.py 不存在，跳过 OCR 富化。"
}

# Step 3: 构建 wiki
Write-Host "`n[3/4] 构建 wiki 派生层..." -ForegroundColor Yellow
$buildScript = Join-Path $ProjectRoot "tools\build_agent_wiki.py"
if (Test-Path $buildScript) {
    python $buildScript
    if ($LASTEXITCODE -ne 0) {
        Write-Error "构建 wiki 失败，退出。"
        exit 1
    }
} else {
    Write-Warning "build_agent_wiki.py 不存在，尝试用 build_claims_from_corpus.py 重建 claims。"
    $claimsScript = Join-Path $ProjectRoot "tools\build_claims_from_corpus.py"
    if (Test-Path $claimsScript) {
        python $claimsScript
    }
}

# Step 4: 标签富化与交叉回填
Write-Host "`n[3.5/4] 标签富化与交叉回填..." -ForegroundColor Yellow
$enrichLabelsScript = Join-Path $ProjectRoot "tools\enrich_asset_labels.py"
if (Test-Path $enrichLabelsScript) {
    python $enrichLabelsScript
}

# Step 5: 健康检查
Write-Host "`n[4/4] 健康检查..." -ForegroundColor Yellow
$lintScript = Join-Path $ProjectRoot "tools\lint_agent_wiki.py"
if (Test-Path $lintScript) {
    python $lintScript
    Write-Host "`n健康报告已写入 reports/wiki_health_report.md" -ForegroundColor Green
}

Write-Host "`n=== 重建完成 ===" -ForegroundColor Cyan
