# Rendernote design

Rendernote turns a LilyPond score into one HTML file you can open in any
browser: the score and each part, playable by tapping a note, with a
mixer, tempo, click and loop. It is a small project meant to be forked
and extended, so the code favours being short and obvious over handling
every case.

## Happy path

```
pip install rendernote
rendernote jingle-bells.ly
```

This writes `Jingle Bells.html` next to the score. Open it, or send it to
the other players. `rendernote serve jingle-bells.ly` serves it on your
Wi-Fi (with a QR code for a tablet) and rebuilds it whenever the score is
saved.

## What goes in

One `.ly` file that LilyPond compiles. `\include` files work as usual.

- Each staff is a part, named by its `instrumentName` ("Part 1", "Part 2"
  if it has none). A piano or other multi-staff group is one part.
- The title comes from `\header { title = ... }`, or the file name.
- Page defaults (tempo, count-in, click) can be set in the `\header`.
- The first `\score` in the file is the one rendered.
- LilyPond handles transposing instruments, repeats, voices, lyrics and
  percussion; playback follows what LilyPond's MIDI does.

Other formats come in once and become the `.ly` source from then on:
`rendernote import song.musicxml` (or `.abc`), using the converters that
ship with LilyPond. MuseScore users export MusicXML first.

## What comes out

`<Title>.html`, one self-contained file holding:

- the full score and each part, engraved by LilyPond as SVG
- the MIDI, one track per part
- the full score and part PDFs, as download buttons
- the sounds for the instruments used, from MuseScore General
- the player code and the licence notices of what it includes

Loose copies of the PDFs and `.mid` files (`Jingle Bells - Descant.pdf`
and so on) are written alongside only on request.

## The page

- A menu: full score, then one button per part.
- On a part: the other parts are drawn smaller; the part's own notes are
  full size.
- Tap any note to play from there. Notes light up as they sound, and the
  page scrolls a line at a time.
- Tempo slider; volume, mute and solo for each part; click volume, on
  every beat or only the downbeat, and count-in length; loop between two
  bars.
- The click and count-in are made by the page, not baked into the MIDI.
- Settings are remembered by each browser and can be put in the link
  (`#part=descant&tempo=80`), so one setup can be shared.
- The build date (and git commit, if the score is in git) shows at the
  bottom, so players can tell which version they have.

## Code

- `rendernote/build.py`: runs LilyPond and assembles the HTML.
- `rendernote/rendernote.ily`: what Rendernote adds to every score (note
  timing in the SVG, part extraction).
- `rendernote/player.js`: playback and page controls, on Tone.js.
- `rendernote/cli.py`: the `rendernote` command.
- `examples/jingle-bells.ly`: the demo.

Errors from LilyPond are shown as LilyPond prints them.

## Demo

Jingle Bells (James Lord Pierpont, 1857, public domain) for descant and
treble recorder, in an arrangement written for this project.

## Licences

Code: MIT. The Jingle Bells arrangement: CC0. MuseScore General: MIT.
Tone.js: MIT.

## Not in version 1

MP3 or WAV output; recording, comping and video; a hosted service.
