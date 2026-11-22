\version "2.24.0"
\language "english"

% Jingle Bells (James Lord Pierpont, 1857), arranged for descant and
% treble recorder. This arrangement is dedicated to the public domain (CC0).

\header {
  title = "Jingle Bells"
  composer = "James Lord Pierpont"
  arranger = "arr. for descant and treble recorder"
  tagline = ##f
}

global = {
  \key g \major
  \time 4/4
  \tempo "Brightly" 4 = 120
}

% The descant recorder sounds an octave above written pitch.
descant = {
  \global
  % verse
  d'4\mf b' a' g'    | d'2. d'8 d'      | d'4 b' a' g'     | e'1              |
  e'4 c'' b' a'      | fs'1             | d''4 d'' c'' a'  | b'1              |
  d'4 b' a' g'       | d'1              | d'4 b' a' g'     | e'2. e'4         |
  e'4 c'' b' a'      | d''4 d'' d'' d'' | e''4 d'' c'' a'  | g'2 d''2         |
  % chorus
  b'4\f b' b'2       | b'4 b' b'2       | b'4 d'' g'4. a'8 | b'1              |
  c''4 c'' c''4. c''8 | c''4 b' b' b'8 b' | b'4 a' a' b'    | a'2 d''2         |
  b'4 b' b'2         | b'4 b' b'2       | b'4 d'' g'4. a'8 | b'1              |
  c''4 c'' c'' c''   | c''4 b' b' b'8 b' | d''4 d'' c'' a' | g'1 \bar "|."    |
}

treble = {
  \global
  % verse
  g'2\mp b'2         | b'2. r4          | g'2 b'2          | c''1             |
  c''2 e''2          | d''1             | fs'2 a'2         | g'1              |
  g'2 b'2            | b'1              | g'2 b'2          | c''2. c''4       |
  c''2 e''2          | fs'4 fs' fs' fs' | a'4 b' a' fs'    | g'2 fs'2         |
  % chorus
  d''4\mf d'' d''2   | d''4 d'' d''2    | d''4 b' b'4. c''8 | d''1            |
  e''4 e'' e''4. e''8 | e''4 d'' d'' d''8 d'' | d''4 c'' c'' d'' | c''2 fs'2  |
  d''4 d'' d''2      | d''4 d'' d''2    | d''4 b' b'4. c''8 | d''1            |
  e''4 e'' e'' e''   | e''4 d'' d'' d''8 d'' | fs'4 fs' fs' c'' | b'1 \bar "|." |
}

\score {
  <<
    \new Staff \with {
      instrumentName = "Descant"
      midiInstrument = "recorder"
    } { \clef "treble^8" \transposition c'' \descant }
    \new Staff \with {
      instrumentName = "Treble"
      midiInstrument = "recorder"
    } { \treble }
  >>
  \layout { }
  \midi { }
}
