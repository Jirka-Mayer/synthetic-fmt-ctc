import music21


def remove_problematic_notation(score: music21.stream.Score):
    """Removes notation elements that would not be synthesized anyways,
    so that the training annotations correspond to the synthetic images."""
    
    # The list of problematic symbols is listed in
    # Primus2018Enumerator.PROBLEMATIC_INCIPITS_CONTAINING

    # remove all grace notes
    for note in score.flatten().getElementsByClass(music21.note.Note):
        if note.duration.isGrace:
            score.remove(note, recurse=True)
    
    # multirests are already handled in MEI, no need to handle here

    # fermatas are really infrequent so we will just leave them in

    # slurs are not that common, ties are more common and really,
    # they should be added to the synthesizer asap.
