@echo off
setlocal
set "CHROME_MENU_FILE=%~f0"
powershell.exe -NoProfile -Command "$s = [IO.File]::ReadAllText($env:CHROME_MENU_FILE); & ([scriptblock]::Create(($s -split '(?m)^# POWERSHELL_START\r?$', 2)[1]))"
if errorlevel 1 pause
exit /b

# POWERSHELL_START

$ErrorActionPreference = 'Stop'

$baseDir = Split-Path $env:CHROME_MENU_FILE
$listPath = Join-Path $baseDir 'danhsach.txt'
$configPath = Join-Path $baseDir 'chrome_profile.json'
$userData = Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data'
$statePath = Join-Path $userData 'Local State'

# Tim Chrome.
$chrome = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
) | Where-Object {
    Test-Path -LiteralPath $_
} | Select-Object -First 1

if (-not $chrome) {
    throw 'Khong tim thay Google Chrome.'
}

if (-not (Test-Path -LiteralPath $listPath)) {
    throw 'Khong tim thay danhsach.txt cung thu muc.'
}

function Read-Profiles {
    if (-not (Test-Path -LiteralPath $statePath)) {
        throw 'Chua tim thay du lieu Chrome. Hay mo Chrome it nhat mot lan.'
    }

    $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 |
        ConvertFrom-Json

    $cache = $state.profile.info_cache

    if (-not $cache) {
        throw 'Khong doc duoc danh sach ho so Chrome.'
    }

    foreach ($property in $cache.PSObject.Properties) {
        $directory = $property.Name

        # Chi chap nhan ten thu muc profile thong thuong.
        if ($directory -notmatch '^(Default|Profile \d+)$') {
            continue
        }

        $profilePath = Join-Path $userData $directory

        if (-not (Test-Path -LiteralPath $profilePath -PathType Container)) {
            continue
        }

        $displayName = [string]$property.Value.name
        $email = [string]$property.Value.user_name

        if ([string]::IsNullOrWhiteSpace($displayName)) {
            $displayName = $directory
        }

        [PSCustomObject]@{
            Directory = $directory
            Name      = $displayName
            Email     = $email
        }
    }
}

$script:profiles = @(Read-Profiles | Sort-Object Name, Directory)
$script:activeProfile = $null

if ($script:profiles.Count -eq 0) {
    throw 'Khong tim thay ho so Chrome.'
}

function Select-Profile {
    # Doc lai de cap nhat neu vua them ho so.
    $script:profiles = @(Read-Profiles | Sort-Object Name, Directory)

    if ($script:profiles.Count -eq 0) {
        throw 'Khong tim thay ho so Chrome.'
    }

    while ($true) {
        Clear-Host
        Write-Host '========== CHON HO SO CHROME ==========' -ForegroundColor Cyan
        Write-Host ''

        for ($i = 0; $i -lt $script:profiles.Count; $i++) {
            $profile = $script:profiles[$i]

            Write-Host ('[{0}] {1}' -f ($i + 1), $profile.Name)
            Write-Host ('    Thu muc: {0}' -f $profile.Directory)

            if (-not [string]::IsNullOrWhiteSpace($profile.Email)) {
                Write-Host ('    Email  : {0}' -f $profile.Email)
            }

            Write-Host ''
        }

        $answer = Read-Host 'Nhap so ho so muon su dung'
        $number = 0

        if (
            [int]::TryParse($answer.Trim(), [ref]$number) -and
            $number -ge 1 -and
            $number -le $script:profiles.Count
        ) {
            $script:activeProfile = $script:profiles[$number - 1]

            try {
                @{
                    Directory = $script:activeProfile.Directory
                } |
                    ConvertTo-Json |
                    Set-Content -LiteralPath $configPath -Encoding UTF8
            }
            catch {
                Write-Host 'Khong luu duoc lua chon cho lan sau.' -ForegroundColor Yellow
                [void](Read-Host 'Nhan Enter de tiep tuc')
            }

            return
        }

        Write-Host 'Lua chon khong hop le.' -ForegroundColor Yellow
        [void](Read-Host 'Nhan Enter de chon lai')
    }
}

# Khoi phuc ho so da chon lan truoc.
if (Test-Path -LiteralPath $configPath) {
    try {
        $saved = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 |
            ConvertFrom-Json

        $script:activeProfile = $script:profiles |
            Where-Object { $_.Directory -eq $saved.Directory } |
            Select-Object -First 1
    }
    catch {
        $script:activeProfile = $null
    }
}

if (-not $script:activeProfile) {
    Select-Profile
}

# Doc danh sach ten,url khong co dong tieu de.
$items = @(
    Get-Content -LiteralPath $listPath -Encoding UTF8 |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        ConvertFrom-Csv -Header Name, Url
)

if ($items.Count -eq 0) {
    throw 'Danh sach URL dang trong.'
}

