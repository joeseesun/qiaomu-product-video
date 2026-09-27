"""Tests for the self-contained audio / plan tools (need ffmpeg)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

S = Path(__file__).resolve().parents[1] / "scripts"
HAS_FFMPEG = bool(shutil.which("ffmpeg"))


def py(*a):
    return subprocess.run([sys.executable, *map(str, a)], capture_output=True, text=True)


PLAN = {
    "title": "t", "duration": 8, "format": {"width": 1920, "height": 1080, "fps": 30},
    "shots": [
        {"id": "a", "start": 0, "end": 3, "type": "feature", "role": ["hook", "brand", "aha"], "headline": "读到一句好话",
         "actions": [{"id": "click", "at": 1.0, "soundRequired": True}]},
        {"id": "b", "start": 3, "end": 5, "type": "brand", "headline": "乔木"},
        {"id": "c", "start": 5, "end": 8, "type": "end", "role": ["cta"], "headline": "读到好的，直接进笔记。"},
    ],
    "deliverables": [{"id": "hero", "aspect": "16:9", "duration": 8, "sound": "on"},
                     {"id": "short", "aspect": "9:16", "duration": 6, "sound": "on", "from": "hero", "shots": ["a", "c"], "layout": "stacked"}],
    "audio": {"music": {"file": "assets/music.wav", "gain": 0.5}, "beatGrid": {"bpm": 96, "offset": 0},
              "cues": [{"at": 1.0, "file": "assets/sfx/click.wav", "gain": 0.6, "role": "click", "syncOffset": 0.0, "actionId": "click"},
                       {"at": 3.9, "file": "assets/sfx/pop.wav", "gain": 0.5, "role": "popup", "syncOffset": 0.0}]},
}


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg required")
class AudioTools(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        (self.d / "plan.json").write_text(json.dumps(PLAN, ensure_ascii=False))

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_pipeline(self):
        r = py(S / "score.py", self.d / "plan.json", "--mood", "warm", "--out", "assets/music.wav")
        self.assertEqual(r.returncode, 0, r.stderr)
        info = json.loads(r.stdout)
        self.assertEqual([s["level"] for s in info["sections"]], [1, 1, "end"])
        self.assertTrue((self.d / "assets/music.wav").exists())
        r = py(S / "make_sfx.py", "--out", self.d / "assets/sfx", "--only", "click,pop")
        self.assertEqual(r.returncode, 0, r.stderr)
        lm = json.loads(py(S / "sfx_landmarks.py", self.d / "assets/sfx/click.wav").stdout)[0]
        self.assertAlmostEqual(lm["peakDbfs"], -3.0, delta=0.3)
        r = py(S / "mix_audio.py", self.d / "plan.json")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads((self.d / "evidence/audio-mix.json").read_text())
        self.assertEqual(rep["cues"][0]["alignmentFrames"], 0.0)
        self.assertIn("marginDb", rep["cues"][0])
        self.assertAlmostEqual(float(rep["loudness"]["output_i"]), -16, delta=1.0)
        # derived deliverable: shots a + c back to back, cue of dropped shot b removed
        r = py(S / "derive_plan.py", self.d / "plan.json", "--deliverable", "short")
        self.assertEqual(r.returncode, 0, r.stderr)
        dp = json.loads((self.d / "plan.short.json").read_text())
        self.assertEqual(dp["duration"], 6)
        self.assertEqual([(s["id"], s["start"]) for s in dp["shots"]], [("a", 0), ("c", 3)])
        self.assertEqual(len(dp["audio"]["cues"]), 1)
        self.assertEqual(dp["audio"]["music"]["file"], "assets/music-short.wav")

    def test_record_terminal(self):
        out = self.d / "demo.cast"
        r = py(S / "record_terminal.py", "--out", out, "--type", "echo hi", "--", "echo", "hi")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = out.read_text().splitlines()
        self.assertEqual(json.loads(lines[0])["version"], 2)
        text = "".join(json.loads(l)[2] for l in lines[1:])
        self.assertIn("echo hi", text)
        self.assertIn("hi\r\n", text)


class CheckPlanTiers(unittest.TestCase):
    def test_override_downgrades_default_rule_only(self):
        d = Path(tempfile.mkdtemp())
        plan = json.loads(json.dumps(PLAN))
        plan["shots"][0]["headline"] = "这是一句远远超过十五个中文字的开场白用来测试"
        plan["shots"][0]["claim"] = True  # no source: invariant, must stay an error
        plan["overrides"] = [{"rule": "hook copy", "reason": "悬念式开场"}, {"rule": "claim without source", "reason": "try"}]
        (d / "plan.json").write_text(json.dumps(plan, ensure_ascii=False))
        out = json.loads(py(S / "check_plan.py", d / "plan.json").stdout)
        self.assertTrue(any("hook copy" in n for n in out["notes"]))
        self.assertTrue(any("claim without source" in e for e in out["errors"]))
        shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
