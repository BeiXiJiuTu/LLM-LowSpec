#requires -RunAsAdministrator
<#
.SYNOPSIS
  授予或移除当前用户的“锁定内存页”(SeLockMemoryPrivilege) 权限。
  用途：解锁 FreeToken 等需要 CUDA 固定内存(pinned memory)的应用。

.PARAMETER Action
  - Grant   : 授予当前用户“锁定内存页”权限（含原始策略备份，可还原）
  - Revoke  : 移除/还原，恢复到运行 Grant 前的状态
.PARAMETER TargetUser
  要处理的目标用户名，默认取“当前登录用户”。
  例：-TargetUser "xwj"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Grant","Revoke")]
    [string]$Action,

    [string]$TargetUser = "$env:USERNAME"
)

$ErrorActionPreference = "Stop"

# 需要管理员权限，用当前用户名的 SID 计算
function Get-UserSid([string]$userName) {
    try {
        $nt = New-Object System.Security.Principal.NTAccount($userName)
        return $nt.Translate([System.Security.Principal.SecurityIdentifier]).Value
    } catch {
        throw "无法解析用户 [$userName]，请确认用户名正确。原始错误: $_"
    }
}

$USER_SID = Get-UserSid -userName $TargetUser

# 输出文件路径（放在脚本同目录）
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackupInf   = Join-Path $ScriptDir "SeLockMemory_Policy_Backup.inf"   # 原始策略备份（Grant 时创建）
$WorkDirXml  = Join-Path $ScriptDir "_work"                              # 临时工作目录
$TempInf     = Join-Path $WorkDirXml "secpol.inf"                        # 每次导出的可编辑副本

# 工具常量
$CMD_SECEDIT    = "$env:SystemRoot\System32\secedit.exe"
$CMD_SDARKPERM  = "$env:SystemRoot\System32\whoami.exe"

function Write-Log([string]$msg) {
    Write-Host ("[$(Get-Date -Format HH:mm:ss)] " + $msg) -ForegroundColor Cyan
}

function Test-LockPrivilege {
    # 检查当前会话是否真的持有该权限（仅做提示，不阻断）
    $privs = & whoami /priv 2>$null | Out-String
    return ($privs -match "SeLockMemoryPrivilege")
}

# ---------- 前置检查 ----------
if (-not (Test-Path $CMD_SECEDIT)) {
    throw "找不到 secedit.exe"
}

