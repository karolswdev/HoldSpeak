# PHILO-5-04 real brief producer fixtures

These files are complete JSON response objects copied from retained real
producer observations. `latest-run4.json` is the GET `/api/brief/latest`
answer. `generate-run5.json` is the later real brief read back after Codex generated it.
The test serves that exact producer object as the POST answer. Their section counts and `generated_at` values are different so the
rendered Generate transition cannot pass with a stale receipt. `empty-s3.json`
is a retained real empty response for the zero-count receipt fence.

- `latest-run4.json`: `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/receipt-red/brief-read.json`, extracted at `response`; source SHA256: `f5cfe0b7aceb35084b3674b088dbdffa650d867f2a0a9d9f2c0515867e1e62c8`; fixture SHA256: `792310ade8a7852343b9ebce6ceaadfe372fd72ba3c20ab9ae5747c634496ea7`; 5 items at `2026-09-25T18:08:10.043146`.
- `generate-s4.json`: `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/carried/s4-1440/20260924T233409Z-case.closure.chain.s4_saved_content-astra-1440/observation.json`, extracted at `setup/26/response`; source SHA256: `1053077f8d6565fc055146bbbdd726a731a4f5ad54aec2dd2717500beeab1328`; fixture SHA256: `6adf188aa9035930d59323146dc96b89324e3f4fc4ea6a23bb3ab38f4f4d473d`; 4 items at `2026-09-24T17:35:04.179773`.
- `empty-s3.json`: `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T224233Z-case.j10.route_generate_again.same_day_same_id-astra-1440/observation.json`, extracted at `trigger/response`; source SHA256: `f30917a955b7c1ba4e67b876d8bbafa9d1ad0c1d76164d85b32d2ef34a463df2`; fixture SHA256: `e54e9d863c8e8c3c02da5bcce12cfd52a369d2992aaffb26fa3ac4f62b05bab5`; zero items at `2026-09-24T16:42:39.649297`.

- `generate-run5.json`: `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/observations/brief.json`, extracted at `brief_read/response`; source SHA256: `5399183aecc9cdfc24de075fce2d10549ee6b352a9c24ce641568763d438fee9`; fixture SHA256: `007a24004c1e5a65b82e7de64994f55e65d2e621cb187b129f614dcf995b3473`; 6 items at `2026-09-25T18:19:14.790734`. This replaces the older S4 object in the final transition test; `generate-s4.json` remains the original pre-fix fixture for the retained red test run.
