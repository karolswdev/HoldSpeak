# Restoring Device-Side Audio Output

The AIPI-Lite firmware in `aipi.yaml` **deliberately ships without a
speaker / media_player / amplifier-toggle stack**. The bridge.py
thin-forwarder architecture is one-way (mic → HoldSpeak); HoldSpeak
does not push audio back, so plumbing the device-side TTS path costs
PSRAM, init complexity, and an EMI workaround that pays no rent.

This doc captures the knowledge that came out of `aipi.yaml` so a
future "HoldSpeak speaks back" story doesn't have to rediscover it
the hard way. Most of these defaults exist because Karol burned hours
chasing them on real hardware — the workarounds are not optional;
the chip + board have specific quirks.

The exact removed YAML lives in this file's [§4 Paste-back blocks](#4-paste-back-blocks).
Earlier git history (pre-removal commit) also has the working version
under `aipi.yaml` if you'd rather diff than copy.

---

## 1. Why removed

- **bridge.py architecture (AIPI-2 thin forwarder):** mic → HoldSpeak
  WS → host typing. The device never plays anything; LCD is the only
  output channel.
- **Cost when unused:** the `media_player:` announcement pipeline
  reserves PSRAM (≥ 8 KB internal buffer + announcement chain), the
  EMI workaround toggles GPIO9 / re-mutes the ES8311 on every turn,
  and `restore_mic` ran on every continuous-mode turn — all dead work
  for the v1 design.
- **Cost-of-recovery:** low. The chip (ES8311) is still wired up for
  the mic, the i2s_audio bus is still defined, and re-adding the
  `speaker:` and `media_player:` blocks plus a couple of API services
  brings playback back. No firmware-level surgery required.

## 2. Hardware quirks (the part that matters)

These are **not** documented anywhere in ESPHome's docs. They
were discovered empirically on the AIPI-Lite (ESP32-S3 + ES8311 +
amp) by the upstream sticks918 work and Karol's debugging. If you
re-introduce the speaker stack and skip any of these, the device
will appear to work but produce garbage on the speaker, garbage on
the mic, or both.

### 2.1 Octal PSRAM is mandatory

```yaml
psram:
  mode: octal
```

The `media_player:` `announcement_pipeline` allocates a large HTTP
buffer for streaming WAVs over the network. With `mode: quad` (the
ESPHome default), the SRAM gets fragmented enough that the I2S mic
DMA buffer fails to allocate at runtime — symptom is "mic stops
working after the first announcement plays." `mode: octal` keeps the
heap headroom large enough for both pipelines to coexist.

This setting is currently kept in `aipi.yaml` even though no speaker
is wired up — it costs nothing and the board supports it, and ripping
it out would force re-discovery on the next attempt.

### 2.2 The EMI dance: GPIO9 cuts amp power during mic capture

The amplifier (powered via GPIO9 = `speaker_enable`) bleeds the WiFi
antenna's RF noise into the analog mic line as **deafening white
noise**. The mic is unusable while the amp is powered.

The workaround:

1. **Default state:** `speaker_enable = LOW` (amp off).
2. **Before playback:** set `speaker_enable = HIGH`, wait 50 ms for
   the amp to settle, unmute the ES8311 DAC.
3. **After playback:** stop the media_player, mute the ES8311 DAC,
   then `speaker_enable = LOW` again.
4. **Mic capture happens with the amp OFF.**

The 50 ms settling delay isn't arbitrary — shorter delays produce a
"pop" at the start of the WAV; longer delays delay the user's
prompt. 50 ms was the sweet spot.

Currently in `aipi.yaml`: `speaker_enable` is held `restore_mode: ALWAYS_OFF`
+ `internal: true` so the amp can never power up by accident. To
re-enable playback, flip to `restore_mode: ALWAYS_ON` (or remove
`internal:` so HA can toggle it) and re-add the `prepare_speaker` /
`restore_mic` services in §4.

### 2.3 ES8311 deep mute via raw I2C

ESPHome's `media_player.stop:` does **not** physically release the
DAC; the chip keeps driving the I2S clocks at idle, which (a) wastes
power and (b) creates a low-level hiss on the speaker. Worse, on
this board, idle DAC clocks couple onto the shared I2S data lines and
**corrupt the mic capture** even with the amp off.

