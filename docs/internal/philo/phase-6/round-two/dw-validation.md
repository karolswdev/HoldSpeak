# Partial validation - PHILO-6-03 round two

- **Story:** PHILO-6-03 - The toast that does not cover
- **Status:** in-progress; component/canvas proof only, no story flip
- **Date:** 2026-09-24

The DW capture template initially labels evidence `done`; that label is corrected
here because these are partial captures and the story remains in progress.
The canvas capture stdout was truncated by DW; `canvas/facts.json` retains
all 14 results, and its recorded command exit was 0.

## Proof

### Captured run — 2026-09-25T03:59:36Z

- **Command:** `.venv/bin/python docs/internal/philo/phase-6/round-two/zero-component/shoot.py docs/internal/philo/phase-6/round-two/zero-component`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f230ede00b085d6c86283b1e3daa66956a7c2673

```text
[
  {
    "width": 1440,
    "height": 900,
    "card": {
      "x": 440,
      "y": 677,
      "width": 560,
      "height": 119
    },
    "openProposals": false,
    "dismissed": true,
    "pageErrors": [],
    "kind": "actual AmbientLayer + real publishAftercare component fixture, no hub/walk"
  },
  {
    "width": 393,
    "height": 852,
    "card": {
      "x": 16,
      "y": 601,
      "width": 361,
      "height": 147
    },
    "openProposals": false,
    "dismissed": true,
    "pageErrors": [],
    "kind": "actual AmbientLayer + real publishAftercare component fixture, no hub/walk"
  }
]
```

### Captured run — 2026-09-25T04:05:14Z

- **Command:** `.venv/bin/python docs/internal/philo/phase-6/toast/canvas/harness/shoot.py docs/internal/philo/phase-6/round-two/canvas`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f230ede00b085d6c86283b1e3daa66956a7c2673

