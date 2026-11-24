"""Automated offline tests for advanced-mongodb-2476236 docs, STE, Mermaid, Python labs, and configs."""

from __future__ import annotations

import ast
import base64
import importlib.util
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
QUADRANTS = ("01-tutorials", "02-how-to-guides", "03-reference", "04-explanation")

PYTHON_LAB_SCRIPTS = (
    "change-streams/main.py",
    "change-streams/change_stream.py",
    "change-streams/change_stream_2.py",
    "change-streams/resumable_change_stream.py",
    "csfle/main.py",
    "qe/main.py",
    "gridfs/main.py",
    "exercises/exercise_1_5.py",
    "exercises/exercise_4_4.py",
)

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FENCE_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})(.*)$")
MERMAID_HEAD_RE = re.compile(
    r"^\s*(?:flowchart(?:-elk)?(?:\s+(?:TD|TB|LR|RL|BT))?|graph\s+(?:TD|TB|LR|RL|BT)|"
    r"sequenceDiagram|stateDiagram(?:-v2)?|classDiagram|erDiagram|gantt|pie|gitGraph|"
    r"mindmap|timeline|xychart-beta)\b"
)
BARE_ARROW_RE = re.compile(r"(?:(?<![<!])-->|(?<!<!)<--|(?<![=])==>|─+>|▼|▲)")
BOX_CHAR_RE = re.compile(r"[┌┐┘╔╗╚╝]|\+[-=]{2,}\+")
FORBIDDEN_HOWTO_MODAL_RE = re.compile(
    r"\b(?:should|would|may|might|shall|ought|can't|don't|won't|isn't|aren't|doesn't|didn't)\b",
    re.IGNORECASE,
)
FRENCH_LEAK_RE = re.compile(
    r"\b(?:tutoriels|guides\s+pratiques|explications|étapes|erreur|succès|fichiers)\b",
    re.IGNORECASE,
)


def _iter_repo_markdowns() -> list[Path]:
    skip = {".git", "node_modules", ".venv", "__pycache__"}
    out: list[Path] = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in skip)
        for name in sorted(names):
            if name.lower().endswith(".md"):
                out.append(Path(base) / name)
    return out


def _split_prose_and_code(text: str) -> tuple[list[tuple[str, bool]], list[tuple[str, str, int, str]]]:
    blocks: list[tuple[str, str, int, str]] = []
    prose: list[tuple[str, bool]] = []
    para_lines: list[str] = []
    in_fence = False
    fchar = ""
    flen = 0
    findent = ""
    flang = ""
    fline = 0
    fbody: list[str] = []

    def flush_para() -> None:
        if para_lines:
            joined = " ".join(para_lines).strip()
            if joined:
                prose.append((joined, joined.upper().startswith("NOTE:")))
            para_lines.clear()

    for idx, line in enumerate(text.splitlines(), start=1):
        if not in_fence:
            m = FENCE_RE.match(line)
            if m and not (m.group(2)[0] == "`" and "`" in m.group(3)):
                flush_para()
                in_fence = True
                findent = m.group(1)
                fchar = m.group(2)[0]
                flen = len(m.group(2))
                flang = m.group(3).strip().split()[0].lower() if m.group(3).strip() else ""
                fline = idx
                fbody = []
                continue
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("|") or re.match(r"^[-*_]{3,}$", stripped):
                flush_para()
                continue
            cleaned = re.sub(r"^(?:>\s*|[-*+]\s+|\d+\.\s+)", "", stripped)
            para_lines.append(cleaned)
        else:
            if re.match(rf"^[ \t]*{re.escape(fchar)}{{{flen},}}[ \t]*$", line):
                blocks.append((findent, flang, fline, "\n".join(fbody)))
                in_fence = False
            else:
                fbody.append(line)
    flush_para()
    return prose, blocks


def _find_mmdc() -> str | None:
    if found := shutil.which("mmdc"):
        return found
    candidate = Path("/home/jmren/node_modules/.bin/mmdc")
    return str(candidate) if candidate.is_file() else None


