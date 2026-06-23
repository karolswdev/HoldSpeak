import warnings; warnings.filterwarnings("ignore")
import numpy as np, torch, librosa, coremltools as ct
from resemblyzer import VoiceEncoder
from resemblyzer.audio import wav_to_mel_spectrogram

ve = VoiceEncoder("cpu"); ve.eval()
PART = 25440   # samples -> 160 mel frames (resemblyzer's partial unit)

class AudioToEmbedding(torch.nn.Module):
    def __init__(self, enc, basis):
        super().__init__()
        self.enc = enc
        self.register_buffer("mb", torch.from_numpy(basis).float())
        self.register_buffer("win", torch.hann_window(400))
    def forward(self, wav):                       # wav: (1, PART)
        spec = torch.stft(wav, n_fft=400, hop_length=160, win_length=400,
                          window=self.win, center=True, pad_mode="constant", return_complex=True)
        power = spec.abs()**2                      # (1, 201, frames)
        mel = torch.matmul(self.mb, power)         # (1, 40, frames)
        mel = mel.transpose(1, 2)                  # (1, frames, 40)
        return self.enc(mel)                       # (1, 256)

basis = librosa.filters.mel(sr=16000, n_fft=400, n_mels=40)
m = AudioToEmbedding(ve, basis).eval()

wav = (0.4*np.sin(2*np.pi*np.linspace(0,1.59,PART)*220) + 0.05*np.random.randn(PART)).astype(np.float32)
wt = torch.from_numpy(wav).unsqueeze(0)
with torch.no_grad(): pt = m(wt).numpy().reshape(-1)
ref = ve(torch.from_numpy(wav_to_mel_spectrogram(wav)).unsqueeze(0)).detach().numpy().reshape(-1)
print("[torch e2e vs resemblyzer-encoder] cosine =", round(float(np.dot(pt,ref)/(np.linalg.norm(pt)*np.linalg.norm(ref))),5))

traced = torch.jit.trace(m, wt)
try:
    ml = ct.convert(traced, inputs=[ct.TensorType(name="audio", shape=(1, PART), dtype=np.float32)],
                    minimum_deployment_target=ct.target.iOS17, convert_to="mlprogram")
    out = ml.get_spec().description.output[0].name
    cm = np.array(ml.predict({"audio": wav.reshape(1,-1)})[out]).reshape(-1)
    cos = float(np.dot(ref,cm)/(np.linalg.norm(ref)*np.linalg.norm(cm)))
    print("[CORE ML e2e converts ✓] audio->embedding cosine vs resemblyzer =", round(cos,5))
    ml.save("/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/3c60528f-7203-452e-8bdc-baa806256a04/scratchpad/diar/AudioEmbed.mlpackage")
    print("[saved] AudioEmbed.mlpackage")
except Exception as e:
    print("[CORE ML stft conversion FAILED] ->", repr(e)[:300])
    print("[fallback] compute mel in Swift (Accelerate FFT), feed mel(1,frames,40) to the already-working VoiceEncoder.mlpackage")
