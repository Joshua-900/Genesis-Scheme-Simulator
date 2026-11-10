@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /O2 /fp:precise /LD roughness_step.c /link /OUT:roughness_step.dll

