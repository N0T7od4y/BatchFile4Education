@echo off
setlocal DisableDelayedExpansion
set "GH_FOLDER_SCRIPT=%~f0"
powershell.exe -NoLogo -NoProfile -Command "$s=[IO.File]::ReadAllText($env:GH_FOLDER_SCRIPT); & ([scriptblock]::Create(($s -split '(?m)^# POWERSHELL_START\r?\n',2)[1]))"
set "GH_FOLDER_EXIT=%errorlevel%"
echo.
pause
exit /b %GH_FOLDER_EXIT%
# POWERSHELL_START
$ErrorActionPreference = 'Stop'
$tempDir = $null
$exitCode = 1
try {
    Write-Host '=== TAI THU MUC GITHUB V2 - KHONG CHECKOUT ===' -ForegroundColor Cyan
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) {
        throw 'Chua co Git. Cai Git for Windows: https://git-scm.com/downloads/win'
    }
    $url = (Read-Host 'Dan link thu muc GitHub').Trim().Trim('"')
    $uri = [Uri]$url
    if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'github.com' -or $uri.UserInfo) {
        throw 'Chi nhan link https://github.com/OWNER/REPO/tree/BRANCH/FOLDER'
    }
    $parts = $uri.AbsolutePath.Trim('/').Split('/')
    if ($parts.Count -lt 5 -or $parts[2] -ne 'tree') {
        throw 'Hay mo thu muc tren GitHub va sao chep link co /tree/.'
    }
    $owner = $parts[0]
    $repo = $parts[1]
    if ($owner -notmatch '^[A-Za-z0-9-]+$' -or $repo -notmatch '^[A-Za-z0-9_.-]+$') {
        throw 'Ten owner/repo khong hop le.'
    }
    $tail = [Uri]::UnescapeDataString(($parts[3..($parts.Count-1)] -join '/'))
    $defaultBranch = [Uri]::UnescapeDataString($parts[3])
    Write-Host 'Neu ten branch co dau /, nhap day du, vi du feature/demo.'
    $branch = (Read-Host "Branch/tag [Enter = $defaultBranch]").Trim()
    if (-not $branch) { $branch = $defaultBranch }
    if ($branch.StartsWith('-') -or -not $tail.StartsWith($branch + '/', [StringComparison]::Ordinal)) {
        throw 'Branch/tag khong khop link. Kiem tra lai ten branch/tag tren GitHub.'
    }
    $folder = $tail.Substring($branch.Length + 1).TrimEnd('/')
    $segments = $folder.Split('/')
    foreach ($segment in $segments) {
        if (-not $segment -or $segment -eq '.' -or $segment -eq '..' -or
            $segment -match '[<>:"\\|?*\x00-\x1f]' -or $segment -match '[. ]$' -or
            $segment -match '^(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)') {
            throw 'Duong dan thu muc khong hop le tren Windows.'
        }
    }
    $defaultDest = Join-Path $env:USERPROFILE 'Downloads'
    $dest = (Read-Host "Thu muc luu [Enter = $defaultDest]").Trim().Trim('"')
    if (-not $dest) { $dest = $defaultDest }
    $dest = [IO.Path]::GetFullPath($dest)
    [IO.Directory]::CreateDirectory($dest) | Out-Null
    $id = [Guid]::NewGuid().ToString('N')
    $output = Join-Path $dest ($segments[-1] + '_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + $id.Substring(0,6))
    $tempDir = Join-Path ([IO.Path]::GetTempPath()) ('github_folder_' + $id)
    $clone = Join-Path $tempDir 'repo'
    [IO.Directory]::CreateDirectory($tempDir) | Out-Null
    Write-Host "Dang tai: $owner/$repo -> $folder" -ForegroundColor Cyan
    # Disable hooks; do not run any scripts from the downloaded repository.
    $hooks = Join-Path $tempDir 'empty-hooks'
    [IO.Directory]::CreateDirectory($hooks) | Out-Null
    & git.exe -c core.longpaths=true -c "core.hooksPath=$hooks" clone --depth 1 --filter=blob:none --no-checkout --single-branch --branch $branch -- "https://github.com/$owner/$repo.git" $clone
    if ($LASTEXITCODE -ne 0) { throw 'Git clone that bai. Kiem tra link, branch, mang hoac quyen truy cap.' }
    # Archive the selected subtree directly; no full-repository index/checkout.
    $tree = 'HEAD:' + $folder
    $kind = & git.exe -C $clone cat-file -t $tree
    if ($LASTEXITCODE -ne 0 -or $kind -ne 'tree') {
        throw 'Khong tim thay thu muc. Kiem tra branch va duong dan.'
    }
    # Preserve tracked files even when repository export attributes say otherwise.
    $attributes = Join-Path $clone '.git/info/attributes'
    [IO.File]::WriteAllText($attributes, "* -export-ignore -export-subst`n", [Text.Encoding]::ASCII)
    $archive = $output + '.tar'
    Write-Host 'Dang xuat rieng thu muc da chon; co the mat thoi gian voi dataset lon...'
    & git.exe -C $clone archive --format=tar --output=$archive $tree
    if ($LASTEXITCODE -ne 0) {
        throw "Xuat archive that bai. File TAR neu co la ban chua hoan tat: $archive"
    }
    if (-not (Get-Command tar.exe -ErrorAction SilentlyContinue)) {
        throw "Da tai xong TAR: $archive . May chua co tar.exe; dung 7-Zip de giai nen."
    }
    [IO.Directory]::CreateDirectory($output) | Out-Null
    & tar.exe -xf $archive -C $output
    if ($LASTEXITCODE -ne 0) {
        throw "Giai nen chua hoan tat. Giu ban TAR day du tai: $archive . Xem loi tar o tren."
    }
    Remove-Item -LiteralPath $archive -Force
    Write-Host "`nHOAN TAT: $output" -ForegroundColor Green
    $exitCode = 0
} catch {
    Write-Host ("`nLOI: " + $_.Exception.Message) -ForegroundColor Red
} finally {
    if ($tempDir -and (Test-Path -LiteralPath $tempDir)) {
        try { Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction Stop }
        catch { Write-Warning "Khong don duoc thu muc tam: $tempDir" }
    }
}
exit $exitCode
