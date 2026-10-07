# Parked: the old system sprites (2026-10-07)

The Dock and chrome sprites of the HS-135-14 "bright mold", parked (not
deleted) when PHILO Phase 14 lane A0b redrew the set in the D1 "Workbench+"
mold (ruling: `docs/internal/philo/phase-14/icons/README.md`).

The new set was drawn by PixelLab at 32 px (one `create_1_direction_object`
call, review object `cf4c9f3f-a901-44e0-9dc8-50e9d263c4af`, D1 stem). Nothing
in the product references this folder; `systemSprites.ts` registers only the
files one level up.