```text
{
  "today-1440": {
    "board": "today",
    "query": "?board=today",
    "viewport": {
      "width": 1440,
      "height": 900
    },
    "card": {
      "x": 440,
      "y": 644,
      "width": 560,
      "height": 152,
      "right": 1000,
      "bottom": 796
    },
    "card_in_viewport": true,
    "summary_well": {
      "x": 296,
      "y": 359.59375,
      "width": 888,
      "height": 92,
      "right": 1184,
      "bottom": 451.59375
    },
    "summary_text": {
      "x": 300,
      "y": 391.59375,
      "width": 880,
      "height": 54,
      "right": 1180,
      "bottom": 445.59375
    },
    "capture_bar": {
      "x": 256,
      "y": 758,
      "width": 928,
      "height": 74,
      "right": 1184,
      "bottom": 832
    },
    "active_sections": {
      "NO CALENDAR": {
        "x": 256,
        "y": 122.59375,
        "width": 928,
        "height": 33,
        "right": 1184,
        "bottom": 155.59375
      },
      "BRIEF": {
        "x": 256,
        "y": 179.59375,
        "width": 928,
        "height": 33,
        "right": 1184,
        "bottom": 212.59375
      },
      "MEETINGS \u00b7 1": {
        "x": 256,
        "y": 268.59375,
        "width": 928,
        "height": 27,
        "right": 1184,
        "bottom": 295.59375
      }
    },
    "surface_regions": {},
    "chrome_regions": {
      "menubar": {
        "x": 0,
        "y": 0,
        "width": 1440,
        "height": 28,
        "right": 1440,
        "bottom": 28
      },
      "dock": {
        "x": 288.2890625,
        "y": 849,
        "width": 863.421875,
        "height": 51,
        "right": 1151.7109375,
        "bottom": 900
      }
    },
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": true,
    "card_overlaps_surface": {},
    "card_overlaps_chrome": {
      "menubar": false,
      "dock": false
    },
    "floor_content_visible": true,
    "chair_scroll_top": 0,
    "scroll_width": 1440,
    "button_count": 2,
    "capture_state": "idle-mic"
  },
  "proposed-1440": {
    "board": "proposed",
    "query": "?board=proposed",
    "viewport": {
      "width": 1440,
      "height": 900
    },
    "card": {
      "x": 440,
      "y": 391.59375,
      "width": 560,
      "height": 152,
      "right": 1000,
      "bottom": 543.59375
    },
    "card_in_viewport": true,
    "summary_well": null,
    "summary_text": null,
    "capture_bar": {
      "x": 256,
      "y": 758,
      "width": 928,
      "height": 74,
      "right": 1184,
      "bottom": 832
    },
    "active_sections": {
      "NO CALENDAR": {
        "x": 256,
        "y": 122.59375,
        "width": 928,
        "height": 33,
        "right": 1184,
        "bottom": 155.59375
      },
      "BRIEF": {
        "x": 256,
        "y": 179.59375,
        "width": 928,
        "height": 33,
        "right": 1184,
        "bottom": 212.59375
      },
      "MEETINGS \u00b7 1": {
        "x": 256,
        "y": 268.59375,
        "width": 928,
        "height": 27,
        "right": 1184,
        "bottom": 295.59375
      }
    },
    "surface_regions": {},
    "chrome_regions": {
      "menubar": {
        "x": 0,
        "y": 0,
        "width": 1440,
        "height": 28,
        "right": 1440,
        "bottom": 28
      },
      "dock": {
        "x": 288.2890625,
        "y": 849,
        "width": 863.421875,
        "height": 51,
        "right": 1151.7109375,
        "bottom": 900
      }
    },
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "card_overlaps_surface": {},
    "card_overlaps_chrome": {
      "menubar": false,
      "dock": false
    },
    "floor_content_visible": true,
    "chair_scroll_top": 0,
    "scroll_width": 1440,
    "button_count": 2,
    "capture_state": "idle-mic"
  },
  "summary-open-1440": {
    "board": "summary-open",
    "query": "?board=summary-open",
    "viewport": {
      "width": 1440,
      "height": 900
    },
    "card": {
      "x": 440,
      "y": 495.59375,
      "width": 560,
      "height": 152,
      "right": 1000,
      "bottom": 647.59375
    },
    "card_in_viewport": true,
    "summary_well": {
      "x": 296,
      "y": 359.59375,
      "width": 888,
      "height": 92,
      "right": 1184,
      "bottom": 451.59375
    },
    "summary_text": {
      "x": 300,
      "y": 391.59375,
      "width": 880,
      "height": 54,
      "right": 1180,
      "bottom": 445.59375
    },
    "capture_bar": {
      "x": 256,
      "y": 758,
      "width": 928,
      "height": 74,
      "right": 1184,
      "bottom": 832
    },
    "active_sections": {
      "NO CALENDAR": {
        "x": 256,
        "y": 122.59375,
        "width": 928,
        "height": 33,
        "right": 1184,
        "bottom": 155.59375
      },
      "BRIEF": {
        "x": 256,
        "y": 179.59375,
        "width": 928,
        "height": 33,
        "right": 1184,
        "bottom": 212.59375
      },
      "MEETINGS \u00b7 1": {
        "x": 256,
        "y": 268.59375,
        "width": 928,
        "height": 27,
        "right": 1184,
        "bottom": 295.59375
      }
    },
    "surface_regions": {},
    "chrome_regions": {
      "menubar": {
        "x": 0,
        "y": 0,
        "width": 1440,
        "height": 28,
        "right": 1440,
        "bottom": 28
      },
      "dock": {
        "x": 288.2890625,
        "y": 849,
        "width": 863.421875,
        "height": 51,
        "right": 1151.7109375,
        "bottom": 900
      }
    },
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "card_overlaps_surface": {},
    "card_overlaps_chrome": {
      "menubar": false,
      "dock": false
    },
    "floor_content_visible": true,
    "chair_scroll_top": 0,
    "scroll_width": 1440,
    "button_count": 2,
    "capture_state": "idle-mic"
  },
  "capture-1440": {
    "board": "capture",
    "query": "?board=capture",
    "viewport": {
      "width": 1440,
      "height": 900
    },
    "card": {
      "x": 440,
      "y": 495.59375,
      "width": 560,
      "height": 152,
      "right": 1000,
      "bottom": 647.59375
    },
    "card_in_viewport": true,
    "summary_well": {
      "x": 296,
      "y": 359.59375,
      "width": 888,
      "height": 92,
      "right": 1184,
      "bottom": 451.59375
    },
    "summary_text": {
      "x": 300,
      "y": 391.59375,
      "width": 880,
      "height": 54,
      "right": 1180,
      "bottom": 445.59375
    },
    "capture_bar": {
      "x": 256,
      "y": 758,
      "width": 928,
      "height": 74,
      "right": 1184,
      "bottom": 832
    },
    "active_sections": {
      "NO CALENDAR": {
        "x": 256,
        "y": 122.59375,
        "width": 928,
        "height": 33,
        "right": 1184,
        "bottom": 155.59375
      },
      "BRIEF": {
        "x": 256,
        "y": 179.59375,
        "width": 928,
        "height": 33,
        "right": 1184,
        "bottom": 212.59375
      },
      "MEETINGS \u00b7 1": {
        "x": 256,
        "y": 268.59375,
        "width": 928,
        "height": 27,
        "right": 1184,
        "bottom": 295.59375
      }
    },
    "surface_regions": {},
    "chrome_regions": {
      "menubar": {
        "x": 0,
        "y": 0,
        "width": 1440,
        "height": 28,
        "right": 1440,
        "bottom": 28
      },
      "dock": {
        "x": 288.2890625,
        "y": 849,
        "width": 863.421875,
        "height": 51,
        "right": 1151.7109375,
        "bottom": 900
      }
    },
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "card_overlaps_surface": {},
    "card_overlaps_chrome": {
      "menubar": false,
      "dock": false
    },
    "floor_content_visible": true,
    "chair_scroll_top": 0,
    "scroll_width": 1440,
    "button_count": 2,
    "capture_state": "pressed-mic"
  },
  "meetings-1440": {
    "board": "meetings",
    "query": "?board=meetings",
    "viewport": {
      "width": 1440,
      "height": 900
    },
    "card": {
      "x": 39,
      "y": 133,
      "width": 610,
      "height": 152,
      "right": 649,
      "bottom": 285
    },
    "card_in_viewport": true,
    "summary_well": null,
    "summary_text": null,
    "capture_bar": null,
    "active_sections": {
      "MEETINGS \u00b7 1": {
        "x": 39,
        "y": 341.890625,
        "width": 610,
        "height": 27,
        "right": 649,
        "bottom": 368.890625
      }
    },
    "surface_regions": {
      "titlebar": {
        "x": 25,
        "y": 73,
        "width": 638,
        "height": 40,
        "right": 663,
        "bottom": 113
      },
      "content": {
        "x": 39,
        "y": 312,
        "width": 610,
        "height": 186.890625,
        "right": 649,
        "bottom": 498.890625
      }
    },
    "chrome_regions": {
      "menubar": {
        "x": 0,
        "y": 0,
        "width": 1440,
        "height": 28,
        "right": 1440,
        "bottom": 28
      },
      "dock": {
        "x": 258.2890625,
        "y": 849,
        "width": 923.421875,
        "height": 51,
        "right": 1181.7109375,
        "bottom": 900
      }
    },
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "card_overlaps_surface": {
      "titlebar": false,
      "content": false
    },
    "card_overlaps_chrome": {
      "menubar": false,
      "dock": false
    },
    "floor_content_visible": true,
    "chair_scroll_top": null,
    "scroll_width": 1440,
    "button_count": 2,
    "capture_state": "idle-mic"
  },
  "floor-1440": {
    "board": "floor",
    "query": "?board=floor",
    "viewport": {
      "width": 1440,
      "height": 900
    },
    "card": {
      "x": 440,
      "y": 66,
      "width": 560,
      "height": 152,
      "right": 1000,
      "bottom": 218
    },
    "card_in_viewport": true,
    "summary_well": null,
    "summary_text": null,
    "capture_bar": null,
    "active_sections": {},
    "surface_regions": {
      "work_area": {
        "x": 0,
        "y": 230,
        "width": 1440,
        "height": 598,
        "right": 1440,
        "bottom": 828
      },
      "floor_content": {
        "x": 160,
        "y": 323.390625,
        "width": 1120,
        "height": 266,
        "right": 1280,
        "bottom": 589.390625
      }
    },
    "chrome_regions": {
      "menubar": {
        "x": 0,
        "y": 0,
        "width": 1440,
        "height": 28,
        "right": 1440,
        "bottom": 28
      },
      "dock": {
        "x": 288.2890625,
        "y": 849,
        "width": 863.421875,
        "height": 51,
        "right": 1151.7109375,
        "bottom": 900
      }
    },
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "card_overlaps_surface": {
      "work_area": false,
      "floor_content": false
    },
    "card_overlaps_chrome": {
      "menubar": false,
      "dock": false
    },
    "floor_content_visible": true,
    "chair_scroll_top": null,
    "scroll_width": 1440,
    "button_count": 2,
    "capture_state": "idle-mic"
  },
  "summary-open-long-1440": {
    "board": "summary-open-long",
    "query": "?board=summary-open&summary=long",
    "viewport": {
      "width": 1440,
      "height": 900
    },
    "card": {
      "x": 440,
      "y": 513.59375,
      "width": 560,
      "height": 152,
      "right": 1000,
      "bottom": 665.59375
    },
    "card_in_viewport": true,
    "summary_well": {
      "x": 296,
      "y": 359.59375,
      "width": 888,
      "height": 110,
      "right": 1184,
      "bottom": 469.59375
    },
    "summary_text": {
      "x": 300,
      "y": 391.59375,
      "width": 880,
      "height": 72,
      "right": 1180,
      "bottom": 463.59375
    },
    "capture_bar": {
      "x": 256,
      "y": 758,
      "width": 928,
      "height": 74,
      "right": 1184,
      "bottom": 832
    },
    "active_sections": {
      "NO CALENDAR": {
        "x": 256,
        "y": 122.59375,
        "width": 928,
        "height": 33,
        "right": 1184,
        "bottom": 155.59375
      },
      "BRIEF": {
        "x": 256,
        "y": 179.59375,
        "width": 928,
        "height": 33,
        "right": 1184,
        "bottom": 212.59375
      },
      "MEETINGS \u00b7 1": {
        "x": 256,
        "y": 268.59375,
        "width": 928,
        "height": 27,
        "right": 1184,
        "bottom": 295.59375
      }
    },
    "surface_regions": {},
    "chrome_regions": {
      "menubar": {
        "x": 0,
        "y": 0,
        "width": 1440,
        "height": 28,
        "right": 1440,
        "bottom": 28
      },
      "dock": {
        "x": 288.2890625,
        "y": 849,
        "width": 863.421875,
        "height": 51,
        "right": 1151.7109375,
        "bottom": 900
      }
    },
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "card_overlaps_surface": {},
    "card_overlaps_chrome": {
      "menubar": false,
      "dock": false
    },
    "floor_content_visible": true,
    "chair_scroll_top": 0,
    "scroll_width": 1440,
    "button_count": 2,
    "capture_state": "idle-mic"
  },
  "today-393": {
    "board": "today",
    "query": "?board=today",
    "viewport": {
      "width": 393,
      "height": 852
    },
    "card": {
      "x": 16,
      "y": 568,
      "width": 361,
      "height": 180,
      "right": 377,
      "bottom": 748
    },
    "card_in_viewport": true,
    "summary_well": {
      "x": 12,
      "y": 456.59375,
      "width": 369,
      "height": 146,
      "right": 381,
      "bottom": 602.59375
    },
    "summary_text": {
      "x": 16,
      "y": 488.59375,
      "width": 361,
      "height": 108,
      "right": 377,
      "bottom": 596.59375
    },
    "capture_bar": {
      "x": 12,
      "y": 573,
      "width": 369,
      "height": 138,
      "right": 381,
      "bottom": 711
    },
    "active_sections": {
      "NO CALENDAR": {
        "x": 12,
        "y": 110.59375,
        "width": 369,
        "height": 61,
        "right": 381,
        "bottom": 171.59375
      },
      "BRIEF": {
        "x": 12,
        "y": 187.59375,
        "width": 369,
        "height": 61,
        "right": 381,
        "bottom": 248.59375
      },
      "MEETINGS \u00b7 1": {
        "x": 12,
        "y": 296.59375,
        "width": 369,
        "height": 27,
        "right": 381,
        "bottom": 323.59375
      }
    },
    "surface_regions": {},
    "chrome_regions": {
      "menubar": {
        "x": 0,
        "y": 0,
        "width": 393,
        "height": 28,
        "right": 393,
        "bottom": 28
      },
      "dock": {
        "x": 0,
        "y": 727,
        "width": 393,
        "height": 125,
        "right": 393,
        "bottom": 852
      }
    },
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": true,
    "card_overlaps_summary_well": true,
    "card_overlaps_capture_bar": true,
    "card_overlaps_surface": {},
    "card_overlaps_chrome": {
      "menubar": false,
      "dock": true
    },
    "floor_content_visible": true,
    "chair_scroll_top": 0,
    "scroll_width": 393,
    "button_count": 2,
    "capture_state": "idle-mic"
  },
  "proposed-393": {
    "board": "proposed",
    "query": "?board=proposed",
    "viewport": {
      "width": 393,
      "height": 852
    },
    "card": {
      "x": 12,
      "y": 381.59375,
      "width": 369,
      "height": 180,
      "right": 381,
      "bottom": 561.59375
    },
    "card_in_viewport": true,
    "summary_well": null,
    "summary_text": null,
    "capture_bar": {
      "x": 12,
      "y": 573,
      "width": 369,
      "height": 138,
      "right": 381,
      "bottom": 711
    },
    "active_sections": {
      "NO CALENDAR": {
        "x": 12,
        "y": 11.59375,
        "width": 369,
        "height": 61,
        "right": 381,
        "bottom": 72.59375
      },
      "BRIEF": {
        "x": 12,
        "y": 88.59375,
        "width": 369,
        "height": 61,
        "right": 381,
        "bottom": 149.59375
      },
      "MEETINGS \u00b7 1": {
        "x": 12,
        "y": 197.59375,
        "width": 369,
        "height": 27,
        "right": 381,
        "bottom": 224.59375
      }
    },
    "surface_regions": {},
    "chrome_regions": {
      "menubar": {
        "x": 0,
        "y": 0,
        "width": 393,
        "height": 28,
        "right": 393,
        "bottom": 28
      },
      "dock": {
        "x": 0,
        "y": 727,
        "width": 393,
        "height": 125,
        "right": 393,
        "bottom": 852
      }
    },
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "card_overlaps_surface": {},
    "card_overlaps_chrome": {
      "menubar": false,
      "dock": false
    },
    "floor_content_visible": true,
    "chair_scroll_top": 99,
    "scroll_width": 393,
    "button_count": 2,
    "capture_state": "idle-mic"
  },
  "summary-open-393": {
    "board": "summary-open",
    "query": "?board=summary-open",
    "viewport": {
      "width": 393,
      "height": 852
    },
    "card": {
      "x": 12,
      "y": 373.59375,
      "width": 369,
      "height": 180,
      "right": 381,
      "bottom": 553.59375
    },
    "card_in_viewport": true,
    "summary_well": {
      "x": 12,
      "y": 191.59375,
      "width": 369,
      "height": 146,
      "right": 381,
      "bottom": 337.59375
    },
    "summary_text": {
      "x": 16,
      "y": 223.59375,
      "width": 361,
      "height": 108,
      "right": 377,
      "bottom": 331.59375
    },
    "capture_bar": {
      "x": 12,
      "y": 573,
      "width": 369,
      "height": 138,
      "right": 381,
      "bottom": 711
    },
    "active_sections": {
      "NO CALENDAR": {
        "x": 12,
        "y": -154.40625,
        "width": 369,
        "height": 61,
        "right": 381,
        "bottom": -93.40625
      },
      "BRIEF": {
        "x": 12,
        "y": -77.40625,
        "width": 369,
        "height": 61,
        "right": 381,
        "bottom": -16.40625
      },
      "MEETINGS \u00b7 1": {
        "x": 12,
        "y": 31.59375,
        "width": 369,
        "height": 27,
        "right": 381,
        "bottom": 58.59375
      }
    },
    "surface_regions": {},
    "chrome_regions": {
      "menubar": {
        "x": 0,
        "y": 0,
        "width": 393,
        "height": 28,
        "right": 393,
        "bottom": 28
      },
      "dock": {
        "x": 0,
        "y": 727,
        "width": 393,
        "height": 125,
        "right": 393,
        "bottom": 852
      }
    },
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "card_overlaps_surface": {},
    "card_overlaps_chrome": {
      "menubar": false,
      "dock": 
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
