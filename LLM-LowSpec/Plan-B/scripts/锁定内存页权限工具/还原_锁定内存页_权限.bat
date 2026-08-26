@echo off
chcp 65001 >nul
title 还原锁定内存页权限
echo ================================================
echo   还原 "锁定内存页" 权限
echo   恢复到运行"启用"脚本前的原始状态
echo ================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Set-LockPagesPrivilege.ps1" -Action Revoke
echo.
echo 已还原。请注销或重启系统后生效。
PAUSE