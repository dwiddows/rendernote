\version "2.24.0"

% The RenderNote logo: RENDER and NOTE written down the spaces of the
% staff, then two notes, the second lit red as if sounding.
% Engrave with:  lilypond -dbackend=svg -dcrop rendernote_logo.ly
% then save rendernote_logo.cropped.svg as rendernote_logo.svg with a white background, so the
% logo shows on dark pages too.
\paper { indent = 0 ragged-right = ##t tagline = ##f oddHeaderMarkup = ##f oddFooterMarkup = ##f }

% one letter per space: R above the staff (G), E N D E in the E C A F spaces, R below (D)
renderWord = \markup \abs-fontsize #5.6 \bold \override #'(baseline-skip . 1) \center-column { R E N D E R }
% N O T E in the E C A F spaces, beside it
noteWord = \markup \abs-fontsize #5.6 \bold \override #'(baseline-skip . 1) \center-column { N O T E }
words = \markup \line { \renderWord \hspace #0.5 \lower #1 \noteWord }

\layout {
  \context {
    \Staff
    \remove Time_signature_engraver
    \override Clef.stencil = #(lambda (grob) (grob-interpret-markup grob words))
    \override Clef.Y-offset = #2.11
    \override Clef.space-alist.first-note = #'(minimum-fixed-space . 2.5)
  }
  \context { \Score \omit BarLine }
}

\relative {
  \clef treble
  e'4
  \once \override NoteHead.color = #red
  g2
}
