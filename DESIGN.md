<img src="images/logo.svg" alt="RenderNote" width="240">

# RenderNote design

Rendernote takes a music score and prepares each part for playing along live, with the audio of the whole piece to follow.
A LilyPond score goes in, and one HTML file comes out that opens in any browser.

## Happy path

```
pip install rendernote
rendernote scarborough-fair.ly
```

This writes `Scarborough-Fair.html` next to the score.
Open it, or send it to the other players.
`rendernote serve scarborough-fair.ly` serves it on your Wi-Fi (with a QR code for a tablet) and rebuilds it whenever the score is saved.

## What goes in

One `.ly` file that LilyPond compiles.
`\include` files work as usual.

- Each staff is a part, named by its `instrumentName` ("Part 1", "Part 2" if it has none).
  A piano or other multi-staff group is one part.
- The title comes from `\header { title = ... }`, or the file name.
- Page defaults (tempo, count-in, click) can be set in the `\header`.
- The first `\score` in the file is the one rendered.
- LilyPond handles transposing instruments, repeats, voices, lyrics and percussion; playback follows what LilyPond's MIDI does.

Other formats come in once and become the `.ly` source from then on: `rendernote import song.musicxml` (or `.abc`), using the converters that ship with LilyPond.
MuseScore users export MusicXML first.

## What comes out

`<Title>.html` (spaces in the title become hyphens), one self-contained file holding:

- the full score and each part, engraved by LilyPond as SVG
- the MIDI, one track per part
- the full score and part PDFs, as download buttons
- the sounds for the instruments used, from MuseScore General (fetched once, 40 MB, into the user's cache; without it the page uses a plain synth sound)
- the player code and the licence notices of what it includes

Loose copies of the PDFs and `.mid` files (`Scarborough-Fair-Part-1.pdf` and so on) are written alongside only on request.

## The page

- Tabs: full score, then one per part.
- On a part: the other parts are drawn smaller; the part's own notes are full size.
- Each view is engraved twice, on an A4-width page and on a 100 mm page for phones; the page shows the one that fits the screen.
- Tap any note to play from there.
  Notes light up as they sound, and the page scrolls a line at a time.
- Tempo slider; volume, mute and solo for each part; click volume, on every beat or only the downbeat, and count-in length; loop between two bars.
- The page makes the click and count-in itself, so they follow the tempo and settings.
- Settings are remembered by each browser and can be put in the link (`#view=Part 1&tempo=80`), so one setup can be shared.
- The build date (and git commit, if the score is in git) shows at the bottom, so players can tell which version they have.

## Code

- `rendernote/build.py`: runs LilyPond, reads the MIDI and assembles the HTML.
- `rendernote/rendernote.ily`: what Rendernote adds to every score (note timing in the SVG, other parts smaller or left out, the phone page size, MIDI with repeats played out).
- `rendernote/soundfont.py`: reads an instrument's samples from a SoundFont.
- `rendernote/page.html`, `rendernote/player.js`: the page, and playback and controls on the browser's own Web Audio, with no libraries.
- `rendernote/cli.py`: the `rendernote` command.
- `examples/scarborough-fair.ly`: the demo, and `examples/scarborough-fair-easy-duet.mscz`, the MuseScore file it came from.

Errors from LilyPond are shown as LilyPond prints them.

## Demo

Scarborough Fair (traditional), an easy duet arranged by Dominic Widdows in 2022 and first published on MuseScore.com.
The parts are Part 1 and Part 2, for any two instruments; playback uses violin.

## Licences

Code: MIT.
The Scarborough Fair arrangement: CC BY 4.0, credited in the score.
MuseScore General: MIT, with its contributors' notices carried in every page that uses it.

## Recording with it

The page is also a backing track for recording yourself, one part at a time.

1. Open the page on a phone or tablet and choose your part.
2. Listen through a wired earpiece in one ear.
   The backing stays out of the recording, you can still hear yourself, and there's no Bluetooth delay.
3. Record yourself, on video or just audio, with another device.
   Keep the click on, and turn your own part up so you can play along with it.
4. Play the piece through several times in one recording.
   The more takes, the more there is to choose from.
5. Do the same for each part.
6. Give the recordings and the score to an agent such as Claude Code, and ask it to pick the best of each take and mix them into one video.
   It can check every take for split notes and line the parts up bar by bar.

The [Moon River trombone quartet video](https://youtu.be/LXzhrkVmQxY) was made this way.