# ---------- 核心逻辑 ----------
switch ($Action) {

    "Grant" {
        Write-Log "== 开始授予“锁定内存页”权限 =="

        # 1) 先备份原始策略（仅首次执行时备份，避免覆盖已有备份）
        if (-not (Test-Path $BackupInf)) {
            Write-Log "备份原始安全策略到: $BackupInf"
            & $CMD_SECEDIT /export /cfg $BackupInf /areas USER_RIGHTS | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "备份原始策略失败 (secedit exit=$LASTEXITCODE)" }
            Write-Log "原始策略备份完成"
        } else {
            Write-Log "检测到已存在备份，跳过备份（保持原始备份不受后续 Grant 影响）"
        }

        # 2) 导出当前策略到可编辑副本
        if (-not (Test-Path $WorkDirXml)) { New-Item -ItemType Directory -Path $WorkDirXml | Out-Null }
        & $CMD_SECEDIT /export /cfg $TempInf /areas USER_RIGHTS | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "导出当前策略失败 (secedit exit=$LASTEXITCODE)" }

        # 3) 检查目标权限当前是否已包含该用户
        $content = Get-Content -Path $TempInf -Raw
        $privLine = [regex]::Match($content, '(?m)^\s*SeLockMemoryPrivilege\s*=\s*(?<val>.*)$')
        $already = $false
        if ($privLine.Success -and $privLine.Groups["val"].Value -match [regex]::Escape($USER_SID)) {
            $already = $true
        }

        if ($already) {
            Write-Log "用户 [$TargetUser] ($USER_SID) 已拥有“锁定内存页”权限，无需修改。"
        } else {
            # 4) 追加 SID 到 SeLockMemoryPrivilege
            if ($privLine.Success) {
                $newVal = ($privLine.Groups["val"].Value.Trim().TrimEnd('*')) + ",*" + $USER_SID
                $content = $content -replace '(?m)^(\s*SeLockMemoryPrivilege\s*=\s*).*$', ("$1" + $newVal)
                Write-Log "已追加用户到现有 [Privilege Rights]"
            } else {
                # 若该项不存在，则在 [Privilege Rights] 段末添加
                if ($content -match '(?m)^\[Privilege Rights\]$') {
                    $content = $content -replace '(?m)^(\[Privilege Rights\]\s*)', ("$1`nSeLockMemoryPrivilege = *" + $USER_SID + "`n")
                } else {
                    $content += "`n[Privilege Rights]`nSeLockMemoryPrivilege = *" + $USER_SID + "`n"
                }
                Write-Log "新建 SeLockMemoryPrivilege 条目并加入用户"
            }

            # 5) 写回并应用
            [System.IO.File]::WriteAllText($TempInf, $content, (New-Object System.Text.UTF8Encoding($false)))
            & $CMD_SECEDIT /configure /db "secedit.sdb" /cfg $TempInf /areas USER_RIGHTS /log $ScriptDir\secedit_apply.log | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "应用策略失败 (secedit exit=$LASTEXITCODE)。日志: $ScriptDir\secedit_apply.log" }

            Write-Log "已授予用户 [$TargetUser] ($USER_SID) “锁定内存页”权限。"
        }

        # 6) 提示
        $hasPriv = Test-LockPrivilege
        Write-Host ""
        if ($hasPriv) {
            Write-Host "✅ 当前会话已持有该权限。" -ForegroundColor Green
        } else {
            Write-Host "⚠️  权限已写入策略，但当前会话尚未生效。" -ForegroundColor Yellow
            Write-Host "    建议：注销并重新登录，或**重启系统**后，FreeToken 才能使用大块固定内存。" -ForegroundColor Yellow
        }
        Write-Host "原始策略已在: $BackupInf" -ForegroundColor DarkGray
        Write-Host "运行 Set-LockPagesPrivilege.ps1 -Action Revoke 即可完整还原。" -ForegroundColor DarkGray
    }

    "Revoke" {
        Write-Log "== 开始还原/移除“锁定内存页”权限 =="

        if (-not (Test-Path $BackupInf)) {
            Write-Host "❌ 未找到原始策略备份 ($BackupInf)。" -ForegroundColor Red
            Write-Host "   无法自动还原。若你确认要移除该权限，请手工在 secpol.msc 中从'锁定内存页'里删除用户 [$TargetUser]。" -ForegroundColor Red
            exit 1
        }

        # 1) 直接用原始备份合成一个“还原”文件：复制备份，移除该用户 SID（双重保险）
        if (-not (Test-Path $WorkDirXml)) { New-Item -ItemType Directory -Path $WorkDirXml | Out-Null }
        $restoreInf = Join-Path $WorkDirXml "secpol_restore.inf"
        Copy-Item -Path $BackupInf -Destination $restoreInf -Force

        $content = Get-Content -Path $restoreInf -Raw
        $privLine = [regex]::Match($content, '(?m)^\s*SeLockMemoryPrivilege\s*=\s*(?<val>.*)$')
        if ($privLine.Success) {
            $val = $privLine.Groups["val"].Value.Trim()
            # 移除该用户 SID，同时清理多余分隔符
            $newVal = ($val -replace [regex]::Escape("*$USER_SID"), "")
            $newVal =  $newVal -replace ',\*', '*' -replace '^\*', '' -replace '\*$','' -replace '\s+',' '
            if ([string]::IsNullOrWhiteSpace($newVal.Replace('*','').Replace(',','')) ) {
                $content = $content -replace '(?m)^\s*SeLockMemoryPrivilege\s*=.*\r?\n?', ""
                Write-Log "从还原文件中移除了整条 SeLockMemoryPrivilege（原为仅该用户）"
            } else {
                $content = $content -replace '(?m)^\s*SeLockMemoryPrivilege\s*=\s*.*$', ("SeLockMemoryPrivilege = " + $newVal.Trim())
            }
        }
        [System.IO.File]::WriteAllText($restoreInf, $content, (New-Object System.Text.UTF8Encoding($false)))

        # 2) 应用还原
        & $CMD_SECEDIT /configure /db "secedit.sdb" /cfg $restoreInf /areas USER_RIGHTS /log $ScriptDir\secedit_revoke.log | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "还原策略失败 (secedit exit=$LASTEXITCODE)。日志: $ScriptDir\secedit_revoke.log" }

        Write-Log "已还原，用户 [$TargetUser] 的“锁定内存页”权限已被移除（恢复到授予前）。"
        Write-Host "⚠️  建议注销/重启后彻底生效。" -ForegroundColor Yellow
    }
}

Write-Log "完成。"