The fix is a raw I2C poke to the ES8311's mute register (REG31 = 0x31):

```cpp
// Mute (deep — releases I2S clocks at idle)
uint8_t mute[] = {0x31, 0xFF};
id(i2c_es8311)->write(0x18, mute, 2, true);

// Unmute (for playback)
uint8_t unmute[] = {0x31, 0x00};
id(i2c_es8311)->write(0x18, unmute, 2, true);
```

This bypasses ESPHome's `audio_dac:` abstraction (which doesn't expose
the chip-specific mute path). 0x18 is the ES8311's I2C address;
0x31 is the mute register; 0xFF is "all bits muted," 0x00 is "all
bits unmuted." Don't substitute partial-mute values — the bug only
goes away with deep mute.

### 2.4 Don't lock the speaker bus from `voice_assistant`

`voice_assistant:` in ESPHome can be configured with both `speaker:`
and `microphone:` IDs, in which case it tries to coordinate playback
+ capture. **On this hardware, that locks the I2S bus and deadlocks
the state machine after the first turn.** The original repo's
solution was strictly listen-only:

```yaml
voice_assistant:
  id: va
  microphone: i2s_mic     # mic only, no speaker reference
```

The bridge handles all output orchestration — when re-introducing
playback, do it via the `media_player:` component invoked by an API
service the bridge calls, **not** by giving `voice_assistant:` the
`speaker:` reference.

### 2.5 ES8311 mic gain on the analog path

```yaml
audio_dac:
  - platform: es8311
    id: es8311_dac
    address: 0x18
    mic_gain: 42DB
```

`use_microphone:` (which would enable the chip's PDM digital mic
path) is intentionally NOT set — the AIPI-Lite uses the analog MIC1
path, which is on by default (REG14 = 0x1A in `es8311.cpp`). The
`mic_gain: 42DB` is what brings the analog mic level up to where
faster-whisper / HoldSpeak can transcribe at conversational distance
(~30 cm). 36 dB and below produce intermittent transcripts; above
48 dB clips on loud speakers.

## 3. bridge.py changes required

These are needed alongside the YAML changes — the firmware can't
play audio that bridge.py never sends.

### 3.1 The trigger

There's no inbound-audio path on HoldSpeak's `/api/devices/audio`
WebSocket today (it's bridge → HoldSpeak only — the device handshake
sends `hello`, audio is binary frames device-side, and the server
sends control JSON only: `status`, `error`, `hello-ack`). For a
device-side TTS feature, **HoldSpeak's protocol needs an additional
control frame** — e.g. `audio-url` with a URL the device fetches
over HTTP, or `audio-stream` flipping the WS into duplex binary mode.
Pick one and wire it into HoldSpeak first; the bridge changes
follow.

### 3.2 The bridge.py wiring

Once HoldSpeak is sending an `audio-url` frame, in `HoldSpeakLeg._dispatch`:

```python
elif msg_type == "audio-url":
    # Server told us to play <url>. Forward to the firmware via the
    # `prepare_speaker` API service + media_player.play_media.
    asyncio.create_task(self._fire_play_audio(payload["url"]))
```

And in `DeviceLeg`, a method that:

1. Calls the firmware's `prepare_speaker` API service (turns on
   GPIO9, unmutes the ES8311).
2. Sends `media_player.play_media` over the ESPHome API with the URL.
3. After the media_player reports `STATE_IDLE` (or after a fixed
   timeout), calls `restore_mic` (mute ES8311, GPIO9 off).

The original `bridge.py` (pre-AIPI-2 rewrite, in git history) had
this dance — it served a temporary HTTP server hosting the synth'd
WAV with a `?t=timestamp` cache-bust. That's a useful reference if
you're plumbing a similar URL flow.

## 4. Paste-back blocks

The exact YAML that came out of `aipi.yaml` for this revision. Drop
these back in (and undo the comment + `restore_mode: ALWAYS_OFF` /
`internal: true` flip on `speaker_enable` in §2.2).

### 4.1 API services

