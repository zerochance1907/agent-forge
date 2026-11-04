@echo off
rem Entry point for Windows Task Scheduler. Advances the pipeline as far as it can.
cd /d "%~dp0"
python forge.py run >> logs\scheduler.log 2>&1