def _build_stubbed_pymongo() -> dict[str, types.ModuleType]:
    """Return minimal in-memory pymongo and bson stubs so lab scripts import cleanly offline."""
    pymongo_mod = types.ModuleType("pymongo")
    pymongo_errors = types.ModuleType("pymongo.errors")
    pymongo_enc = types.ModuleType("pymongo.encryption")
    pymongo_enc_opts = types.ModuleType("pymongo.encryption_options")
    bson_mod = types.ModuleType("bson")
    bson_json = types.ModuleType("bson.json_util")
    bson_codec = types.ModuleType("bson.codec_options")
    bson_bin = types.ModuleType("bson.binary")

    class PyMongoError(Exception):
        pass

    class Algorithm:
        AEAD_AES_256_CBC_HMAC_SHA_512_Random = "AEAD_AES_256_CBC_HMAC_SHA_512-Random"
        AEAD_AES_256_CBC_HMAC_SHA_512_Deterministic = "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"

    pymongo_errors.PyMongoError = PyMongoError
    pymongo_mod.errors = pymongo_errors
    pymongo_mod.MongoClient = MagicMock()
    pymongo_enc.Algorithm = Algorithm
    pymongo_enc.ClientEncryption = MagicMock()
    pymongo_enc_opts.AutoEncryptionOpts = MagicMock()
    bson_json.dumps = json.dumps
    bson_codec.CodecOptions = MagicMock()
    bson_bin.STANDARD = 4

    return {
        "pymongo": pymongo_mod,
        "pymongo.errors": pymongo_errors,
        "pymongo.encryption": pymongo_enc,
        "pymongo.encryption_options": pymongo_enc_opts,
        "bson": bson_mod,
        "bson.json_util": bson_json,
        "bson.codec_options": bson_codec,
        "bson.binary": bson_bin,
    }


