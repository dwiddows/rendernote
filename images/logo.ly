\version "2.24.0"

% The RenderNote logo: three notes, the middle one lit up as it sounds.
% Engrave with:  lilypond -dbackend=svg -dcrop logo.ly
% then save logo.cropped.svg as logo.svg with a white background, so the
% logo shows on dark pages too.

\paper {
  indent = 0
  ragged-right = ##t
  tagline = ##f
  oddHeaderMarkup = ##f
  oddFooterMarkup = ##f
}

\layout {
  \context { \Staff \remove Time_signature_engraver }
  \context { \Score \override TextScript.self-alignment-X = #CENTER }
}

\relative {
  \clef treble
  e'4
  \once \override NoteHead.color = #red
  g2^\markup \huge \bold "Render" _\markup \huge \bold "Note"
  c4 \bar "|."
}
