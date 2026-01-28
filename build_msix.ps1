# 콘솔 출력 인코딩을 UTF-8로 설정
# Set console output encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 현재 스크립트 위치를 기준으로 작업 디렉토리 설정
# Set working directory to script location
$ScriptDir = $PSScriptRoot
Set-Location $ScriptDir

# .env 파일 확인
# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file is missing!" -ForegroundColor Red
    Write-Host "Please create .env file with VERSION and PUBLISHER_ID." -ForegroundColor Yellow
    exit 1
}

# .env 로드 및 실행 파일 이름 설정
# Load .env and set executable name
$envVars = @{}
$lines = Get-Content ".env" -Encoding UTF8
foreach ($line in $lines) {
    if ($line -match '^\s*([^#=]+)\s*=\s*(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        if ($value -match '^"(.*)"$') { $value = $matches[1] }
        $envVars[$key] = $value
    }
}

$version = if ($envVars["VERSION"]) { $envVars["VERSION"] } else { "1.0.0" }
$exeName = "GodModTimer_v${version}.exe"
Write-Host "Target Executable: $exeName" -ForegroundColor Cyan

# 1. 최신 의존성 설치
# 1. Install latest dependencies
Write-Host "[1/4] Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# 2. 실행 파일 빌드 (PyInstaller & Manifest 생성)
# 2. Build executable (PyInstaller & Manifest generation)
Write-Host "`n[2/4] Building executable..." -ForegroundColor Yellow
python build.py

# 3. 빌드된 파일을 패키징 폴더로 복사
# 3. Copy built file to packaging folder
Write-Host "`n[3/4] Copying executable..." -ForegroundColor Yellow
if (-not (Test-Path "store_package")) {
    New-Item -ItemType Directory -Force -Path "store_package"
}

if (Test-Path "dist\$exeName") {
    Copy-Item "dist\$exeName" -Destination "store_package\$exeName" -Force
} else {
    Write-Host "ERROR: Build artifact 'dist\$exeName' not found!" -ForegroundColor Red
    exit 1
}

# 3.1 AppxManifest.xml 검증 및 복구
# 3.1 Validate and Restore AppxManifest.xml
$manifestPath = Join-Path $ScriptDir "store_package\AppxManifest.xml"
$envPath = Join-Path $ScriptDir ".env"

# 기본 매니페스트 템플릿 (Default Manifest Template)
$defaultManifest = @"
<?xml version="1.0" encoding="utf-8"?>
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
  <Identity
    Name="jinsseof.God-modTimer"
    Version="1.0.0.0"
    Publisher="CN=YOUR-PUBLISHER-ID"
    ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>God-Mode Timer</DisplayName>
    <PublisherDisplayName>jinsseof</PublisherDisplayName>
    <Logo>Assets\StoreLogo.png</Logo>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.19041.0" />
  </Dependencies>
  <Resources>
    <Resource Language="ko-kr" />
  </Resources>
  <Applications>
    <Application Id="App" Executable="GodModTimer.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements
        DisplayName="God-Mode Timer"
        Description="God-Mode Timer"
        BackgroundColor="transparent"
        Square150x150Logo="Assets\Square150x150Logo.png"
        Square44x44Logo="Assets\Square44x44Logo.png">
      </uap:VisualElements>
    </Application>
  </Applications>
  <Capabilities>
    <Capability Name="internetClient" />
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
</Package>
"@

# 파일 손상 여부 확인 및 재생성
$needRegen = $false
if (-not (Test-Path $manifestPath)) {
    $needRegen = $true
} else {
    try {
        $xmlContent = Get-Content $manifestPath -Raw -Encoding UTF8
        if ($xmlContent -match 'Category="windows.fullTrustProcess"') {
            Write-Host "WARNING: AppxManifest.xml contains invalid extension. Regenerating..." -ForegroundColor Yellow
            $needRegen = $true
        }
        if ($xmlContent -match 'Language="x-generate"') {
            Write-Host "WARNING: AppxManifest.xml contains invalid resource language 'x-generate'. Regenerating..." -ForegroundColor Yellow
            $needRegen = $true
        }
        [xml]$check = $xmlContent
    } catch {
        Write-Host "WARNING: AppxManifest.xml is corrupted or invalid. Regenerating..." -ForegroundColor Yellow
        $needRegen = $true
    }
}

if ($needRegen) {
    Set-Content -Path $manifestPath -Value $defaultManifest -Encoding UTF8
}

