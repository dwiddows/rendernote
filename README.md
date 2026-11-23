<img src="https://dwiddows.github.io/rendernote/images/rendernote_logo.svg" alt="RenderNote" width="200">

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
There's a simple 2-part demo example of [Scarborough Fair](https://dwiddows.github.io/rendernote/examples/Scarborough-Fair.html),
created from this [Scarborough Fair Easy Duet](http://musescore.com/user/6157466/scores/8300549) on MuseScore.

The parts and backing track for [Moon River trombone quartet video](https://youtu.be/I_E8MWM5BTQ) were made using RenderNote.
It should easily scale to many more parts. The parts can be shared and recorded anywhere, and then gathered and mixed later.

[DESIGN.md](https://github.com/dwiddows/rendernote/blob/main/DESIGN.md) describes how it works and how to record with it.
MIT licence.
