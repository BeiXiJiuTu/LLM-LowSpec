@echo off
chcp 65001 >nul
title 授予锁定内存页权限
echo ================================================
echo   授予当前用户 "锁定内存页" 权限
echo   (用于 FreeToken 等需要 CUDA 固定内存的应用)
echo   会做原始策略备份，可随时还原
echo ================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Set-LockPagesPrivilege.ps1" -Action Grant
echo.
echo 已执行。请注销或重启系统后生效。
PAUSE