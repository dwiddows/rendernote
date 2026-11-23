\version "2.24.0"
\language "english"

% Scarborough Fair (traditional), easy duet for any two instruments.
% Arrangement by Dominic Widdows, 2022, shared under CC BY 4.0
% (https://creativecommons.org/licenses/by/4.0/).
% First published at https://musescore.com/user/6157466/scores/8300549

\header {
  title = "Scarborough Fair"
  subtitle = "Easy duet"
  composer = "Traditional"
  arranger = "arr. Dominic Widdows"
  copyright = \markup \center-column {
    "Arrangement © 2022 Dominic Widdows, CC BY 4.0."
    "First published on MuseScore.com as"
    \with-url "https://musescore.com/user/6157466/scores/8300549" \underline "Scarborough Fair Easy Duet"
  }
  tagline = ##f
}

global = {
  \key c \major
  \time 3/4
  \tempo 4 = 120
}

partOne = \relative d' {
  \global
  d2 d4     | a'2 a4    | e4. f8 e4 | d2.~      |
  d4 a' c   | d2 c4     | a4 b g    | a2.~      |
  a2 d4     | d2 d4     | c2 a4     | a4 g f    |
  e2.~      | e2.       | d2 a'4    | g2 f4     |
  e4 d c    | d2.~      | d2.       |
  d2 d4     | a'2 a4    | e4. f8 e4 | d2.~      |
  d4 a' c   | d2 c4     | a4 b g    | a2.~      |
  a2 d4     | d2 d4     | c2 a4     | a4 g f    |
  e2.~      | e2.       | d2 a'4    | g2 f4     |
  e4 d c    | d2.~      | d2. \bar "|."
}

partTwo = \relative d' {
  \global
  d2 d4     | f2 f4     | c2 c4     | d4 f e    |
  d2 e4     | f2.       | g2.       | d4 e c    |
  d2 d4     | d2 e4     | f2 f4     | f2 f4     |
  c4 d b    | c2 a4     | d2.       | c2.       |
  a2.       | d4 e f    | g4 f e    |
  d2 g4     | f4 e d    | c2 a4     | d4 e f    |
  g4 f e    | d2 e4     | f4 g2~    | g4 f a    |
  g4 f e    | d2 e4     | f4 g f    | f4 e d    |
  c2 a4     | c4 d e    | f2.       | e2 d4     |
  c2 a4     | d2.~      | d2. \bar "|."
}

\score {
  <<
    \new Staff \with { instrumentName = "Part 1"  midiInstrument = "violin" } \partOne
    \new Staff \with { instrumentName = "Part 2"  midiInstrument = "violin" } \partTwo
  >>
  \layout { }
  \midi { }
}
