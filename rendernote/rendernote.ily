%% What Rendernote adds to every score it engraves.
%%
%% Set before this file is included (build.py writes a small wrapper):
%%   rendernote-focus  the part a view is for, or #f for the full score
%%   rendernote-narrow #t for the phone-width engraving of a view
%%   rendernote-mode   'shrink  other parts drawn smaller (the page)
%%                     'remove  other parts left out (a part's PDF)
%%                     'midi    no engraving; MIDI with repeats played out

#(define (rn-part-name context)
   "The instrumentName of this staff, or of the group it belongs to."
   (let loop ((ctx context))
     (if (not ctx)
         ""
         (let ((name (ly:context-property ctx 'instrumentName #f)))
           (if (and name (not (equal? name "")))
               (if (string? name) name (markup->string name))
               (loop (ly:context-parent ctx)))))))

%% Every note head in the SVG carries its part, when it starts and ends (in
%% quarter notes from the start of the piece), and its pitch, so the page can
%% play from any note and light up the notes that are sounding.
rnNoteTiming =
#(lambda (context)
   (make-engraver
    (acknowledgers
     ((note-head-interface engraver grob source-engraver)
      (let* ((event (ly:grob-property grob 'cause))
             (start (ly:moment-main (ly:context-current-moment context)))
             (len (ly:moment-main (ly:duration-length (ly:event-property event 'duration))))
             (pitch (ly:event-property event 'pitch)))
        (ly:grob-set-property! grob 'output-attributes
          (list (cons 'class "rn-note")
                (cons 'data-part (rn-part-name context))
                (cons 'data-start (number->string (exact->inexact (* 4 start))))
                (cons 'data-end (number->string (exact->inexact (* 4 (+ start len)))))
                (cons 'data-pitch (number->string (+ 60 (ly:pitch-semitones pitch)))))))))))

%% In a part's view, every other staff is drawn at 3/5 size (or left out).
rnFocus =
#(lambda (context)
   (make-engraver
    ((initialize engraver)
     (if (and rendernote-focus
              (not (equal? (rn-part-name context) rendernote-focus)))
         (if (eq? rendernote-mode 'remove)
             (begin
               (ly:context-set-property! context 'keepAliveInterfaces '())
               (ly:context-pushpop-property context 'VerticalAxisGroup 'remove-empty #t)
               (ly:context-pushpop-property context 'VerticalAxisGroup 'remove-first #t))
             (begin
               (ly:context-set-property! context 'fontSize (magnification->font-size 3/5))
               (ly:context-pushpop-property context 'StaffSymbol 'staff-space 3/5)
               (ly:context-pushpop-property context 'StaffSymbol 'thickness 3/5)))))))

\layout {
  \context {
    \Staff
    \consists \rnNoteTiming
    \consists \rnFocus
  }
}

#(if (memq rendernote-mode '(shrink none))
     (ly:parser-include-string
      "\\paper { page-breaking = #ly:one-page-breaking  ragged-bottom = ##t }"))

%% Phones get their own engraving: a page 100 mm wide, so a line holds a few
%% bars at a readable size instead of a whole A4 line shrunk to fit.
#(if rendernote-narrow
     (ly:parser-include-string
      "\\paper { paper-width = 100\\mm  left-margin = 3\\mm  right-margin = 3\\mm  indent = 0  short-indent = 0 }
       \\layout { \\context { \\Staff \\remove Instrument_name_engraver } }"))

%% MIDI: every score gets a \midi output, with its repeats played out, and
%% nothing engraved.
#(if (eq? rendernote-mode 'midi)
     (set! toplevel-score-handler
       (lambda (score)
         (let ((s (ly:make-score
                   (unfold-repeats-fully (ly:music-deep-copy (ly:score-music score))))))
           (ly:score-add-output-def! s (ly:output-def-clone $defaultmidi))
           (collect-scores-for-book s)))))
