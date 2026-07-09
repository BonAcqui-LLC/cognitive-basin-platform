param(
    [string]$OutputPath = ".\receipts\device_audit.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-Adb {
    $fromPath = Get-Command adb.exe -ErrorAction SilentlyContinue
    if ($fromPath) {
        return $fromPath.Source
    }

    $candidates = @(
        "C:\Users\moop\AppData\Local\Android\Sdk\platform-tools\adb.exe",
        "C:\Android\platform-tools\adb.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    throw "adb.exe was not found in PATH or common local locations."
}

function Invoke-AdbText {
    param(
        [string]$AdbPath,
        [string[]]$Arguments
    )

    $result = & $AdbPath @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "adb command failed: $($Arguments -join ' ')`n$result"
    }
    return ($result | Out-String).Trim()
}

function Get-PropValue {
    param(
        [hashtable]$Props,
        [string]$Key
    )

    if ($Props.ContainsKey($Key)) {
        return $Props[$Key]
    }

    return $null
}

$adb = Find-Adb
$deviceList = Invoke-AdbText -AdbPath $adb -Arguments @("devices", "-l")
$deviceLines = @($deviceList -split "`r?`n" | Where-Object { $_ -match "\sdevice\b" })

if ($deviceLines.Count -eq 0) {
    throw "No connected adb device was detected."
}

if ($deviceLines.Count -gt 1) {
    throw "More than one adb device was detected. Connect exactly one handset for a trustworthy audit."
}

$propsText = Invoke-AdbText -AdbPath $adb -Arguments @("shell", "getprop")
$props = @{}
foreach ($line in ($propsText -split "`r?`n")) {
    if ($line -match "^\[(.+?)\]: \[(.*)\]$") {
        $props[$matches[1]] = $matches[2]
    }
}

$wmSize = Invoke-AdbText -AdbPath $adb -Arguments @("shell", "wm", "size")
$dfData = Invoke-AdbText -AdbPath $adb -Arguments @("shell", "df", "/data")
$meminfo = Invoke-AdbText -AdbPath $adb -Arguments @("shell", "cat", "/proc/meminfo")
$cpuinfo = Invoke-AdbText -AdbPath $adb -Arguments @("shell", "cat", "/proc/cpuinfo")
$slotInfo = Invoke-AdbText -AdbPath $adb -Arguments @("shell", "getprop", "ro.boot.slot_suffix")

$receipt = [ordered]@{
    recorded_at = (Get-Date).ToString("s")
    adb_path = $adb
    device_line = $deviceLines[0]
    observed_properties = [ordered]@{
        product_device = Get-PropValue -Props $props -Key "ro.product.device"
        product_name = Get-PropValue -Props $props -Key "ro.product.name"
        product_model = Get-PropValue -Props $props -Key "ro.product.model"
        build_fingerprint = Get-PropValue -Props $props -Key "ro.build.fingerprint"
        build_id = Get-PropValue -Props $props -Key "ro.build.id"
        build_version_release = Get-PropValue -Props $props -Key "ro.build.version.release"
        build_version_sdk = Get-PropValue -Props $props -Key "ro.build.version.sdk"
        manufacturer = Get-PropValue -Props $props -Key "ro.product.manufacturer"
        brand = Get-PropValue -Props $props -Key "ro.product.brand"
        hardware = Get-PropValue -Props $props -Key "ro.hardware"
        board = Get-PropValue -Props $props -Key "ro.product.board"
        bootloader = Get-PropValue -Props $props -Key "ro.bootloader"
        flash_locked = Get-PropValue -Props $props -Key "ro.boot.flash.locked"
        verifiedboot_state = Get-PropValue -Props $props -Key "ro.boot.verifiedbootstate"
        vbmeta_state = Get-PropValue -Props $props -Key "ro.boot.vbmeta.device_state"
        oem_unlock_supported = Get-PropValue -Props $props -Key "ro.oem_unlock_supported"
        carrier = Get-PropValue -Props $props -Key "ro.carrier"
        operator_alpha = Get-PropValue -Props $props -Key "gsm.operator.alpha"
        operator_numeric = Get-PropValue -Props $props -Key "gsm.operator.numeric"
        serial = Get-PropValue -Props $props -Key "ro.serialno"
        ab_slot_suffix = $slotInfo
        abi = Get-PropValue -Props $props -Key "ro.product.cpu.abi"
    }
    raw_observations = [ordered]@{
        wm_size = $wmSize
        df_data = $dfData
        meminfo = $meminfo
        cpuinfo = $cpuinfo
    }
    safety_statement = "Read-only audit only. This script does not unlock, flash, root, or modify the handset."
}

$targetPath = if ([System.IO.Path]::IsPathRooted($OutputPath)) {
    $OutputPath
} else {
    Join-Path -Path (Get-Location).Path -ChildPath $OutputPath
}
$targetDir = Split-Path -Parent $targetPath
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $targetPath -Encoding UTF8

Write-Host "Wrote device audit receipt to $targetPath"
