#!/usr/bin/env python3
"""
bake_interface.py — inline an atlas into the page, producing one file.

  python bake_interface.py --template index.html \
      --atlas atlas_gemma-3-1b-it.json --out gemma-3-1b-it.html

  # several models in one page
  python bake_interface.py --template index.html \
      --atlas atlas_gemma-3-1b-it.json atlas_phi-2.json --out interface.html

WHY BAKE

  The page fetches its atlas by default, which needs a web server: opening the
  template from the filesystem trips the browser's origin policy and the fetch
  fails silently. A baked file has no fetch, so it opens by double-clicking and
  can be attached to an email or a supplementary-material upload.

  The cost is size — an atlas is a few megabytes and base64 would add a third,
  so the JSON is embedded directly rather than encoded.

MULTIPLE MODELS

  With more than one atlas the page gains a model selector. Comparing the Gram
  matrix across models is the most informative thing the interface does: the
  same seven word lists produce a well-conditioned basis in one model and a
  poorly conditioned one in another, which is the paper's cross-model finding
  made visible rather than tabulated.
"""
import argparse, json, os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default="index.html")
    ap.add_argument("--atlas", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    html = open(a.template, encoding="utf-8").read()
    atlases = []
    for p in a.atlas:
        d = json.load(open(p, encoding="utf-8"))
        atlases.append(d)
        print(f"  {os.path.basename(p):<40}{d['model']:<28}"
              f"{len(d['tokens']):>7} tokens  c*={d['c_star']}")

    if len(atlases) == 1:
        blob = f"const ATLAS = {json.dumps(atlases[0], separators=(',', ':'))};"
    else:
        blob = (f"const ATLASES = {json.dumps(atlases, separators=(',', ':'))};\n"
                f"const ATLAS = ATLASES[0];")

    html = html.replace('const ATLAS_URL = "atlas_demo.json";',
                        blob + '\nconst ATLAS_URL = null;')

    if len(atlases) > 1:
        # a selector, injected rather than always present, so the single-model
        # build stays free of controls that do nothing
        sel = ('<div style="padding:0 24px 10px"><select id="modelsel" '
               'style="background:#1a1c26;color:#e8e9f0;border:1px solid #2b2e3d;'
               'border-radius:6px;padding:6px 10px;font-family:inherit;'
               'font-size:12.5px">' +
               "".join(f'<option value="{i}">{d["model"]}</option>'
                       for i, d in enumerate(atlases)) +
               '</select></div>')
        html = html.replace('<div class="wrap">', sel + '<div class="wrap">')
        html = html.replace(
            'if (typeof ATLAS !== "undefined") boot(ATLAS);',
            'if (typeof ATLASES !== "undefined") {\n'
            '  boot(ATLASES[0]);\n'
            '  document.getElementById("modelsel").onchange = e => {\n'
            '    mode = "dual";\n'
            '    document.getElementById("b-dual").className = "on";\n'
            '    document.getElementById("b-raw").className = "";\n'
            '    boot(ATLASES[+e.target.value]);\n'
            '  };\n'
            '} else if (typeof ATLAS !== "undefined") boot(ATLAS);')

    open(a.out, "w", encoding="utf-8").write(html)
    mb = os.path.getsize(a.out) / 1e6
    print(f"\n-> {a.out}  ({mb:.1f} MB)")
    if mb > 25:
        print("  Large for a single file. Consider raising --top-per-axis "
              "filtering in make_atlas.py, or shipping one model per page.")


if __name__ == "__main__":
    main()
