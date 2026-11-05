$ErrorActionPreference = 'Stop'

$basePath = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
$buildInfo = Get-ItemProperty -Path $basePath -ErrorAction Stop

$channel = 'Unknown'
$selfHostPath = 'HKLM:\SOFTWARE\Microsoft\WindowsSelfHost\Applicability'
if (Test-Path $selfHostPath) {
    $selfHostInfo = Get-ItemProperty -Path $selfHostPath -ErrorAction SilentlyContinue
    if ($null -ne $selfHostInfo -and $selfHostInfo.PSObject.Properties.Name -contains 'BranchName') {
        $channel = $selfHostInfo.BranchName
    }
}

$buildNumber = $buildInfo.CurrentBuild
$ubr = if ($null -ne $buildInfo.UBR) { [int]$buildInfo.UBR } else { 0 }
$displayVersion = if ($null -ne $buildInfo.DisplayVersion) { $buildInfo.DisplayVersion } else { 'Unknown' }
$productName = if ($null -ne $buildInfo.ProductName) { $buildInfo.ProductName } else { 'Windows' }
$releaseId = if ($null -ne $buildInfo.ReleaseId) { $buildInfo.ReleaseId } else { 'Unknown' }

$result = [pscustomobject]@{
    ProductName = $productName
    DisplayVersion = $displayVersion
    ReleaseId = $releaseId
    CurrentBuild = [int]$buildNumber
    UBR = $ubr
    FullBuild = "{0}.{1}" -f $buildNumber, $ubr
    Channel = $channel
    TimestampUtc = (Get-Date).ToUniversalTime().ToString('o')
}

$result | ConvertTo-Json -Compress
