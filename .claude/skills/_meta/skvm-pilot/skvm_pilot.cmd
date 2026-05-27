@echo off
REM ─────────────────────────────────────────────────────────────────────────
REM SkVM Pilot Setup Script (Phase 3 of AHE+Ctx2Skill+SkVM integration)
REM Based on arXiv:2604.03088 (Chen et al., SJTU IPADS)
REM
REM What this does:
REM  1. Install @ipads-skvm/skvm via npm (global)
REM  2. Run `skvm config init` (interactive — set up harness + provider)
REM  3. Profile 5 high-frequency skills across current LLMs
REM  4. Print where to find results
REM
REM Cost: ~$5-10 (token cost during profiling)
REM Time: ~30-60 minutes
REM
REM SAFETY: Each step interactive — choice /M prompts before action.
REM ─────────────────────────────────────────────────────────────────────────

setlocal

set PROFILE_DIR=%USERPROFILE%\.claude\projects\C--Users-Administrator\skvm-profile
if not exist "%PROFILE_DIR%" mkdir "%PROFILE_DIR%"

echo.
echo ============================================
echo SkVM Pilot Setup (each step asks for confirmation)
echo ============================================

echo.
echo Step 1: Install SkVM CLI
echo   command: npm i -g @ipads-skvm/skvm
echo.
choice /M "Run npm install"
if errorlevel 2 goto skip_install
call npm i -g @ipads-skvm/skvm
:skip_install

echo.
echo Step 2: Initialize SkVM config
echo   command: skvm config init
echo   注: 选 harness (Claude Code / OpenClaw / Hermes / pi) 和 LLM provider
echo       custom provider 配置 tone.nyc.mn (base + key from api-credentials.env)
echo.
choice /M "Run skvm config init"
if errorlevel 2 goto skip_init
call skvm config init
:skip_init

echo.
echo Step 3: Pilot profile - 5 high-frequency skills, current LLMs
echo   skills to profile (suggested):
echo     - task-router       (Funnel core)
echo     - daozhi-distill    (蒸馏)
echo     - scrnaseq-pipeline (heavy bio)
echo     - wos-starter-search (lit search)
echo     - cs-paper-self-review (writing)
echo   output: %PROFILE_DIR%\round1.json
echo.
choice /M "Run skvm profile --help (first see CLI options)"
if errorlevel 2 goto skip_profile
call skvm profile --help

echo.
echo 看完 --help 后请手动跑：
echo   skvm profile ^
echo     --skills %USERPROFILE%\.gemini\skills\task-router ^
echo     --skills %USERPROFILE%\.gemini\skills\daozhi-distill ^
echo     --skills %USERPROFILE%\.gemini\skills\scrnaseq-pipeline ^
echo     --skills %USERPROFILE%\.gemini\skills\wos-starter-search ^
echo     --skills %USERPROFILE%\.gemini\skills\cs-paper-self-review ^
echo     --output %PROFILE_DIR%\round1.json

:skip_profile

echo.
echo ============================================
echo Pilot setup done. Manual next steps:
echo   1. Check %PROFILE_DIR%\ for profiling results
echo   2. If profiling worked, try AOT compile on 1 skill:
echo        skvm compile <path-to-skill> --target claude-code+opus-4.7
echo   3. Compare token/latency before vs after with a real query
echo   4. If 5x speedup or 20%% token reduction met -^> expand to 50 skills
echo   5. If not -^> revert per Phase 3 撤回条件 (见 README.md)
echo ============================================

endlocal
