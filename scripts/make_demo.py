"""Turn four browser-captured screens into a ten-second project walkthrough."""

from pathlib import Path

from PIL import Image


def main() -> None:
    source = Path("web/test-results/live")
    frames = [
        Image.open(source / (name + ".png")).convert("RGB")
        for name in ("statement", "allocation", "anomalies", "portfolio")
    ]
    frames[0].save(
        source / "demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=2500,
        loop=0,
        optimize=True,
    )
    with Image.open(source / "demo.gif") as output:
        assert output.n_frames == 4
        assert (
            sum(output.seek(i) or output.info["duration"] for i in range(output.n_frames)) == 10000
        )


if __name__ == "__main__":
    main()
