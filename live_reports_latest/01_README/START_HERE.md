# START HERE — Backtesting Updates Package

This folder is organized to make handoff to your desktop backtesting machine simple and consistent.

## Order of Use
1. 02_Reports/Backtesting_Adjustments_Report_2025-09-26.md — read summary of learnings and adjustments
2. 04_Configs/optimized_backtesting_config.yaml — review/merge config changes
3. 03_Checklists/Backtesting_Implementation_Checklist.md — implement step-by-step
4. 06_DataContracts/* — validate data formats and schemas
5. 05_Scripts/run_backtesting.py — run tests/optimization per README and checklist
6. 07_Results/ — store outputs; keep dated subfolders
7. 99_Archive/ — move deprecated/old files here

## Key Files
- Existing overview: 02_Reports/Backtesting_Fix_Update_Summary.md
- Desktop script: 05_Scripts/run_backtesting.py
- Configs: 04_Configs/*.yaml

## Notes
- Keep naming: YYYY-MM-DD in new files and result folders
- Do not overwrite; create new dated versions
- Validate slippage/spread/news modeling is enabled