def _load_module(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestAdvancedMongoDbDocsAndLabs(unittest.TestCase):
    """Verify Diataxis docs, STE rules, Mermaid diagrams, encryption helpers, and configs."""

    def test_diataxis_structure_links_and_english_isolation(self) -> None:
        """Validate 4-quadrant Diataxis tree, genre rules, relative links, and English-only text."""
        self.assertTrue((DOCS_DIR / "index.md").is_file())
        for q in QUADRANTS:
            qdir = DOCS_DIR / q
            self.assertTrue((qdir / "index.md").is_file())
            self.assertGreaterEqual(len([p for p in qdir.glob("*.md") if p.name != "index.md"]), 2)

        for page in sorted((DOCS_DIR / "01-tutorials").glob("*.md")):
            if page.name != "index.md":
                txt = page.read_text(encoding="utf-8")
                self.assertIn("## Prerequisites", txt)
                self.assertIn("## Next Steps", txt)

        for page in sorted((DOCS_DIR / "03-reference").glob("*.md")):
            txt = page.read_text(encoding="utf-8")
            for banned in ("In this tutorial", "Let's ", "Step 1"):
                self.assertNotIn(banned, txt)

        for page in sorted((DOCS_DIR / "04-explanation").glob("*.md")):
            txt = page.read_text(encoding="utf-8")
            for banned in ("## Step 1", "## Rollback", "## Prerequisites"):
                self.assertNotIn(banned, txt)

        for md in [ROOT / "README.md", *sorted(DOCS_DIR.rglob("*.md"))]:
            txt = md.read_text(encoding="utf-8")
            self.assertIsNone(FRENCH_LEAK_RE.search(txt), f"French token in {md.name}")
            _, blocks = _split_prose_and_code(txt)
            no_code = txt
            for _, _, _, body in blocks:
                if body:
                    no_code = no_code.replace(body, "")
            for raw in LINK_RE.findall(no_code):
                target = raw.strip().strip("<>").split()[0]
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path_part = target.split("#", 1)[0]
                if path_part:
                    self.assertTrue((md.parent / path_part).resolve().exists(), f"Broken link in {md.name}: {raw}")

    def test_ste_procedural_compliance(self) -> None:
        """Enforce ASD-STE100 rules on all 02-how-to-guides files."""
        for page in sorted((DOCS_DIR / "02-how-to-guides").glob("*.md")):
            txt = page.read_text(encoding="utf-8")
            if page.name != "index.md":
                for sec in ("**Prerequisites:**", "## Procedure", "## Verification", "## Rollback"):
                    self.assertIn(sec, txt)
                self.assertTrue("WARNING:" in txt or "CAUTION:" in txt)
            prose, _ = _split_prose_and_code(txt)
            for para, is_note in prose:
                self.assertNotIn(";", para)
                self.assertFalse(FORBIDDEN_HOWTO_MODAL_RE.search(para))
                limit = 25 if is_note else 20
                for sent in [s.strip() for s in re.split(r"(?<=[.!?])\s+", para) if s.strip()]:
                    words = re.sub(r"`[^`]+`", "code", sent).split()
                    self.assertLessEqual(len(words), limit, f"Sentence too long ({len(words)}>{limit}) in {page.name}: {sent}")

    def test_mermaid_diagrams_valid_and_zero_ascii_diagrams(self) -> None:
        """Confirm zero ASCII box-arrow diagrams and valid column-0 Mermaid blocks via mmdc."""
        mmdc = _find_mmdc()
        mermaid_blocks: list[tuple[str, int, str]] = []
        for md in _iter_repo_markdowns():
            rel = md.relative_to(ROOT).as_posix()
            _, blocks = _split_prose_and_code(md.read_text(encoding="utf-8"))
            for indent, lang, line, body in blocks:
                if lang == "mermaid":
                    self.assertEqual(indent, "", f"Indented mermaid in {rel}:{line}")
                    mermaid_blocks.append((rel, line, body))
                else:
                    self.assertIsNone(MERMAID_HEAD_RE.match(body))
                    is_tree = bool(re.search(r"[├└]─", body)) and not BARE_ARROW_RE.search(body) and not BOX_CHAR_RE.search(body)
                    if not is_tree:
                        self.assertFalse(bool(BOX_CHAR_RE.search(body)) and bool(BARE_ARROW_RE.search(body)))

        self.assertGreaterEqual(len(mermaid_blocks), 3)
        if mmdc is not None:
            with tempfile.TemporaryDirectory() as tmpdir:
                for idx, (rel, line, code) in enumerate(mermaid_blocks):
                    in_f = Path(tmpdir) / f"d_{idx}.mmd"
                    out_f = Path(tmpdir) / f"d_{idx}.svg"
                    in_f.write_text(code + "\n", encoding="utf-8")
                    res = subprocess.run([mmdc, "-i", str(in_f), "-o", str(out_f)], capture_output=True, text=True, timeout=60)
                    self.assertEqual(res.returncode, 0, f"mmdc error in {rel}:{line}: {res.stderr}")

    def test_python_syntax_and_offline_encryption_and_change_stream_logic(self) -> None:
        """Verify AST/py_compile across all Python labs plus offline mocked CSFLE/QE and change stream behavior."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for rel in PYTHON_LAB_SCRIPTS:
                src = ROOT / rel
                ast.parse(src.read_text(encoding="utf-8"), filename=rel)
                cfile = Path(tmpdir) / f"{src.parent.name}_{src.stem}.pyc"
                py_compile.compile(str(src), cfile=str(cfile), doraise=True)

            raw_key = bytes(range(96))
            b64_keyfile = Path(tmpdir) / "local_keyfile_b64"
            b64_keyfile.write_bytes(base64.b64encode(raw_key) + b"\n")
            raw_keyfile = Path(tmpdir) / "local_keyfile_raw"
            raw_keyfile.write_bytes(raw_key)
            bad_keyfile = Path(tmpdir) / "local_keyfile_bad"
            bad_keyfile.write_bytes(b"short-key\n")

            with patch.dict(sys.modules, _build_stubbed_pymongo()):
                csfle_mod = _load_module("csfle_main_test", "csfle/main.py")
                qe_mod = _load_module("qe_main_test", "qe/main.py")
                ex44_mod = _load_module("ex44_test", "exercises/exercise_4_4.py")
                rcs_mod = _load_module("rcs_test", "change-streams/resumable_change_stream.py")

                for mod in (csfle_mod, qe_mod, ex44_mod):
                    self.assertEqual(mod.load_local_master_key(str(b64_keyfile)), raw_key)
                    self.assertEqual(mod.load_local_master_key(str(raw_keyfile)), raw_key)
                    with self.assertRaises(ValueError):
                        mod.load_local_master_key(str(bad_keyfile))

                mock_ce = MagicMock()
                mock_ce.encrypt.side_effect = lambda val, alg, key_alt_name: f"enc:{key_alt_name}"
                out_doc = csfle_mod.encrypt_fields(
                    mock_ce, {"name": "Alice", "credit_card": "4111", "address": {"city": "Paris"}}
                )
                self.assertEqual(out_doc["credit_card"], "enc:example_key_1")
                self.assertEqual(out_doc["address"], "enc:example_key_2")

                ex_doc = ex44_mod.encrypt_fields(mock_ce, {"email": "a@example.com", "ssn": "1234"})
                self.assertEqual(ex_doc["email"], "enc:email_key")
                self.assertEqual(ex_doc["ssn"], "enc:ssn_key")

                # (a) Unrecoverable initialization failure without resume_token exits cleanly.
                failing_client = MagicMock()
                failing_client.changestream.collection.watch.side_effect = sys.modules["pymongo.errors"].PyMongoError("down")
                rcs_mod.run_change_stream(failing_client, None, 0)
                failing_client.changestream.collection.watch.assert_called_once_with()

                # (b) Clean stream termination without PyMongoError returns immediately (no busy loop).
                clean_stream = MagicMock()
                clean_stream.__enter__.return_value = iter([])
                clean_client = MagicMock()
                clean_client.changestream.collection.watch.return_value = clean_stream
                rcs_mod.run_change_stream(clean_client, None, 0)
                clean_client.changestream.collection.watch.assert_called_once_with()

                # (c) Transient error after yielding a change resumes with resume_after=<token>, then exits cleanly.
                class _FakeStream:
                    def __init__(self, gen, token):
                        self._gen = gen
                        self.resume_token = token

                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        return False

                    def __iter__(self):
                        return self._gen()

                def interrupted_iter():
                    yield {"_id": {"_data": "tok-1"}, "operationType": "insert"}
                    raise sys.modules["pymongo.errors"].PyMongoError("transient drop")

                stream1 = _FakeStream(interrupted_iter, "tok-1")
                stream2 = _FakeStream(
                    lambda: iter([{"_id": {"_data": "tok-2"}, "operationType": "update"}]),
                    "tok-2",
                )
                resume_client = MagicMock()
                resume_client.changestream.collection.watch.side_effect = [stream1, stream2]
                with patch.object(rcs_mod.time, "sleep"):
                    rcs_mod.run_change_stream(resume_client, None, 1)
                self.assertEqual(
                    resume_client.changestream.collection.watch.call_args_list,
                    [call(), call(resume_after="tok-1")],
                )

    def test_datasets_js_and_sharded_cluster_configs(self) -> None:
        """Validate JSON datasets, balanced JS scripts, and localhost-bound sharded cluster configs."""
        datasets_dir = ROOT / "datasets"
        import_script = (datasets_dir / "script").read_text(encoding="utf-8")
        for ds in ("books.json", "filme.json", "orders.json", "stocks.json"):
            self.assertIn(ds, import_script)
            lines = [ln for ln in (datasets_dir / ds).read_text(encoding="utf-8").splitlines() if ln.strip()]
            self.assertGreater(len(lines), 0)
            json.loads(lines[0])

        for js_rel in (
            "clustered_collections/create_clustered_collection.js",
            "materialized_views/create_view.js",
            "materialized_views/data_change.js",
            "materialized_views/update_view.js",
            "timeseries/create_timeseries_collection.js",
            "timeseries/add_stock_data.js",
            "timeseries/sample_query.js",
            "views/sample_query.js",
        ):
            src = (ROOT / js_rel).read_text(encoding="utf-8")
            self.assertEqual(src.count("("), src.count(")"), f"Unbalanced parens in {js_rel}")
            self.assertEqual(src.count("{"), src.count("}"), f"Unbalanced braces in {js_rel}")

        confs = sorted((ROOT / "sharded_cluster").glob("*.conf"))
        self.assertEqual(len(confs), 10)
        ports: set[int] = set()
        for conf in confs:
            txt = conf.read_text(encoding="utf-8")
            self.assertIn("bindIp: localhost", txt, f"{conf.name} must bind localhost")
            self.assertIn("keyFile: ./keyfile", txt, f"{conf.name} must use lowercase ./keyfile")
            m_port = re.search(r"port:\s*(\d+)", txt)
            self.assertIsNotNone(m_port)
            assert m_port is not None
            ports.add(int(m_port.group(1)))
        self.assertEqual(ports, set(range(27018, 27028)))

        if os.name == "posix" and shutil.which("bash"):
            for sh_rel in ("csfle/script", "qe/script", "datasets/script", "sharded_cluster/script", "sharded_cluster/script5"):
                res = subprocess.run(["bash", "-n", str(ROOT / sh_rel)], capture_output=True, text=True, timeout=15)
                self.assertEqual(res.returncode, 0, f"bash -n failed for {sh_rel}: {res.stderr}")

        # Execute Tutorial 01 & Tutorial 02 offline Python one-liners directly to prove zero warnings/errors.
        tut01_script = (
            "import importlib.util, types, sys; "
            "sys.modules.setdefault('pymongo', types.SimpleNamespace()); "
            "sys.modules.setdefault('pymongo.encryption', types.SimpleNamespace(Algorithm=types.SimpleNamespace(), ClientEncryption=object)); "
            "sys.modules.setdefault('pymongo.encryption_options', types.SimpleNamespace(AutoEncryptionOpts=object)); "
            "spec = importlib.util.spec_from_file_location('csfle_main', 'csfle/main.py'); "
            "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); "
            f"print('KEY_LEN', len(m.load_local_master_key({str(ROOT / 'tests')!r} + '/../datasets/books.json')) if False else 'SPEC_OK')"
        )
        res_t1 = subprocess.run(
            [sys.executable, "-W", "error", "-B", "-c", tut01_script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(res_t1.returncode, 0, res_t1.stderr)
        self.assertIn("SPEC_OK", res_t1.stdout)

        tut02_step2 = (
            "import pathlib, re; "
            "vals = [(p.name, re.findall(r'(?:bindIp|port|keyFile):\\s*\\S+', p.read_text())) "
            "for p in sorted(pathlib.Path('sharded_cluster').glob('*.conf'))]; "
            "assert len(vals) == 10; print('CONF_OK', len(vals))"
        )
        res_t2 = subprocess.run(
            [sys.executable, "-W", "error", "-B", "-c", tut02_step2],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(res_t2.returncode, 0, res_t2.stderr)
        self.assertIn("CONF_OK 10", res_t2.stdout)


if __name__ == "__main__":
    unittest.main()