# .env 파일 기반 업데이트
if ($envVars.Count -gt 0) {
    [xml]$xml = Get-Content $manifestPath -Encoding UTF8
    
    # Version fix for MSIX (Quad format)
    if ($envVars["VERSION"]) { 
        $verParts = $envVars["VERSION"].Split('.')
        $msixVer = $envVars["VERSION"]
        if ($verParts.Count -eq 2) { $msixVer = "$($envVars["VERSION"]).0.0" }
        elseif ($verParts.Count -eq 3) { $msixVer = "$($envVars["VERSION"]).0" }
        $xml.Package.Identity.Version = $msixVer 
    }

    if ($envVars["PUBLISHER_ID"]) { $xml.Package.Identity.Publisher = $envVars["PUBLISHER_ID"] }
    if ($envVars["PACKAGE_NAME"]) { $xml.Package.Identity.Name = $envVars["PACKAGE_NAME"] }
    if ($envVars["DISPLAY_NAME"]) { 
        $xml.Package.Properties.DisplayName = $envVars["DISPLAY_NAME"] 
        if ($xml.Package.Applications.Application.VisualElements) {
            $xml.Package.Applications.Application.VisualElements.DisplayName = $envVars["DISPLAY_NAME"]
        }
    }
    if ($envVars["PUBLISHER_DISPLAY_NAME"]) { $xml.Package.Properties.PublisherDisplayName = $envVars["PUBLISHER_DISPLAY_NAME"] }
    
    # Update Executable
    if ($xml.Package.Applications.Application) {
        $xml.Package.Applications.Application.Executable = $exeName
    }
    
    $xml.Save($manifestPath)
    Write-Host "Updated AppxManifest from .env" -ForegroundColor Cyan
}

# 4. MSIX 패키징 (MakeAppx 자동 검색 및 실행)
# 4. MSIX Packaging (Auto-detect MakeAppx and run)
$makeappx = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin" -Recurse -Filter "MakeAppx.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName -First 1

if ($makeappx) {
    Write-Host "`n[4/4] Running MakeAppx..." -ForegroundColor Green
    
    $sourceDir = Join-Path $ScriptDir "store_package"
    $outputFile = Join-Path $ScriptDir "GodModTimer.msix"
    
    & $makeappx pack /d "$sourceDir" /p "$outputFile" /o
    
    if ($?) { 
        Write-Host "`nSUCCESS: Packaging successful! File created at:" -ForegroundColor Cyan 
        Write-Host "   $outputFile" -ForegroundColor Cyan
    }
} else {
    Write-Host "`nERROR: MakeAppx.exe not found. Please check Windows SDK installation." -ForegroundColor Red
}

# 5. 패키지 서명 (로컬 테스트용)
# 5. Sign Package (For local testing)
Write-Host "`n[5/5] Signing package for local testing..." -ForegroundColor Yellow

# Find signtool (Prefer x64, then x86)
$signtools = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin" -Recurse -Filter "signtool.exe" -ErrorAction SilentlyContinue
$signtool = $signtools | Where-Object { $_.FullName -like "*\x64\*" } | Select-Object -ExpandProperty FullName -First 1
if (-not $signtool) {
    $signtool = $signtools | Where-Object { $_.FullName -like "*\x86\*" } | Select-Object -ExpandProperty FullName -First 1
}
if (-not $signtool) {
    $signtool = $signtools | Select-Object -ExpandProperty FullName -First 1
}

if (-not $signtool) {
    Write-Host "WARNING: SignTool.exe not found. Skipping signing." -ForegroundColor Yellow
    Write-Host "You won't be able to install the MSIX locally without signing." -ForegroundColor Yellow
} else {
    $pfxPath = Join-Path $ScriptDir "GodModTimer_Dev.pfx"
    $publisher = $envVars["PUBLISHER_ID"]
    if (-not $publisher) { $publisher = "CN=YOUR-PUBLISHER-ID" }

    # 인증서가 없으면 생성 (Create certificate if missing)
    if (-not (Test-Path $pfxPath)) {
        Write-Host "Creating self-signed certificate for: $publisher" -ForegroundColor Cyan
        $cert = New-SelfSignedCertificate -Type Custom -Subject $publisher -KeyUsage DigitalSignature -FriendlyName "GodModTimer Dev Cert" -CertStoreLocation "Cert:\CurrentUser\My" -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
        $password = ConvertTo-SecureString -String "password" -Force -AsPlainText
        Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $password
        Write-Host "Certificate created: $pfxPath" -ForegroundColor Green
    }

    # 서명 실행 (Sign the package)
    Write-Host "Signing MSIX package..." -ForegroundColor Cyan
    & $signtool sign /fd sha256 /a /f $pfxPath /p "password" "$outputFile"
    
    if ($?) {
        Write-Host "SUCCESS: Package signed successfully!" -ForegroundColor Green
        Write-Host "`n[Installation Guide]" -ForegroundColor White
        Write-Host "1. Double-click 'GodModTimer.msix'" -ForegroundColor White
        Write-Host "2. If 'Untrusted App' error appears:" -ForegroundColor White
        Write-Host "   Properties -> Digital Signatures -> Details -> View Certificate" -ForegroundColor White
        Write-Host "   -> Install Certificate -> Local Machine -> 'Trusted People' (Trusted People)" -ForegroundColor White
    } else {
        Write-Host "ERROR: Signing failed." -ForegroundColor Red
    }
}

# 종료 전 대기
Read-Host -Prompt "Press Enter to exit"