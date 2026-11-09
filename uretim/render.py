import os, sys, json, math, subprocess, colorsys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from tts import say

W, H, FPS, SR = 1080, 1920, 30, 44100
A = "/home/claude/assets"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
TR_V, ES_V = "tr_TR-fahrettin-medium", "es_MX-claude-high"

def font(name, size):
    if name == "inter":
        f = ImageFont.truetype(f"{A}/Inter.ttf", size)
        try: f.set_variation_by_axes([min(32, max(14, size)), 600])
        except Exception: pass
        return f
    return ImageFont.truetype(f"{A}/Poppins-{name}.ttf", size)

_em = {}
def emoji(ch, size):
    k = (ch, size)
    if k not in _em:
        f = ImageFont.truetype(EMOJI_FONT, 109)
        im = Image.new("RGBA", (160, 160)); ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox()); r = size / max(im.size)
        _em[k] = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    return _em[k]

def text_layer(lines, fnt, fill, stroke=0, stroke_fill=(0, 0, 0), spacing=14, maxw=960):
    # wrap
    out = []
    for ln in lines:
        words, cur = ln.split(" "), ""
        for w_ in words:
            t = (cur + " " + w_).strip()
            if fnt.getlength(t) > maxw and cur: out.append(cur); cur = w_
            else: cur = t
        out.append(cur)
    asc, desc = fnt.getmetrics(); lh = asc + desc
    wmax = int(max(fnt.getlength(l) for l in out)) + 2 * stroke + 8
    im = Image.new("RGBA", (wmax, lh * len(out) + spacing * (len(out) - 1) + 2 * stroke + 8))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(out):
        x = (wmax - fnt.getlength(l)) / 2
        d.text((x, stroke + 4 + i * (lh + spacing)), l, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im

def pill(w, h, fill, r=None):
    im = Image.new("RGBA", (w, h)); ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r or h // 2, fill=fill)
    return im

def ease(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3

def paste(frame, im, cx, y, alpha=1.0, scale=1.0):
    if alpha <= 0.01: return
    if abs(scale - 1) > 0.01:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 0.99:
        im = im.copy(); a = im.getchannel("A").point(lambda v: int(v * alpha)); im.putalpha(a)
    frame.alpha_composite(im, (int(cx - im.width / 2), int(y - im.height / 2)))

# ---------- background ----------
def make_bokeh(seed, hue):
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (W, H * 2)); d = ImageDraw.Draw(im)
    for _ in range(26):
        r = int(rng.uniform(40, 170)); x = rng.uniform(0, W); y = rng.uniform(0, 2 * H)
        c = colorsys.hsv_to_rgb((hue + rng.uniform(-0.08, 0.08)) % 1, 0.45, 1)
        d.ellipse((x - r, y - r, x + r, y + r), fill=tuple(int(v * 255) for v in c) + (int(rng.uniform(25, 60)),))
    im = im.filter(ImageFilter.GaussianBlur(18))
    return Image.alpha_composite(im, Image.new("RGBA", im.size)), im

def background(t, hue, bokeh):
    yy = np.linspace(0, 1, H)[:, None]
    h1 = (hue + 0.03 * math.sin(t * 0.6)) % 1; h2 = (hue + 0.12 + 0.03 * math.cos(t * 0.5)) % 1
    c1 = np.array(colorsys.hsv_to_rgb(h1, 0.85, 0.32)); c2 = np.array(colorsys.hsv_to_rgb(h2, 0.9, 0.12))
    k = (yy + 0.08 * math.sin(t * 0.8)).clip(0, 1)
    g = (c1 * (1 - k) + c2 * k) * 255
    arr = np.repeat(g[:, None, :], W, axis=1).reshape(H, W, 3).astype(np.uint8)
    fr = Image.fromarray(arr, "RGB").convert("RGBA")
    off = int((t * 45) % H)
    fr.alpha_composite(bokeh.crop((0, H - off, W, 2 * H - off)))
    return fr

# ---------- audio ----------
def load(path):
    tmp = "/tmp/_rs.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ar", str(SR), "-ac", "1", tmp], check=True)
    d, _ = sf.read(tmp, dtype="float32"); return d

