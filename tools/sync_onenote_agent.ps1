# OneNote 同步脚本：从 OneNote 笔记本导出页面、图片和文本链接
#
# 用法: & .\tools\sync_onenote_agent.ps1
#
# 输出:
#   raw/onenote_pages.jsonl     - 页面列表与元信息
#   raw/assets.jsonl            - 图片/文本链接资产列表
#   raw/page_xml/*.xml          - 页面 XML 导出
#   raw/images/*.png            - 提取的图片
#   raw/last_sync_manifest.json - 同步清单
#
# 依赖: 本机需安装 OneNote 桌面版 (通过 COM 对象调用)

$ErrorActionPreference = "Stop"

# ====== 配置变量 ======
$NotebookName = "我的笔记本"
$SectionName = "Agent"
$OutputRoot = $PSScriptRoot | Split-Path -Parent
$RawDir = Join-Path $OutputRoot "raw"
$ImagesDir = Join-Path $RawDir "images"
$XmlDir = Join-Path $RawDir "page_xml"
$OcrCacheDir = Join-Path $RawDir "ocr_cache"

# ====== 初始化目录 ======
foreach ($dir in @($RawDir, $ImagesDir, $XmlDir, $OcrCacheDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# ====== 辅助函数 ======
function Get-ImageHash {
    param([string]$ImagePath)
    if (-not (Test-Path $ImagePath)) { return "" }
    $bytes = [System.IO.File]::ReadAllBytes($ImagePath)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $hash = $sha256.ComputeHash($bytes)
    return [BitConverter]::ToString($hash).Replace("-", "").ToLower()
}

function New-AssetId {
    param([string]$SectionPrefix, [int]$PageIndex, [int]$AssetIndex, [string]$HashSuffix)
    $hashShort = $HashSuffix.Substring(0, [Math]::Min(12, $HashSuffix.Length))
    return "agent_img_${SectionPrefix}_${AssetIndex}_${hashShort}"
}

# ====== 主同步流程 ======
Write-Host "=== OneNote 同步 ===" -ForegroundColor Cyan
Write-Host "笔记本: $NotebookName / $SectionName" -ForegroundColor Cyan

# 生成同步运行 ID
$SyncRunId = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")

# 连接 OneNote COM
try {
    $OneNote = New-Object -ComObject OneNote.Application
    Write-Host "已连接 OneNote COM" -ForegroundColor Green
} catch {
    Write-Error "无法连接 OneNote COM，请确认已安装 OneNote 桌面版。错误: $_"
    exit 1
}

# 获取 XML 层次结构
try {
    $hierarchyXml = $OneNote.GetHierarchy("", [Microsoft.Office.Interop.OneNote.HierarchyScope]::hsPages)
} catch {
    Write-Error "无法获取 OneNote 层次结构。错误: $_"
    exit 1
}

# 查找目标分区
$xmlDoc = [xml]$hierarchyXml
$ns = @{one = "http://schemas.microsoft.com/office/onenote/2013/onenote"}

$targetSection = $xmlDoc.SelectSingleNode(
    "//one:Section[contains(@name,'$SectionName')]//ancestor::one:Notebook[contains(@name,'$NotebookName')]",
    $ns
)
if (-not $targetSection) {
    # 尝试反向查找
    $targetSection = $xmlDoc.SelectSingleNode(
        "//one:Notebook[contains(@name,'$NotebookName')]//one:Section[contains(@name,'$SectionName')]",
        $ns
    )
}
if (-not $targetSection) {
    Write-Error "找不到分区: $NotebookName / $SectionName"
    exit 1
}

$sectionId = $targetSection.ID
Write-Host "找到分区 ID: $sectionId" -ForegroundColor Green

# 获取分区下的页面
$pagesXml = $OneNote.GetHierarchy($sectionId, [Microsoft.Office.Interop.OneNote.HierarchyScope]::hsPages)
$pagesDoc = [xml]$pagesXml
$pageNodes = $pagesDoc.SelectNodes("//one:Page", $ns)

if (-not $pageNodes -or $pageNodes.Count -eq 0) {
    Write-Warning "分区下没有页面。"
    exit 0
}

Write-Host "找到 $($pageNodes.Count) 个页面" -ForegroundColor Green

# ====== 遍历页面 ======
$allPages = @()
$allAssets = @()
$totalImages = 0
$totalTextLinks = 0

for ($pageIdx = 0; $pageIdx -lt $pageNodes.Count; $pageIdx++) {
    $pageNode = $pageNodes[$pageIdx]
    $pageId = $pageNode.ID
    $pageName = $pageNode.name
    $pageModified = if ($pageNode.lastModifiedTime) { $pageNode.lastModifiedTime } else { "" }

    Write-Host "`n[$($pageIdx + 1)/$($pageNodes.Count)] $pageName" -ForegroundColor Yellow

    # 导出页面 XML
    $safeName = $pageName -replace '[\\/:*?"<>|]', '_'
    $xmlFileName = "{0:D3}_{1}.xml" -f ($pageIdx + 1), $safeName
    $xmlPath = Join-Path $XmlDir $xmlFileName

    try {
        $OneNote.GetPageContent($pageId, $xmlPath, [Microsoft.Office.Interop.OneNote.PageInfo]::piAll)
        Write-Host "  XML -> $xmlFileName"
    } catch {
        Write-Warning "  导出 XML 失败: $_"
        continue
    }

    # 解析 XML 提取图片和链接
    $pageXml = [xml](Get-Content $xmlPath -Encoding UTF8)
    $pageNs = @{one = "http://schemas.microsoft.com/office/onenote/2013/onenote"}

    $sectionPrefix = "{0:D3}" -f ($pageIdx + 1)
    $imageCount = 0
    $linkCount = 0

    # 提取图片
    $imageNodes = $pageXml.SelectNodes("//one:Image", $pageNs)
    if ($imageNodes) {
        foreach ($imgNode in $imageNodes) {
            $imageCount++
            $dataNode = $imgNode.SelectSingleNode("one:Data", $pageNs)
            $callbackId = $imgNode.callbackID
            if (-not $dataNode) { continue }

            try {
                $imgBytes = [Convert]::FromBase64String($dataNode.InnerText)
            } catch {
                Write-Warning "  Base64 解码失败: $_"
                continue
            }

            $imgHash = [BitConverter]::ToString(
                [System.Security.Cryptography.SHA256]::Create().ComputeHash($imgBytes)
            ).Replace("-", "").ToLower()

            $hashShort = $imgHash.Substring(0, 12)
            $assetId = "agent_img_${sectionPrefix}_{0:D3}_${hashShort}" -f $imageCount
            $imgFileName = "${assetId}.png"
            $imgPath = Join-Path $ImagesDir $imgFileName

            # 检查是否已存在
            if (-not (Test-Path $imgPath)) {
                [System.IO.File]::WriteAllBytes($imgPath, $imgBytes)
            }

            # 提取 source_url (如果有)
            $sourceUrl = ""
            $metaNodes = $imgNode.SelectNodes("one:Meta[contains(@name,'source')]", $pageNs)
            if (-not $metaNodes -or $metaNodes.Count -eq 0) {
                $metaNodes = $imgNode.SelectNodes("one:Meta", $pageNs)
            }
            if ($metaNodes) {
                foreach ($meta in $metaNodes) {
                    $content = $meta.content
                    if ($content -match '^https?://') {
                        $sourceUrl = $content
                        break
                    }
                }
            }

            $asset = @{
                schema_version = 1
                asset_id = $assetId
                asset_type = "onenote_image"
                sync_run_id = $SyncRunId
                notebook = $NotebookName
                section = $SectionName
                page_title = $pageName
                page_index = $pageIdx + 1
                page_id = $pageId
                page_modified_time = $pageModified
                image_index = $imageCount
                onenote_object_id = $callbackId
                object_created_time = ""
                object_modified_time = ""
                source_url = $sourceUrl
                image_path = "raw/images/$imgFileName"
                image_sha256 = $imgHash
                image_bytes = $imgBytes.Length
                width = $imgNode.width
                height = $imgNode.height
                ocr_text = ""
                ocr_text_sha256 = ""
            }
            $allAssets += $asset
            $totalImages++
        }
    }

    # 提取文本链接 (从 Title 和 Outline 中的链接)
    $linkNodes = $pageXml.SelectNodes("//one:OE//one:Meta[contains(@name,'hyperlink')]", $pageNs)
    if ($linkNodes) {
        foreach ($linkNode in $linkNodes) {
            $linkCount++
            $linkUrl = $linkNode.content
            if (-not $linkUrl -or $linkUrl -notmatch '^https?://') { continue }

            $textParent = $linkNode.ParentNode
            $linkText = if ($textParent) { $textParent.InnerText } else { $linkUrl }

            $linkId = "agent_link_${sectionPrefix}_{0:D3}" -f $linkCount
            $linkHash = [BitConverter]::ToString(
                [System.Security.Cryptography.SHA256]::Create().ComputeHash(
                    [System.Text.Encoding]::UTF8.GetBytes($linkUrl)
                )
            ).Replace("-", "").ToLower()
            $linkAssetId = "${linkId}_${($linkHash.Substring(0, 12))}"

            $linkAsset = @{
                schema_version = 1
                asset_id = $linkAssetId
                asset_type = "onenote_text_link"
                sync_run_id = $SyncRunId
                notebook = $NotebookName
                section = $SectionName
                page_title = $pageName
                page_index = $pageIdx + 1
                page_id = $pageId
                page_modified_time = $pageModified
                image_index = $linkCount
                onenote_object_id = ""
                object_created_time = ""
                object_modified_time = ""
                source_url = $linkUrl
                image_path = ""
                image_sha256 = ""
                image_bytes = 0
                width = ""
                height = ""
                ocr_text = $linkText
                ocr_text_sha256 = ""
            }
            $allAssets += $linkAsset
            $totalTextLinks++
        }
    }

    # 页面记录
    $pageRecord = @{
        page_index = $pageIdx + 1
        page_id = $pageId
        page_title = $pageName
        section = $SectionName
        notebook = $NotebookName
        page_modified_time = $pageModified
        image_count = $imageCount
        text_link_count = $linkCount
        xml_path = "raw/page_xml/$xmlFileName"
    }
    $allPages += $pageRecord
    Write-Host "  图片: $imageCount, 文本链接: $linkCount"
}

# ====== 写入输出文件 ======
Write-Host "`n=== 写入输出文件 ===" -ForegroundColor Cyan

# onenote_pages.jsonl
$pagesPath = Join-Path $RawDir "onenote_pages.jsonl"
$allPages | ForEach-Object {
    $_ | ConvertTo-Json -Compress -Depth 10
} | Out-File -FilePath $pagesPath -Encoding utf8
Write-Host "页面: $pagesPath ($($allPages.Count) 页)"

# assets.jsonl
$assetsPath = Join-Path $RawDir "assets.jsonl"
$allAssets | ForEach-Object {
    $_ | ConvertTo-Json -Compress -Depth 10
} | Out-File -FilePath $assetsPath -Encoding utf8
Write-Host "资产: $assetsPath ($($allAssets.Count) 条)"

# 同步清单
$manifest = @{
    schema_version = 1
    sync_run_id = $SyncRunId
    notebook = $NotebookName
    section = $SectionName
    output_root = (Resolve-Path $OutputRoot).Path
    pages = $allPages.Count
    assets = $allAssets.Count
    images = $totalImages
    text_links = $totalTextLinks
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
}
$manifestPath = Join-Path $RawDir "last_sync_manifest.json"
$manifest | ConvertTo-Json -Depth 5 | Out-File -FilePath $manifestPath -Encoding utf8
Write-Host "清单: $manifestPath"

Write-Host "`n=== 同步完成 ===" -ForegroundColor Green
Write-Host "页面: $($allPages.Count), 图片: $totalImages, 文本链接: $totalTextLinks"