```yaml
api:
  services:
    # ... keep update_screen + force_toggle_mode ...

    - service: prepare_speaker
      then:
        - switch.turn_on: speaker_enable
        - delay: 50ms
        - lambda: |-
            // Unmute DAC for playback
            uint8_t unmute[] = {0x31, 0x00};
            id(i2c_es8311)->write(0x18, unmute, 2, true);
            ESP_LOGD("custom", "API: ES8311 Unmuted.");

    - service: restore_mic
      then:
        - media_player.stop: speaker_media_player_id
        - delay: 50ms
        - lambda: |-
            // Mute DAC
            uint8_t mute[] = {0x31, 0xFF};
            id(i2c_es8311)->write(0x18, mute, 2, true);
            ESP_LOGD("custom", "API: ES8311 Muted.");
        - delay: 50ms
        # CUT POWER TO THE AMPLIFIER SO IT CANNOT HISS
        - switch.turn_off: speaker_enable
        # In continuous mode, the bridge has just ended a turn and the
        # voice_assistant pipeline is idle. Re-arm it so the mic resumes.
        # Done AFTER the amp is off to keep the EMI workaround intact.
        - if:
            condition:
              lambda: 'return id(continuous_mode);'
            then:
              - delay: 100ms
              - voice_assistant.start:
```

### 4.2 Speaker + media_player

```yaml
speaker:
  - platform: i2s_audio
    id: speaker_id
    i2s_audio_id: i2s_bus
    i2s_dout_pin: GPIO11
    dac_type: external
    mclk_multiple: 256
    sample_rate: 16000
    bits_per_sample: 16bit
    channel: mono
    audio_dac: es8311_dac

media_player:
  - platform: speaker
    name: AiPi Media Player
    id: speaker_media_player_id
    buffer_size: 8192
    volume_min: 0.75
    volume_max: 1.0
    announcement_pipeline:
      speaker: speaker_id
      num_channels: 1
```

### 4.3 `speaker_enable` flip

In the `switch:` section, change the `speaker_enable` block to:

```yaml
- platform: gpio
  pin: GPIO09
  id: speaker_enable
  name: "Speaker Amplifier"
  restore_mode: ALWAYS_ON
```

(Remove `internal: true` + the comment block warning future-you
about EMI; the amp will be cycled by `prepare_speaker` /
`restore_mic` instead.)

### 4.4 on_press: turn off the amp before recording

In `binary_sensor:` `right_button:` `on_press:` `else:` branch,
re-add the `switch.turn_off: speaker_enable` line **before**
`voice_assistant.start:`. Same on `toggle_mode` script's
"switching INTO continuous" branch.

### 4.5 on_boot: turn on the amp

In `esphome:` `on_boot:` priority 800, re-add `switch.turn_on: speaker_enable`
after `switch.turn_on: board_power`. (Or just trust `restore_mode: ALWAYS_ON`
on the switch.)

---

## 5. Testing checklist for the recovered build

When you put this back, test in this order so you can bisect:

1. **Mic still works after speaker re-add.** Bridge-side
   `audio.bytes_forwarded` events should be unchanged after a
   button press. If they're missing, octal PSRAM is wrong or the I2S
   bus isn't shared correctly.
2. **Plain media_player playback works.** From HA or curl, hit
   `prepare_speaker` then `media_player.play_media` with a known
   16 kHz mono int16 WAV URL, confirm audio comes out.
3. **Mic captures after playback.** Press the button after a play.
   If white noise, GPIO9 isn't going low correctly. If silence,
   ES8311 isn't being muted (the I2S clocks are wedging the mic).
4. **Continuous mode survives a play→listen cycle.** This is the
   `restore_mic` path; `voice_assistant.on_end` re-arm should fire
   100 ms after the amp goes off.

Anything fails: revert and read §2 again. The chip's quirks are
load-bearing.

---

## 6. Source canon

- `aipi.yaml` git log around the removal commit — the diff is the
  authoritative paste-back source.
- Robert Lipe's deep-dive on the ES8311 / I2S / I2C interfacing on
  this board: https://www.robertlipe.com/449-2/
- sticks918's foundational ESPHome config:
  https://github.com/sticks918/AIPI-Lite-ESPHome
- ESPHome's `media_player:` docs (announcement_pipeline semantics).
- ESPHome's `audio_dac:` `es8311` component source for register
  numbers (REG14, REG31).
