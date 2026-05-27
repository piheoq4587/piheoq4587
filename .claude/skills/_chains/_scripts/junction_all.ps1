# junction_all.ps1 — Create junctions from canonical to all 3 target CLI dirs
$canon = "$env:USERPROFILE\.gemini\skills"
$cliDirs = @(
    "$env:USERPROFILE\.claude\skills",
    "$env:USERPROFILE\.codex\skills",
    "$env:USERPROFILE\.copilot\skills"
)

$canonItems = Get-ChildItem $canon -Force | Where-Object { $_.Name -notmatch '^_' } | Where-Object { $_.PSIsContainer }
Write-Output "Canonical skill dirs: $($canonItems.Count)"

$totalLinked = 0
$totalExisted = 0
$totalFailed = 0

foreach ($cli in $cliDirs) {
    if (-not (Test-Path $cli)) {
        New-Item -ItemType Directory -Path $cli -Force | Out-Null
    }
    Write-Output ""
    Write-Output "=== $cli ==="
    $linked = 0
    $existed = 0
    $failed = 0
    foreach ($s in $canonItems) {
        $linkPath = Join-Path $cli $s.Name
        if (Test-Path $linkPath) {
            $existed++
            continue
        }
        $output = cmd /c mklink /J "`"$linkPath`"" "`"$($s.FullName)`"" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $linked++
        } else {
            $failed++
        }
    }
    Write-Output "  Newly linked:    $linked"
    Write-Output "  Already existed: $existed"
    Write-Output "  Failed:          $failed"
    $totalLinked += $linked
    $totalExisted += $existed
    $totalFailed += $failed
}

Write-Output ""
Write-Output "=== TOTAL ==="
Write-Output "New junctions: $totalLinked"
Write-Output "Already had:   $totalExisted"
Write-Output "Failed:        $totalFailed"