function Show-List {
    Write-Host '========== HO SO DANG SU DUNG ==========' -ForegroundColor Cyan
    Write-Host ('Ten    : {0}' -f $script:activeProfile.Name)
    Write-Host ('Thu muc: {0}' -f $script:activeProfile.Directory)

    if (-not [string]::IsNullOrWhiteSpace($script:activeProfile.Email)) {
        Write-Host ('Email  : {0}' -f $script:activeProfile.Email)
    }

    Write-Host ''
    Write-Host '========== DANH SACH URL ==========' -ForegroundColor Cyan

    for ($i = 0; $i -lt $items.Count; $i++) {
        Write-Host ('[{0}] {1}' -f ($i + 1), $items[$i].Name)
        Write-Host ('    {0}' -f $items[$i].Url)
    }

    Write-Host ''
}

function Test-WebUrl([string]$Value) {
    $parsed = $null

    return (
        [Uri]::TryCreate($Value, [UriKind]::Absolute, [ref]$parsed) -and
        $parsed.Scheme -in @('http', 'https') -and
        -not [string]::IsNullOrWhiteSpace($parsed.Host) -and
        $Value -notmatch '[\s"]'
    )
}

function Open-Item($Item) {
    $url = ([string]$Item.Url).Trim()

    if (-not (Test-WebUrl $url)) {
        Write-Host (
            'Bo qua URL khong hop le: {0}' -f $Item.Name
        ) -ForegroundColor Yellow
        return
    }

    $arguments = '--user-data-dir="{0}" --profile-directory="{1}" "{2}"' -f (
        $userData,
        $script:activeProfile.Directory,
        $url
    )

    try {
        Start-Process -FilePath $chrome -ArgumentList $arguments

        Write-Host (
            'Da yeu cau mo: {0} | Ho so: {1}' -f
            $Item.Name, $script:activeProfile.Name
        ) -ForegroundColor Green

        Start-Sleep -Milliseconds 300
    }
    catch {
        Write-Host (
            'Khong mo duoc {0}: {1}' -f
            $Item.Name, $_.Exception.Message
        ) -ForegroundColor Red
    }
}

function Save-List {
    $temporaryPath = $listPath + '.tmp'

    try {
        $items |
            Select-Object Name, Url |
            ConvertTo-Csv -NoTypeInformation |
            Select-Object -Skip 1 |
            Set-Content -LiteralPath $temporaryPath -Encoding UTF8

        # Thay file va giu ban truoc do trong danhsach.txt.bak.
        [IO.File]::Replace(
            $temporaryPath,
            $listPath,
            ($listPath + '.bak')
        )
    }
    finally {
        if (Test-Path -LiteralPath $temporaryPath) {
            Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
        }
    }
}

while ($true) {
    Clear-Host
    Show-List

    Write-Host '1. Mo ALL bang ho so dang chon'
    Write-Host '2. Chon ten de mo URL'
    Write-Host '3. Thay doi URL theo ten'
    Write-Host '4. Doi ho so Chrome'
    Write-Host '0. Thoat'
    Write-Host ''

    $choice = Read-Host 'Chon chuc nang'

    if ($choice -eq '0') {
        break
    }

    switch ($choice) {
        '1' {
            foreach ($item in $items) {
                Open-Item $item
            }
        }

        '2' {
            $inputText = Read-Host 'Nhap so cua ten can mo (vi du: 1,3,5)'
            $selected = @()
            $valid = $true

            foreach ($part in ($inputText -split ',')) {
                $number = 0

                if (
                    -not [int]::TryParse($part.Trim(), [ref]$number) -or
                    $number -lt 1 -or
                    $number -gt $items.Count
                ) {
                    $valid = $false
                    break
                }

                $selected += $number
            }

            if (-not $valid) {
                Write-Host 'Hay nhap so hop le trong danh sach.' -ForegroundColor Yellow
            }
            else {
                foreach ($number in ($selected | Select-Object -Unique)) {
                    Open-Item $items[$number - 1]
                }
            }
        }

        '3' {
            $inputText = Read-Host 'Nhap so cua ten can thay doi URL'
            $number = 0

            if (
                -not [int]::TryParse($inputText.Trim(), [ref]$number) -or
                $number -lt 1 -or
                $number -gt $items.Count
            ) {
                Write-Host 'So khong hop le.' -ForegroundColor Yellow
            }
            else {
                $item = $items[$number - 1]

                Write-Host ('Ten    : {0}' -f $item.Name)
                Write-Host ('URL cu : {0}' -f $item.Url)

                $newUrl = (Read-Host 'URL moi (Enter de huy)').Trim()

                if ($newUrl -eq '') {
                    Write-Host 'Da huy.'
                }
                elseif (-not (Test-WebUrl $newUrl)) {
                    Write-Host 'URL phai hop le, bat dau bang http:// hoac https://' -ForegroundColor Yellow
                }
                else {
                    $oldUrl = $item.Url
                    $item.Url = $newUrl

                    try {
                        Save-List
                        Write-Host 'Da luu URL moi.' -ForegroundColor Green
                    }
                    catch {
                        $item.Url = $oldUrl

                        Write-Host (
                            'Luu that bai: {0}' -f $_.Exception.Message
                        ) -ForegroundColor Red
                    }
                }
            }
        }

        '4' {
            Select-Profile
        }

        default {
            Write-Host 'Hay chon 0, 1, 2, 3 hoac 4.' -ForegroundColor Yellow
        }
    }

    Write-Host ''
    [void](Read-Host 'Nhan Enter de quay lai menu')
}