from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "platinum-189-source.png"
DISPLAY = ROOT / "assets" / "platinum-189.png"
ICON = ROOT / "assets" / "platinum-189.ico"
FAVICON = ROOT / "site" / "favicon.png"


def main(offline=False):
    source = Image.open(ROOT / "assets" / "platinum-189-offline-source.png" if offline else SOURCE).convert("RGBA")
    side = max(source.size)
    bounds = source.getchannel("A").getbbox()
    if not bounds:
        raise ValueError("Icon source is fully transparent")
    artwork = source.crop(bounds)
    scale = (side * 0.88) / max(artwork.size)
    artwork = artwork.resize(
        (round(artwork.width * scale), round(artwork.height * scale)),
        Image.Resampling.LANCZOS,
    )
    image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    image.alpha_composite(artwork, ((side - artwork.width) // 2, (side - artwork.height) // 2))
    image.save(ROOT / "assets" / "platinum-189-offline.png" if offline else DISPLAY, optimize=True)
    image.save(
        ROOT / "assets" / "platinum-189-offline.ico" if offline else ICON,
        format="ICO",
        sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    if not offline:
        image.resize((256, 256), Image.Resampling.LANCZOS).save(FAVICON, optimize=True)


if __name__ == "__main__":
    main()
    main(offline=True)
