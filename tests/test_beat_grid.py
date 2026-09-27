"""beat_grid.py and the starter spring kit (needs ffmpeg; node optional)."""
import json
import math
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAS_FFMPEG = shutil.which("ffmpeg")


def synth(path, bpm=128.0, offset=0.37, dur=40.0, drop_bar=10, sr=22050):
    beat = 60 / bpm
    n = int(sr * dur)
    buf = [0.0] * n
    rnd = random.Random(1)
    t, i = offset, 0
    while t < dur - 0.3:
        amp = 0.9 if i % 4 == 0 else 0.45
        s = int(t * sr)
        for j in range(int(0.12 * sr)):
            buf[s + j] += amp * math.exp(-j / sr * 30) * math.sin(2 * math.pi * (55 + 60 * math.exp(-j / sr * 40)) * j / sr)
        h = int((t + beat / 2) * sr)
        for j in range(int(0.03 * sr)):
            if h + j < n:
                buf[h + j] += 0.1 * rnd.uniform(-1, 1) * math.exp(-j / sr * 120)
        t += beat
        i += 1
    drop = offset + drop_bar * 4 * beat
    for k in range(n):
        tt = k / sr
        buf[k] += (0.05 if tt < drop else 0.3) * math.sin(2 * math.pi * 220 * tt)
    m = max(abs(x) for x in buf)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(x / m * 30000)) for x in buf))
    return drop


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg required")
class BeatGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.wav = cls.tmp / "song.wav"
        cls.drop = synth(cls.wav)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_tempo_downbeat_drop_and_plan_write(self):
        plan = {"format": {"fps": 30}, "audio": {}, "shots": [{"id": "a", "start": 0.0}, {"id": "b", "start": 2.25}]}
        pp = self.tmp / "plan.json"
        pp.write_text(json.dumps(plan))
        r = subprocess.run([sys.executable, ROOT / "scripts/beat_grid.py", self.wav, "--plan", pp, "--write"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertAlmostEqual(out["bpm"], 128.0, delta=0.6)
        beat = 60 / 128
        # first downbeat = 0.37 (or a whole bar later), within 25 ms
        phase = (out["offset"] - 0.37) % (4 * beat)
        self.assertLess(min(phase, 4 * beat - phase), 0.025, out)
        self.assertLess(abs(out["drop"]["time"] - self.drop), 0.05, out["drop"])
        saved = json.loads(pp.read_text())
        self.assertTrue(saved["audio"]["beatGrid"]["measured"])
        self.assertEqual(len(out["shots"]), 2)

    def test_undecodable_file_fails_cleanly(self):
        bad = self.tmp / "bad.mp3"
        bad.write_text("not audio")
        r = subprocess.run([sys.executable, ROOT / "scripts/beat_grid.py", bad], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cannot decode", r.stderr)


@unittest.skipUnless(shutil.which("node"), "node required")
class SpringKitTests(unittest.TestCase):
    def test_spring_is_pure_and_settles(self):
        js = (ROOT / "assets/starter/src/kit/spring.js").as_uri()
        code = f"""import('{js}').then(m => {{
          const a = m.springTrack([{{v:0}},{{t:0,v:100}},{{t:0.1,v:50}}], 0.37);
          const b = m.springTrack([{{v:0}},{{t:0,v:100}},{{t:0.1,v:50}}], 0.37);
          const s = m.stretchySpan([{{left:0,right:10}},{{t:0,left:50,right:60}}], 0.05);
          console.log(JSON.stringify({{zero: m.springStep(0), rest: m.springTrack([{{v:0}},{{t:0,v:100}},{{t:0.1,v:50}}], 3), same: a===b, lead: s.right - 10 > s.left, over: m.springStep(0.4, m.SPRINGS.lively) > 1}}));
        }})"""
        r = subprocess.run(["node", "-e", code], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        o = json.loads(r.stdout)
        self.assertEqual(o["zero"], 0)
        self.assertAlmostEqual(o["rest"], 50, delta=0.01)
        self.assertTrue(o["same"] and o["lead"] and o["over"])


if __name__ == "__main__":
    unittest.main()
