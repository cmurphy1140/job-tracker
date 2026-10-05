"""Render a static terminal transcript of the sample run:

    python3 docs/demo/render_demo.py [--command PATH] [--out PATH]

Runs the installed `tracker-digest` console command on `sample/leads.csv`
(copied into a temporary directory so the review log never lands in the
repository), feeds the typed answers on stdin, and writes a dark,
monospace HTML page with the prompts and the typed answers visually
distinct. Standard library only. The prompts come from `input()` and so
carry no trailing newline; the renderer splits on the `[y/N] ` suffix
to put each prompt and its answer on their own line.
"""
import argparse
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = Path(__file__).resolve().parent / "tracker-digest-demo.html"
COMMAND_ARGS = ["sample/leads.csv", "--today", "2026-09-18"]
ANSWERS = ["y", "y"]
# `input()` leaves the cursor after the prompt; split right after each one.
PROMPT_SPLIT = re.compile(r"(?<=\[y/N\] )")

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>tracker-digest {version} demo</title>
<style>
  :root {{
    --bg: #0f1419; --panel: #161b22; --border: #2a313b;
    --text: #d7dde5; --dim: #7d8794; --prompt: #79b8ff; --typed: #f2cc60;
    --title: #e6edf3; --fix: #ff9e8a;
  }}
  body {{ margin: 0; padding: 40px 16px; background: var(--bg); color: var(--text);
         font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 14px; }}
  .window {{ max-width: 860px; margin: 0 auto; background: var(--panel);
             border: 1px solid var(--border); border-radius: 10px; overflow: hidden;
             box-shadow: 0 20px 50px rgba(0,0,0,.5); }}
  .bar {{ display: flex; align-items: center; gap: 8px; padding: 10px 14px;
          background: #1c2230; border-bottom: 1px solid var(--border); color: var(--dim); }}
  .dot {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; }}
  .bar .title {{ margin-left: 8px; color: var(--title); }}
  pre {{ margin: 0; padding: 18px 20px 22px; line-height: 1.55; white-space: pre-wrap;
         word-break: break-word; }}
  .cmd {{ color: var(--title); font-weight: 600; }}
  .cmd::before {{ content: "$ "; color: var(--dim); }}
  .prompt {{ color: var(--prompt); }}
  .typed {{ color: var(--typed); font-weight: 700; background: rgba(242,204,96,.12);
            padding: 0 4px; border-radius: 3px; }}
  .fix {{ color: var(--fix); }}
  .note {{ max-width: 860px; margin: 14px auto 0; color: var(--dim); font-size: 12px; }}
  .note code {{ color: var(--text); }}
</style>
</head>
<body>
<div class="window">
  <div class="bar">
    <span class="dot" style="background:#ff5f57"></span>
    <span class="dot" style="background:#febc2e"></span>
    <span class="dot" style="background:#28c840"></span>
    <span class="title">tracker-digest {version} &mdash; review of sample/leads.csv</span>
  </div>
<pre><span class="cmd">{command}</span>
{body}</pre>
</div>
<p class="note">Typed answers are highlighted. Exit code {exit_code}. Rendered by
<code>docs/demo/render_demo.py</code> from the synthetic <code>sample/leads.csv</code>.</p>
</body>
</html>
"""


def read_version():
    init = (REPO / "src" / "tracker_digest" / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'__version__ = "([^"]+)"', init).group(1)


def run_sample(command):
    """Run the console command in a scratch copy of the sample; return (stdout, exit code)."""
    with tempfile.TemporaryDirectory() as tmp:
        sample_dir = Path(tmp) / "sample"
        sample_dir.mkdir()
        shutil.copy(REPO / "sample" / "leads.csv", sample_dir / "leads.csv")
        proc = subprocess.run(
            [command, *COMMAND_ARGS],
            input="".join(answer + "\n" for answer in ANSWERS),
            capture_output=True, text=True, cwd=tmp,
        )
    return proc.stdout + proc.stderr, proc.returncode


def transcript_html(output):
    """Interleave the typed answers after each prompt and mark up the lines."""
    pieces = PROMPT_SPLIT.split(output)
    prompts, rest = pieces[:-1], pieces[-1]
    if len(prompts) != len(ANSWERS):
        sys.exit(f"expected {len(ANSWERS)} prompts, found {len(prompts)}: {output!r}")

    lines = []
    for prompt, answer in zip(prompts, ANSWERS):
        lines.append(f'<span class="prompt">{html.escape(prompt)}</span><span class="typed">{html.escape(answer)}</span>')
    for line in rest.rstrip("\n").split("\n"):
        escaped = html.escape(line)
        if line.startswith("  line "):
            escaped = f'<span class="fix">{escaped}</span>'
        lines.append(escaped)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render the tracker-digest demo transcript as HTML.")
    parser.add_argument("--command", default="tracker-digest", help="Console command to run (default: tracker-digest on PATH).")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    output, exit_code = run_sample(args.command)
    page = PAGE.format(
        version=read_version(),
        command=html.escape(" ".join(["tracker-digest", *COMMAND_ARGS])),
        body=transcript_html(output),
        exit_code=exit_code,
    )
    args.out.write_text(page, encoding="utf-8")
    print(f"wrote {args.out} (exit code of the demo run: {exit_code})")
    return 0 if exit_code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
