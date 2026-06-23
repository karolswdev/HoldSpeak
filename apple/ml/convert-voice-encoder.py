import torch, numpy as np, warnings
warnings.filterwarnings("ignore")
from resemblyzer import VoiceEncoder
import coremltools as ct

ve = VoiceEncoder("cpu"); ve.eval()

# resemblyzer embeds 160-frame partials (40 mels each) then averages. Convert that unit.
example = torch.randn(1, 160, 40)
traced = torch.jit.trace(ve, example)
print("[trace] ok")

mlmodel = ct.convert(
    traced,
    inputs=[ct.TensorType(name="mels", shape=(1, 160, 40), dtype=np.float32)],
    minimum_deployment_target=ct.target.iOS16,
    compute_units=ct.ComputeUnit.ALL,
    convert_to="mlprogram",
)
out_dir = "/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/3c60528f-7203-452e-8bdc-baa806256a04/scratchpad/diar/VoiceEncoder.mlpackage"
mlmodel.save(out_dir)
print("[convert] saved ->", out_dir)
spec = mlmodel.get_spec()
out_name = spec.description.output[0].name
print("[io] input=mels(1,160,40) output=", out_name)

# Validate: PyTorch vs CoreML embeddings on random + structured inputs.
cosines = []
for i in range(5):
    mel = torch.randn(1, 160, 40)
    with torch.no_grad(): pt = ve(mel).numpy().reshape(-1)
    cm = np.array(mlmodel.predict({"mels": mel.numpy().astype(np.float32)})[out_name]).reshape(-1)
    cos = float(np.dot(pt, cm)/(np.linalg.norm(pt)*np.linalg.norm(cm)))
    cosines.append(cos)
print("[validate] PyTorch vs CoreML cosine per run:", [round(c,5) for c in cosines])
print("[validate] min cosine:", round(min(cosines),5), "(pass = ~1.0)")
import os
sz = sum(os.path.getsize(os.path.join(r,f)) for r,_,fs in os.walk(out_dir) for f in fs)
print(f"[size] model = {sz/1e6:.1f} MB")
