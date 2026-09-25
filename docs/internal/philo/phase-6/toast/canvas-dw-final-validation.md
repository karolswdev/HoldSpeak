# Evidence - PHILO-6-03

- **Story:** PHILO-6-03 - The toast that does not cover
- **Status:** partial — owner ratification pending
- **Date:** 2026-09-24

## Proof

### Captured run — 2026-09-25T03:22:19Z

- **Command:** `bash -c set -euo pipefail; export HOME=$(mktemp -d); export HOLDSPEAK_EVIDENCE_WRITE=1; export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; .venv/bin/python docs/internal/philo/phase-6/toast/canvas/harness/shoot.py docs/internal/philo/phase-6/toast/parent-shots; git apply --check docs/internal/philo/phase-6/toast/chairhome.patch; git diff --exit-code -- web/src/desk/chair/ChairHome.tsx; git status --short pm/roadmap/holdspeak/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 705d21af76797a847f58927ac6c4a3f27d3480a4

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
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": true,
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
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
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
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
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
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "chair_scroll_top": 0,
    "scroll_width": 1440,
    "button_count": 2,
    "capture_state": "pressed-mic"
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
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
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
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": true,
    "card_overlaps_summary_well": true,
    "card_overlaps_capture_bar": true,
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
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
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
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "chair_scroll_top": 265,
    "scroll_width": 393,
    "button_count": 2,
    "capture_state": "idle-mic"
  },
  "capture-393": {
    "board": "capture",
    "query": "?board=capture",
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
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "chair_scroll_top": 265,
    "scroll_width": 393,
    "button_count": 2,
    "capture_state": "pressed-mic"
  },
  "summary-open-long-393": {
    "board": "summary-open-long",
    "query": "?board=summary-open&summary=long",
    "viewport": {
      "width": 393,
      "height": 852
    },
    "card": {
      "x": 12,
      "y": 362.59375,
      "width": 369,
      "height": 180,
      "right": 381,
      "bottom": 542.59375
    },
    "summary_well": {
      "x": 12,
      "y": 126.59375,
      "width": 369,
      "height": 200,
      "right": 381,
      "bottom": 326.59375
    },
    "summary_text": {
      "x": 16,
      "y": 158.59375,
      "width": 361,
      "height": 162,
      "right": 377,
      "bottom": 320.59375
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
        "y": -219.40625,
        "width": 369,
        "height": 61,
        "right": 381,
        "bottom": -158.40625
      },
      "BRIEF": {
        "x": 12,
        "y": -142.40625,
        "width": 369,
        "height": 61,
        "right": 381,
        "bottom": -81.40625
      },
      "MEETINGS \u00b7 1": {
        "x": 12,
        "y": -33.40625,
        "width": 369,
        "height": 27,
        "right": 381,
        "bottom": -6.40625
      }
    },
    "card_text": "MEETING READY\nArchitecture review\n\n3 open\n\nOpen proposals\nDismiss",
    "card_overlaps_summary_text": false,
    "card_overlaps_summary_well": false,
    "card_overlaps_capture_bar": false,
    "chair_scroll_top": 330,
    "scroll_width": 393,
    "button_count": 2,
    "capture_state": "idle-mic"
  }
}
{
  "browser_errors": []
}
```

Final canvas recapture after Muad'Dib counsel: distinct pressed-mic fixture; placement remains unbuilt. Paired done evidence is deferred until story completion.
