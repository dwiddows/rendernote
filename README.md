<img src="images/logo.svg" alt="RenderNote" width="200">

RenderNote takes a music score and prepares each part for playing along live, with the audio of the whole piece to follow.
A LilyPond score goes in, and one HTML file comes out that opens in any browser.

You need [LilyPond](https://lilypond.org/download.html) (on a Mac, `brew install lilypond`).
Then:

```
git clone https://github.com/dwiddows/rendernote
cd rendernote
pip install .
rendernote examples/scarborough-fair.ly
```

This writes `examples/Scarborough-Fair.html`.
Open it, choose a part, and tap any note to play from there.

The [Moon River trombone quartet video](https://youtu.be/I_E8MWM5BTQ) was recorded one part at a time, playing along with these pages.

[DESIGN.md](DESIGN.md) describes how it works and how to record with it.
MIT licence.
