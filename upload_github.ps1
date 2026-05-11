# GitHub 上传脚本 - 使用 PowerShell 直接调用 GitHub API

$headers = @{
    "Authorization" = "token YOUR_GITHUB_TOKEN_HERE"
    "Accept" = "application/vnd.github.v3+json"
    "Content-Type" = "application/json"
}

$repoOwner = "JamesFeiPF"
$repoName = "660mw-heat-balance"
$branch = "main"
$baseUrl = "https://api.github.com/repos/$repoOwner/$repoName/contents"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "GitHub 文件上传工具" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. 验证 Token
Write-Host "`n[1/4] 验证 GitHub Token..." -ForegroundColor Yellow
$userResponse = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers -Method Get
if ($userResponse) {
    Write-Host "✓ Token 验证成功！用户: $($userResponse.login)" -ForegroundColor Green
} else {
    Write-Host "✗ Token 验证失败" -ForegroundColor Red
    exit 1
}

# 2. 检查仓库
Write-Host "`n[2/4] 检查目标仓库..." -ForegroundColor Yellow
$repoResponse = Invoke-RestMethod -Uri "https://api.github.com/repos/$repoOwner/$repoName" -Headers $headers -Method Get -ErrorAction SilentlyContinue
if ($repoResponse) {
    Write-Host "✓ 仓库已存在: https://github.com/$repoOwner/$repoName" -ForegroundColor Green
} else {
    Write-Host "✗ 仓库不存在: https://github.com/$repoOwner/$repoName" -ForegroundColor Red
    exit 1
}

# 3. 上传文件函数
function Upload-FileToGitHub {
    param(
        [string]$FilePath,
        [string]$RepoPath
    )

    try {
        $content = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($FilePath))

        # 获取文件 SHA（如果存在）
        $sha = $null
        try {
            $existingFile = Invoke-RestMethod -Uri "$baseUrl/$RepoPath" -Headers $headers -Method Get
            $sha = $existingFile.sha
        } catch {
            # 文件不存在，这是正常的
        }

        # 构建请求体
        $body = @{
            message = "Add $RepoPath"
            content = $content
            branch = $branch
        }
        if ($sha) {
            $body.sha = $sha
        }

        $jsonBody = $body | ConvertTo-Json -Depth 10
        $response = Invoke-RestMethod -Uri "$baseUrl/$RepoPath" -Headers $headers -Method Put -Body $jsonBody

        return $true
    } catch {
        Write-Host "  ✗ 上传失败 $RepoPath : $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 4. 上传文件
Write-Host "`n[3/4] 上传项目文件..." -ForegroundColor Yellow

$projectRoot = "e:\kimicode\660MWHF"
$successCount = 0
$failCount = 0

# 定义要排除的目录和文件
$excludePatterns = @("__pycache__", ".git", "node_modules", ".venv", "venv", ".env", ".gitignore")

# 上传文件函数 - 递归
function Upload-Directory {
    param(
        [string]$LocalDir,
        [string]$RepoPath = ""
    )

    $items = Get-ChildItem -Path $LocalDir -File -ErrorAction SilentlyContinue
    foreach ($item in $items) {
        $repoFilePath = if ($RepoPath) { "$RepoPath/$($item.Name)" } else { $item.Name }

        Write-Host "  上传: $repoFilePath" -NoNewline
        if (Upload-FileToGitHub -FilePath $item.FullName -RepoPath $repoFilePath) {
            Write-Host " ✓" -ForegroundColor Green
            $script:successCount++
        } else {
            Write-Host " ✗" -ForegroundColor Red
            $script:failCount++
        }
    }

    # 递归处理子目录
    $subdirs = Get-ChildItem -Path $LocalDir -Directory -ErrorAction SilentlyContinue
    foreach ($subdir in $subdirs) {
        if ($excludePatterns -notcontains $subdir.Name) {
            $newRepoPath = if ($RepoPath) { "$RepoPath/$($subdir.Name)" } else { $subdir.Name }
            Write-Host "`n  进入目录: $($subdir.Name)/" -ForegroundColor Cyan
            Upload-Directory -LocalDir $subdir.FullName -RepoPath $newRepoPath
        }
    }
}

# 上传根目录文件
Write-Host "`n  上传根目录文件..." -ForegroundColor Cyan
$rootFiles = Get-ChildItem -Path $projectRoot -File -ErrorAction SilentlyContinue
foreach ($file in $rootFiles) {
    if ($file.Name -notin $excludePatterns -and $file.Name -ne "upload_to_github.ps1" -and $file.Name -ne "run_upload.ps1" -and $file.Name -ne "run_upload.bat" -and $file.Name -ne "run_upload2.ps1" -and $file.Name -ne "run_python.py" -and $file.Name -ne "direct_run.ps1") {
        Write-Host "  上传: $($file.Name)" -NoNewline
        if (Upload-FileToGitHub -FilePath $file.FullName -RepoPath $file.Name) {
            Write-Host " ✓" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host " ✗" -ForegroundColor Red
            $failCount++
        }
    }
}

# 上传后端代码
Write-Host "`n  上传后端代码 (mhflow_backend/)..." -ForegroundColor Cyan
$backendPath = Join-Path $projectRoot "mhflow_backend"
if (Test-Path $backendPath) {
    Upload-Directory -LocalDir $backendPath -RepoPath "mhflow_backend"
}

# 上传前端代码
Write-Host "`n  上传前端代码 (mhflow_frontend/)..." -ForegroundColor Cyan
$frontendPath = Join-Path $projectRoot "mhflow_frontend"
if (Test-Path $frontendPath) {
    Upload-Directory -LocalDir $frontendPath -RepoPath "mhflow_frontend"
}

# 5. 验证结果
Write-Host "`n[4/4] 上传完成！" -ForegroundColor Yellow
Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "总计: 成功 $successCount 个文件, 失败 $failCount 个文件" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })
Write-Host "仓库地址: https://github.com/$repoOwner/$repoName" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
