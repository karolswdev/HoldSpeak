# 16b: the hub owns the desk's windows (shots)

`tests/e2e/test_philo16_hub_windows_glass.py`: one hub on an isolated HOME,
three browser contexts.

- `1440-A-and-B.png`: context A after it opened Brief, The week and Needs
  you, dragged Brief and seated The week. On the right, context B, a fresh load
  with an empty cache: the same windows, Brief at the same rect, Brief in front
  in both views, The week seated on the Dock.
- `1440-A-follows-B.png`: B raised Needs you; A followed without a reload.
- `1440-A-and-B-tile.png`: the MCP tool `desk_window.arrange` tiled Brief and
  Needs you; both views show the tile.
- `393-C-go-chair.png`: context C at 393, a fresh load: Go lists the three
  Chair windows open. The week is seated (its cache holds `chair:week` in
  `panel.min`).
- `hub-writes.json`: every window write each view sent, in order. The 393 load
  sent none.

## The hub's rows

`GET /api/desk/windows` after A's three actions (`hub-rows.json`):

```json
{
  "windows": [
    {
      "id": "chair:needs",
      "app": "chair",
      "object_ref": null,
      "x": null,
      "y": null,
      "w": null,
      "h": null,
      "depth": 3,
      "minimized": false,
      "zoomed": false,
      "zoom": null,
      "arranged": false,
      "room": null,
      "front": false,
      "revision": 1,
      "updated_at": "2026-10-09 11:06:20"
    },
    {
      "id": "chair:brief",
      "app": "chair",
      "object_ref": null,
      "x": "-10.7042%",
      "y": "-40.9091%",
      "w": "49.1549%",
      "h": "62.7942%",
      "depth": 4,
      "minimized": false,
      "zoomed": false,
      "zoom": null,
      "arranged": true,
      "room": null,
      "front": true,
      "revision": 3,
      "updated_at": "2026-10-09 11:06:20"
    },
    {
      "id": "chair:week",
      "app": "chair",
      "object_ref": null,
      "x": null,
      "y": null,
      "w": null,
      "h": null,
      "depth": 5,
      "minimized": true,
      "zoomed": false,
      "zoom": null,
      "arranged": false,
      "room": null,
      "front": false,
      "revision": 3,
      "updated_at": "2026-10-09 11:06:21"
    }
  ],
  "stage_shelf": "left",
  "revision": 0,
  "registry": "(the registry: static ids and families; elided here)"
}
```

Brief's rect is share+px, recorded against A's band. Each view resolves it
against its own band. Depth is the hub's counter. The front window is derived.
