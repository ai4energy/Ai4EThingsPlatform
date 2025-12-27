@echo off
:: 等待5秒（给系统加载Chrome和桌面环境留时间，避免启动失败）
timeout /t 5 /nobreak >nul

:: 启动Edge全屏打开
:: start "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --kiosk "file:///D:\develop\Ai4EThingsPlatform\v2.0\物理系统\index.html" --edge-kiosk-type=fullscreen

:: 启动Chrome全屏打开
start "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --kiosk "file:///D:\develop\Ai4EThingsPlatform\v2.0\物理系统\index.html" 