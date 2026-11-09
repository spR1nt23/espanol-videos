import sys, sherpa_onnx, soundfile as sf, numpy as np
M = "/home/claude/models"

_cache = {}
def voice(name):
    if name not in _cache:
        from piper import PiperVoice
        d = f"{M}/vits-piper-{name}"
        _cache[name] = PiperVoice.load(f"{d}/{name}.onnx", config_path=f"{d}/{name}.onnx.json")
    return _cache[name]

def say(name, text, out, speed=1.0):
    from piper import SynthesisConfig
    v = voice(name)
    chunks = list(v.synthesize(text, syn_config=SynthesisConfig(length_scale=1.0/speed)))
    s = np.concatenate([c.audio_float_array for c in chunks]).astype(np.float32)
    sr = chunks[0].sample_rate
    sf.write(out, s, sr)
    return len(s) / sr

_rec = None
def transcribe(path, lang):
    global _rec
    if _rec is None:
        w = f"{M}/sherpa-onnx-whisper-small"
        _rec = {}
    if lang not in _rec:
        w = f"{M}/sherpa-onnx-whisper-small"
        _rec[lang] = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=f"{w}/small-encoder.int8.onnx", decoder=f"{w}/small-decoder.int8.onnx",
            tokens=f"{w}/small-tokens.txt", language=lang, task="transcribe", num_threads=4)
    r = _rec[lang]
    d, sr = sf.read(path, dtype="float32")
    if sr != 16000:
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ar", "16000", "-ac", "1", "/tmp/_16k.wav"], check=True)
        d, sr = sf.read("/tmp/_16k.wav", dtype="float32")
    st = r.create_stream(); st.accept_waveform(sr, d); r.decode_stream(st)
    return st.result.text.strip()
