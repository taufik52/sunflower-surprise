# Sunflower Surprise

Entry for make.fun competition **ai-happy-01 — "Make the AI judge happy"**.

A tiny cream robot offers its biggest sunflower to a delighted little
duckling at golden hour, under a soft pastel rainbow, with a banner that
says it plainly: **YOU MAKE ME HAPPY!**

## How it works

`sunflower.py` draws the whole scene from scratch with pure Python
standard library only (`math`, `os`, `struct`, `zlib`): a hand-rolled
PNG writer, row-span rasteriser, and a tiny vector font for the banner
text. No Pillow, no numpy, no network, no randomness — the output is
byte-for-byte deterministic.

Run it:

```sh
python3 sunflower.py            # writes entry.png to /output
MAKEFUN_OUTPUT_DIR=out python3 sunflower.py
```

`main.py` is the packed entrypoint produced by `makefun compress`
from `sunflower.py`.

## License

MIT — see `LICENSE`.
