# _boot_check.ps1 — Logon-time skill chain health check + auto-repair
# 注册为 Windows 登录任务 (schtasks /sc onlogon)
# 跑约 5-15 秒,日志写入 _chains/_boot_log.txt

$ErrorActionPreference = 'Continue'
$canon = "$env:USERPROFILE\.gemini\skills"
$chainDir = "$canon\_chains"
$logFile = "$chainDir\_boot_log.txt"
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

function Log($msg) {
    "$ts $msg" | Out-File -FilePath $logFile -Append -Encoding UTF8
}

Log "===== boot check start ====="

# 1) Junction integrity — count canonical vs each CLI; auto-repair missing
$canonSkills = Get-ChildItem $canon -Force -Directory | Where-Object { $_.Name -notmatch '^_' }
$canonCount = $canonSkills.Count
Log "canonical: $canonCount"

$cliDirs = @(
    "$env:USERPROFILE\.claude\skills",
    "$env:USERPROFILE\.codex\skills",
    "$env:USERPROFILE\.copilot\skills"
)
$totalRepaired = 0

foreach ($cli in $cliDirs) {
    if (-not (Test-Path $cli)) {
        New-Item -ItemType Directory -Path $cli -Force | Out-Null
        Log "  created missing dir: $cli"
    }
    $repaired = 0
    foreach ($s in $canonSkills) {
        $linkPath = Join-Path $cli $s.Name
        if (-not (Test-Path $linkPath)) {
            $null = cmd /c mklink /J "`"$linkPath`"" "`"$($s.FullName)`"" 2>&1
            if ($LASTEXITCODE -eq 0) { $repaired++ }
        }
    }
    if ($repaired -gt 0) {
        Log "  ${cli}: repaired $repaired missing junctions"
    }
    $totalRepaired += $repaired
}
Log "junction integrity: repaired $totalRepaired"

# 2) Chain index freshness — rebuild if any SKILL.md newer than last build
$buildSummary = "$chainDir\_build_summary.json"
$shouldRebuild = $false
if (-not (Test-Path $buildSummary)) {
    $shouldRebuild = $true
    Log "  no build summary — will rebuild"
} else {
    $buildTime = (Get-Item $buildSummary).LastWriteTime
    $newerSkills = Get-ChildItem $canon -Recurse -Filter 'SKILL.md' -Force -ErrorAction SilentlyContinue |
                   Where-Object { $_.LastWriteTime -gt $buildTime } | Select-Object -First 1
    if ($newerSkills) {
        $shouldRebuild = $true
        Log "  detected newer SKILL.md — will rebuild chain index"
    }
}
if ($shouldRebuild) {
    $env:PYTHONIOENCODING = 'utf-8'
    & python "$chainDir\_scripts\build_chains.py" *>&1 | ForEach-Object { Log "  build: $_" }
}

# 3) Verify all 4 CLI primary instruction files reference skill chain v1
$instructions = @{
    "$env:USERPROFILE\.claude\CLAUDE.md"     = "skill_chain_system_v1"
    "$env:USERPROFILE\.codex\skill_chain_v1.md"   = "Skill Chain System v1"
    "$env:USERPROFILE\.copilot\skill_chain_v1.md" = "Skill Chain System v1"
    "$env:USERPROFILE\.gemini\GEMINI.md"     = "skill_chain_system_v1"
}
foreach ($f in $instructions.Keys) {
    if (Test-Path $f) {
        $content = Get-Content $f -Raw -ErrorAction SilentlyContinue
        if ($content -notmatch [regex]::Escape($instructions[$f])) {
            Log "  WARN: $f missing 'skill_chain_v1' reference"
        }
    } else {
        Log "  WARN: instruction file missing: $f"
    }
}

# 4) Final summary
$finalCount = (Get-ChildItem $canon -Force -Directory | Where-Object { $_.Name -notmatch '^_' }).Count
Log "===== boot check end: $finalCount canonical skills, $totalRepaired junctions repaired ====="

# Trim log to last 200 lines so it doesn't grow forever
if (Test-Path $logFile) {
    $tail = Get-Content $logFile -Tail 200
    $tail | Set-Content $logFile -Encoding UTF8
}
