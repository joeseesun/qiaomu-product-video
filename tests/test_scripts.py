"""End-to-end tests for qiaomu-product-video scripts (needs ffmpeg/ffprobe)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "scripts"
HAS_FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")


def py(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


class ScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        (self.repo / "src").mkdir(parents=True)
        (self.repo / "src" / "panel.tsx").write_text("export const Panel = () => null;\n")
        self.proj = self.tmp / "films" / "demo"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def init(self):
        r = py(S / "init_project.py", "--output", self.proj, "--repo", self.repo, "--duration", "6")
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads((self.proj / "plan.json").read_text())

    def test_init_requires_repo_for_repo_style(self):
        r = py(S / "init_project.py", "--output", self.proj)
        self.assertEqual(r.returncode, 2)

    def test_init_does_not_overwrite(self):
        self.init()
        (self.proj / "BRIEF.md").write_text("mine")
        py(S / "init_project.py", "--output", self.proj, "--repo", self.repo)
        self.assertEqual((self.proj / "BRIEF.md").read_text(), "mine")

    def test_skeleton_fails_final(self):
        self.init()
        r = py(S / "check_plan.py", self.proj / "plan.json", "--final", "--tier", "premium")
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout)
        self.assertTrue(any("scope" in e for e in out["errors"]))
        self.assertTrue(any("DIRECTION" in e for e in out["errors"]))

    def good_plan(self, plan, cue_at):
        plan.update({
            "demo": False, "duration": 6,
            "scope": {"versions": "v1.0..v1.1", "platforms": ["web"]},
            "typography": {"fontEn": "Inter", "fontZh": "Noto Sans SC", "exceptionReason": ""},
            "strategy": {"goal": "adoption", "audience": "前端开发者", "singleMessage": "不用切窗口，检查结果就在侧边",
                         "ahaMoment": "点一下，结果出现在侧边", "cta": "升级到 v1.1", "format": "linear"},
            "deliverables": [{"id": "hero", "aspect": "16:9", "duration": 6, "sound": "on"},
                             {"id": "loop", "aspect": "16:9", "duration": 4, "sound": "none", "loop": True,
                              "from": "hero", "shots": ["panel"]}],
        })
        plan["audio"]["music"]["file"] = "assets/music.wav"
        plan["shots"] = [
            {"id": "open", "start": 0, "end": 2, "type": "title", "role": ["hook", "brand"], "headline": "新版本", "actions": []},
            {"id": "panel", "start": 2, "end": 6, "type": "feature", "role": ["aha", "cta"], "headlineEn": "Side panel",
             "headline": "侧边面板", "plainExplanation": "以前要切窗口，现在在侧边直接查看结果。",
             "description": "在侧边面板里直接查看检查结果。", "claim": True, "source": "repo:src/panel.tsx#L1",
             "actions": [{"id": "open-panel", "at": 0.5, "action": "点击打开", "soundRequired": True}]},
        ]
        plan["audio"]["cues"] = [{"at": cue_at, "actionId": "open-panel", "file": "assets/sfx/click.wav",
                                  "gain": 0.8, "role": "click", "syncOffset": 0.01}]
        (self.proj / "plan.json").write_text(json.dumps(plan, ensure_ascii=False))
        d = (self.proj / "DIRECTION.md").read_text()
        d = d.replace("选定：\n理由：\n", "选定：A\n理由：暗色产品\n")
        d = d.replace("因为产品有 ______，所以用 ______。", "因为产品有侧边面板，所以用推近接续。")
        d += "| open | 0-2 | 标题 | 逐字 | 新版本 | 无 |\n| panel | 2-6 | 面板 | 点击 | 侧边面板 | click |\n"
        (self.proj / "DIRECTION.md").write_text(d)
        self.write_scorecard(4)

    def write_scorecard(self, score, passed=True):
        box = "[x]" if passed else "[ ]"
        dims = "".join(f"| d{i} | {score} | t=1s |\n" for i in range(11))
        gates = "".join(f"- {box} G{i} ok\n" for i in range(1, 10))
        (self.proj / "evidence" / "scorecard.md").write_text(
            f"# Scorecard\n\n评审人：无上下文子代理　观看文件：renders/hero.mp4\n\n## 必过项\n{gates}\n"
            f"## 评分\n| 维度 | 分 | 证据 |\n|---|---|---|\n{dims}")

    @unittest.skipUnless(HAS_FFMPEG, "ffmpeg required")
    def test_full_pipeline(self):
        plan = self.init()
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=f=220:d=6",
                        str(self.proj / "assets" / "music.wav")], check=True)
        click = self.proj / "assets" / "sfx" / "click.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
                        "-f", "lavfi", "-i", "sine=f=2000:d=0.05", "-filter_complex",
                        "[0]atrim=0:0.01[a];[a][1]concat=n=2:v=0:a=1", str(click)], check=True)
        lm = json.loads(py(S / "sfx_landmarks.py", click).stdout)[0]
        self.assertAlmostEqual(lm["onset"], 0.01, delta=0.003)
        self.assertLess(lm["peakDbfs"], 0)

        self.good_plan(plan, cue_at=2.49)
        r = py(S / "check_plan.py", self.proj / "plan.json", "--final", "--tier", "premium")
        self.assertEqual(r.returncode, 0, r.stdout)

        self.write_scorecard(3)
        r = py(S / "check_plan.py", self.proj / "plan.json", "--final", "--tier", "premium")
        self.assertEqual(r.returncode, 1)
        self.assertIn("premium bar", r.stdout)
        self.write_scorecard(5, passed=False)
        r = py(S / "check_plan.py", self.proj / "plan.json", "--final", "--tier", "premium")
        self.assertIn("must-pass", r.stdout)

        self.good_plan(plan, cue_at=2.8)
        r = py(S / "check_plan.py", self.proj / "plan.json", "--final", "--tier", "premium")
        self.assertEqual(r.returncode, 1)
        self.assertIn("frames from its action", r.stdout)

        video = self.tmp / "final.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=640x360:d=6:r=30",
                        "-i", str(self.proj / "assets" / "music.wav"), "-shortest", "-pix_fmt", "yuv420p",
                        str(video)], check=True)
        out = self.proj / "evidence" / "review"
        r = py(S / "review_sheets.py", video, "--plan", self.proj / "plan.json", "--out", out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rep = json.loads(r.stdout)
        self.assertEqual(len(rep["contactSheets"]), 2)
        self.assertEqual(len(rep["transitionStrips"]), 1)
        self.assertTrue(Path(rep["audio"]["spectrum"]).exists())
        self.assertTrue(rep["audio"]["rmsDbPerSecond"])
        self.assertTrue(Path(rep["hookStrip"]).exists())
        self.assertEqual(len(rep["thumbnailTests"]), 3)  # first frame + brand shot + aha shot

    @unittest.skipUnless(HAS_FFMPEG, "ffmpeg required")
    def test_loop_seam(self):
        still = self.tmp / "still.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=320x180:d=2:r=30",
                        str(still)], check=True)
        r = py(S / "review_sheets.py", still, "--loop", "--out", self.tmp / "rv")
        self.assertTrue(json.loads(r.stdout)["loop"]["seamless"])

    def test_missing_strategy_and_roles_flagged(self):
        self.init()
        out = json.loads(py(S / "check_plan.py", self.proj / "plan.json", "--final", "--tier", "premium").stdout)
        joined = " ".join(out["errors"])
        for needle in ("strategy.singleMessage", "role 'aha'", "role 'brand'", "scorecard"):
            self.assertIn(needle, joined)


if __name__ == "__main__":
    unittest.main()