def tick():
    n = int(0.06 * SR); t = np.arange(n) / SR
    return (0.6 * np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 90) + 0.25 * np.random.default_rng(1).normal(size=n) * np.exp(-t * 200)).astype(np.float32)

def bell():
    n = int(1.4 * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for f, a, dcy in [(1318.5, 0.5, 3.5), (2637, 0.25, 5), (1975.5, 0.2, 4.5), (3951, 0.08, 8)]:
        s += a * np.sin(2 * np.pi * f * t) * np.exp(-t * dcy)
    return (s * 0.7).astype(np.float32)

def whoosh():
    n = int(0.35 * SR); t = np.arange(n) / SR
    noise = np.random.default_rng(2).normal(size=n)
    env = np.sin(np.pi * t / t[-1]) ** 2
    lp = np.convolve(noise, np.ones(30) / 30, mode="same")
    return (lp * env * 0.5).astype(np.float32)

# ---------- main ----------
def render(item, outdir):
    slug = item["slug"]; wd = f"/home/claude/work/{slug}"; os.makedirs(wd, exist_ok=True)
    tr, es, ok, emj, hue = item["tr"], item["es"], item["okunus"], item["emoji"], item["hue"]
    es_say = item.get("es_say", es)
    clips = {}
    clips["q"] = say(TR_V, f"{tr}. İspanyolca nasıl denir, biliyor musun?", f"{wd}/q.wav")
    clips["a"] = say(ES_V, es_say, f"{wd}/a.wav")
    clips["slow"] = say(ES_V, es_say, f"{wd}/slow.wav", speed=0.68)
    clips["sira"] = say(TR_V, "Sıra sende! Yüksek sesle tekrar et.", f"{wd}/sira.wav")
    clips["yorum"] = say(TR_V, "Bildiysen yorumlara yaz!", f"{wd}/yorum.wav")
    # timeline
    T = {}
    T["q"] = 0.15; q_end = T["q"] + clips["q"]
    T["cd"] = q_end + 0.15
    T["ans"] = T["cd"] + 3.0
    T["a"] = T["ans"] + 0.25
    T["slow"] = T["a"] + clips["a"] + 0.55
    T["sira"] = T["slow"] + clips["slow"] + 0.45
    T["rep"] = T["sira"] + clips["sira"] + 0.1  # user repeats
    T["yorum"] = T["rep"] + 1.9
    dur = T["yorum"] + clips["yorum"] + 1.1
    # audio mix
    N = int(dur * SR) + SR; mix = np.zeros(N, np.float32)
    def put(sig, at, g=1.0):
        i = int(at * SR); mix[i:i + len(sig)] += sig[: N - i] * g
    for k in ["q", "a", "slow", "sira", "yorum"]: put(load(f"{wd}/{k}.wav"), T[k], 1.0)
    for i in range(3): put(tick(), T["cd"] + i, 0.45)
    put(bell(), T["ans"], 0.35); put(whoosh(), T["sira"] - 0.25, 0.25); put(whoosh(), T["yorum"] - 0.25, 0.25)
    mix = mix[: int(dur * SR)]
    mix /= max(1e-6, np.abs(mix).max()) / 0.9
    sf.write(f"{wd}/mix.wav", mix, SR)

    # layers
    L = {}
    L["brand"] = text_layer(["İSPANYOLCA • GÜNÜN CÜMLESİ"], font("SemiBold", 38), (255, 255, 255, 215))
    L["flag"] = emoji("🇪🇸", 58)
    L["emoji"] = emoji(emj, 270)
    L["tr_big"] = text_layer([f"“{tr}”"], font("ExtraBold", 104), (255, 255, 255), stroke=5, stroke_fill=(0, 0, 0, 120), maxw=960)
    L["tr_small"] = text_layer([f"“{tr}”"], font("Bold", 64), (255, 255, 255, 235), maxw=960)
    L["nasil"] = text_layer(["İspanyolca nasıl denir?"], font("Bold", 66), (255, 214, 102))
    L["biliyor"] = text_layer(["Biliyor musun?"], font("SemiBold", 58), (255, 255, 255))
    L["think"] = emoji("🤔", 70)
    L["dusun"] = text_layer(["Düşün…"], font("SemiBold", 56), (255, 255, 255, 220))
    L["nums"] = {n: text_layer([str(n)], font("ExtraBold", 300), (255, 255, 255)) for n in (3, 2, 1)}
    L["es"] = text_layer([es], font("ExtraBold", 112), (255, 214, 102), stroke=6, stroke_fill=(40, 20, 0, 160), maxw=860)
    L["ok"] = text_layer([f"({ok})"], font("SemiBold", 58), (255, 255, 255, 235), maxw=980)
    L["card"] = pill(1000, L["es"].height + L["ok"].height + 120, (0, 0, 0, 95), r=48)
    L["normal"] = text_layer(["🔊"], font("Bold", 10), (0, 0, 0, 0))
    L["lab_n"] = text_layer(["Normal hız"], font("Bold", 46), (255, 255, 255))
    L["lab_s"] = text_layer(["Yavaş"], font("Bold", 46), (255, 255, 255))
    L["e_spk"] = emoji("🔊", 52); L["e_turtle"] = emoji("🐢", 56)
    L["sira"] = text_layer(["Sıra sende!"], font("ExtraBold", 110), (255, 255, 255), stroke=5, stroke_fill=(0, 0, 0, 120))
    L["e_mic"] = emoji("🎤", 120)
    L["tekrar"] = text_layer(["Yüksek sesle tekrar et"], font("SemiBold", 52), (255, 255, 255, 230))
    L["yorum"] = text_layer(["Bildiysen", "yorumlara yaz!"], font("ExtraBold", 92), (255, 255, 255), stroke=4, stroke_fill=(0, 0, 0, 120), maxw=960)
    L["e_down"] = emoji("👇", 120)
    L["takip"] = text_layer(["Her gün yeni bir cümle için takip et"], font("SemiBold", 48), (255, 214, 102), maxw=940)
    _, bokeh = make_bokeh(abs(hash(slug)) % 1000, hue)

    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-i", f"{wd}/mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                             "-movflags", "+faststart", "-shortest", f"{outdir}/{slug}.mp4"], stdin=subprocess.PIPE)
    nf = int(dur * FPS)
    for fi in range(nf):
        t = fi / FPS
        fr = background(t, hue, bokeh)
        # brand
        bw = L["brand"].width + 130
        paste(fr, pill(bw, 84, (0, 0, 0, 90)), W / 2, 150)
        paste(fr, L["flag"], W / 2 - bw / 2 + 60, 150); paste(fr, L["brand"], W / 2 + 32, 150)
        cd, ans = T["cd"], T["ans"]
        if t < cd:  # question
            e = ease((t - 0.0) / 0.35)
            bob = 12 * math.sin(t * 3)
            paste(fr, L["emoji"], W / 2, 520 + bob, e, 0.6 + 0.4 * e)
            paste(fr, L["tr_big"], W / 2, 880 + 60 * (1 - e), e)
            e2 = ease((t - 0.9) / 0.35); paste(fr, L["nasil"], W / 2, 1110 + 40 * (1 - e2), e2)
            e3 = ease((t - (T["q"] + clips["q"] * 0.62)) / 0.3)
            paste(fr, L["biliyor"], W / 2 - 40, 1240, e3); paste(fr, L["think"], W / 2 + L["biliyor"].width / 2 + 10, 1238, e3, 0.6 + 0.4 * e3)
        else:
            paste(fr, L["tr_small"], W / 2, 330)
            paste(fr, L["nasil"], W / 2, 330 + L["tr_small"].height / 2 + 50, 1, 0.75)
        if cd <= t < ans:  # countdown
            k = int(t - cd); n = 3 - k; ph = (t - cd) - k
            cx, cy, R = W / 2, 960, 230
            ov = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(ov)
            d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(0, 0, 0, 80), outline=(255, 255, 255, 60), width=18)
            d.arc((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * (1 - ((t - cd) / 3)), fill=(255, 214, 102), width=18)
            fr.alpha_composite(ov)
            sc = 1.35 - 0.35 * ease(ph / 0.25)
            paste(fr, L["nums"][n], cx, cy - 12, ease(ph / 0.12), sc)
            paste(fr, L["dusun"], W / 2, 1300, 0.6 + 0.4 * math.sin(t * 5) ** 2)
        if t >= ans:  # answer
            e = ease((t - ans) / 0.3)
            cy = 880
            if t >= T["sira"]: cy = 880 - 70 * ease((t - T["sira"]) / 0.4)
            paste(fr, L["card"], W / 2, cy, e, 0.9 + 0.1 * e)
            paste(fr, L["es"], W / 2, cy - L["ok"].height / 2 - 10, e, 0.7 + 0.3 * e)
            paste(fr, L["ok"], W / 2, cy + L["es"].height / 2 + 10, ease((t - ans - 0.25) / 0.3))
            lab_y = cy + L["card"].height / 2 + 70
            if t < T["slow"] - 0.2 and t < T["sira"]:
                a = ease((t - T["a"]) / 0.25)
                paste(fr, L["e_spk"], W / 2 - L["lab_n"].width / 2 - 25, lab_y, a); paste(fr, L["lab_n"], W / 2 + 30, lab_y, a)
            elif t < T["sira"] - 0.1:
                a = ease((t - T["slow"] + 0.2) / 0.25)
                paste(fr, L["e_turtle"], W / 2 - L["lab_s"].width / 2 - 30, lab_y, a); paste(fr, L["lab_s"], W / 2 + 32, lab_y, a)
        if T["sira"] <= t < T["yorum"] - 0.15:
            e = ease((t - T["sira"]) / 0.3)
            pulse = 1 + 0.06 * math.sin((t - T["sira"]) * 8)
            paste(fr, L["e_mic"], W / 2, 1180, e, pulse)
            paste(fr, L["sira"], W / 2, 1340, e, 0.8 + 0.2 * e)
            paste(fr, L["tekrar"], W / 2, 1460, ease((t - T["sira"] - 0.4) / 0.3))
            if t >= T["rep"]:
                p = min(1, (t - T["rep"]) / (T["yorum"] - T["rep"]))
                paste(fr, pill(600, 16, (255, 255, 255, 60)), W / 2, 1540)
                if p > 0.03: fr.alpha_composite(pill(int(600 * p), 16, (255, 214, 102, 255)), (int(W / 2 - 300), 1532))
        if t >= T["yorum"] - 0.15:
            e = ease((t - T["yorum"] + 0.15) / 0.3)
            paste(fr, L["yorum"], W / 2, 1270 + 50 * (1 - e), e)
            paste(fr, L["e_down"], W / 2, 1490 + 14 * math.sin(t * 9), e)
            paste(fr, L["takip"], W / 2, 1640, ease((t - T["yorum"] - 0.4) / 0.3))
        proc.stdin.write(fr.convert("RGB").tobytes())
    proc.stdin.close(); proc.wait()
    return dur, T

if __name__ == "__main__":
    items = json.load(open(sys.argv[1])); outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
    only = sys.argv[3:]
    for it in items:
        if only and it["slug"] not in only: continue
        d, T = render(it, outdir); print(it["slug"], round(d, 2), {k: round(v, 2) for k, v in T.items()}, flush=True)
