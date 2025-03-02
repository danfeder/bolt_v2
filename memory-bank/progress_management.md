# Progress Management System

This document outlines the progress management system for the Gym Class Rotation Scheduler project.

## Structure

The progress tracking is split across multiple files:

1. `progress.md` - Contains current year's progress (2025) and most recent updates
2. `progress_archive_2024.md` - Contains archived progress from 2024
3. Additional archive files will be created for each year as needed

## Archiving Process

When `progress.md` becomes too large to edit directly (usually around 1000 lines), older entries should be moved to the appropriate archive file:

1. Cut the oldest entries from `progress.md`
2. Paste them at the top of the appropriate archive file
3. Update the table of contents in both files
4. Add a note at the top of `progress.md` mentioning where older entries can be found

## File Size Management

- Keep `progress.md` under 1000 lines for easier editing
- Archive every 3-6 months or when the file size becomes unwieldy
- Maintain consistent formatting across all progress files

## Referencing Archived Information

When referencing archived information, specify both the file name and the date/section for easy lookup:

Example: "As noted in progress_archive_2024.md (October 2024), the initial solver implementation..."
