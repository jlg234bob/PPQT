# These imports move Python 2.x almost to Python 3.
# They must precede anything except #comments, including even the docstring
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

__version__ = "0.1.0" # refer to PEP-0008
__author__  = "David Cortesi"
__copyright__ = "Copyright 2011, 2012 David Cortesi"
__maintainer__ = "?"
__email__ = "tallforasmurf@yahoo.com"
__status__ = "first-draft"
__license__ = '''
 License (GPL-3.0) :
    This file is part of PPQT.
    PPQT is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You can find a copy of the GNU General Public License in the file
    extras/COPYING.TXT included in the distribution of this program, or see:
    <http://www.gnu.org/licenses/>.
'''

'''
Implement the Footnote managament panel, whose chief feature is a table
of footnotes that is re/built with a Refresh button. Important nomenclature:
A footnote KEY is a symbol that links a REFERENCE to a NOTE.
A Reference
* appears in text but never in column 0,
* has a Key in square brackets with no superfluous spaces, e.g. [A] or [2].
A Note
* begins on a line following its matching reference
* always begins in column 0 with [Footnote k: where k is a Key.
* always ends with a right square bracket at end of line.

It is not required that Keys be unique. (It is normal for most Keys in a PG
text to be proofed as "A" and a few as "B".) However it is expected and required
that (a) the Reference with Key k precedes the Note with the matching Key k,
and (b) Notes with the same Key appear in the same sequence as their references.

A Note may contain a Reference, but Notes may NOT be nested. A Note ref'd from
another Note must be outside the other note. A note may contain square brackets
so long as the contained brackets do not end a line. This is valid:

  Text[A] and more text[A]
  ...
  [Footnote A: this note has[i] a reference.]
  [Footnote A: this is the second note A and runs
  to multiple -- [text in brackets but not at end of line] --
  lines]
  [Footnote i: inner note referenced from A.]
  
After a Refresh, the table has these columns:

Key:        The key symbol from a footnote, e.g. A or i or 1.

Class:      The class of the key, one of:
                ABC     uppercase alpha
                IVX     uppercase roman numeral
                123     decimal
                abc     lowercase alpha
                ivx     lowercase roman numeral
                *\u00A4\u00A5 symbols

Ref Line:   The text block (line) number containing the key, e.g. [A]

Note Line:   The text block number of the matching [Footnote A: if found

Length:    The length in lines of the matched Note

Text:      The opening text of the Note e.g. [Footnote A: This note has...

The example above might produce the following table:

 Key   Class  Ref Line   Note Line   Length   Text
  A     ABC     1535      1570         1      Footnote A: this note has[i..
  A     ABC     1535      1571         3      Footnote A: this is the sec..
  i     ivx     1570      1574         1      Footnote i: inner note refe..

The table interacts as follows.

* Clicking Key jumps the edit text to the Ref line, unless it is on the ref
  line in which case it jumps to the Note line, in other words, click/click
  to cycle between the Ref and the Note.

* Clicking Ref Line jumps the edit text to that line with the Key
(not the whole Reference) selected.

* Clicking Note line jumps the edit text to that line with the Note selected.

* Doubleclicking Class gets a popup list of classes (see Pages Folio Action)
  and the user can select a different class which is noted.

* When a Key or a Note is not matched, its row is pink.

The actual data behind the table is a Python list of dicts where each dict
describes one Key and/or Note (both when they match), with these fields:

'K' :  Key symbol as a QString
'C' :  Key class number
'R' :  QTextCursor with position/anchor selecting the Key in the Ref, or None
'N' :  QTextCursor selecting the Note, or None

If a Reference is found, K has the Key and R selects the Key.
If a Note is found, K has the key and N selects the Note.
When a Ref and a Note are matched, all fields are set.

Note we don't pull out the line numbers but rather get them as needed from the
QTextCursors. This is because Qt keeps the cursors updated as the document
is edited, so edits that don't modify Refs or Notes don't need Refresh to keep
the table current.

When Refresh is clicked, this list of dicts is rebuilt by scanning the whole
document with regexs to find References and Notes, and matching them.
The progress bar is used during this process.

During Refresh, found Keys are assigned to a number class based on their
values expressed as regular expressions:
    Regex               Assumed class
    [IVXLCDM]{1,15}       IVX
    [A-Z]{1,2}            ABC
    [1-9]{1,3}            123
    [ivxlcdm]{1,15}       ivx
    [a-z]{1,2}            abc
    [*\u00a4\u00a7\u00b6\u2020\u20221] symbols *, para, currency, dagger, dbl-dagger

(Note these are NOT unicode-aware. In Qt5 it may be possible to code a regex
to detect any Unicode uppercase, and we can revisit allowing e.g. Keys with
Greek or Cyrillic letters. For now, only latin-1 key values allowed.)

Other controls supplied at the bottom of the panel are:

Renumber Streams: a box with the six Key classes and for each, a popup
giving the choice of renumber stream:

  no renumber
  1,2,..999
  A,B,..ZZ
  I,II,..M
  a,b,..zz
  i,ii,..m

There are five unique number streams, set to 0 at the start of a renumber
operation and incremented before use, and formatted in one of five ways.
The initial settings of classes to streams are:

  123 : 1,2,..999
  ABC : A,B,..ZZ
  IVX : A,B,..ZZ
  abc : a,b,..zz
  ivx : a,b,..zz
  sym : no renumber

A typical book has only ABC keys, or possibly ABC and also ixv or 123 Keys.
There is unavoidable ambiguity between alpha and roman classes. Although an
alpha key with only roman letters is classed as roman, the renumber stream
for roman is initialized to the alpha number stream.

In other words, the ambiguity is resolved in favor of treating all alphas
as alphas. If the user actually wants a roman stream, she can e.g. set
class ivx to use stream i,ii..m. Setting either roman Class to use a
roman Stream causes the alpha class of that case to be set to no-renumber.
Setting an alpha class to use any stream causes the roman stream of that
case to also use the same stream. Thus we will not permit a user to try
to have both an alpha stream AND a roman stream of the same letter case
at the same time.

The Renumber button checks for any nonmatched keys and only shows an error
dialog if any exist. Else it causes all Keys in the table to be renumbered
using the stream assigned to their class. This is a single-undo operation.

A Footnote Section is marked off using /F .. F/ markers (which are ignored by
the reflow code). The Move Notes button asks permission with a warning message.
On OK, it scans the document and makes a list of QTextCursors of the body of
all Footnote Sections. If none are found it shows an error and stops. If the 
last one found is above the last Note in the table, it shows an error and stops.
Else it scans the Notes in the table from bottom up. For each note, if the note
is not already inside a Footnote section, its contents are inserted at the
head of the Footnote section next below it and deleted at the 
original location. The QTextCursor in the table is repositioned.

The database of footnotes built by Refresh and shown in the table is cleared
on the DocHasChanged signal from pqMain, so it has to be rebuilt after any
book is loaded, and isn't saved. We should think about adding the footnote
info to the document metadata, but only if the Refresh operation proves to be
too lengthy to bear.

'''

from PyQt4.QtCore import (
    Qt,
    QAbstractTableModel,QModelIndex,
    QChar, QString, QStringList,
    QRegExp,
    QVariant,
    SIGNAL)
from PyQt4.QtGui import (
    QBrush, QColor,
    QComboBox,
    QItemDelegate,
    QSpacerItem,
    QTableView,
    QGroupBox,
    QHBoxLayout, QVBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextCursor,
    QWidget)
import pqMsgs

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# This code is global and relates to creating the "database" of footnotes.
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Right, let's get some constants defined globally
# KeyClass_* gives sequential integer values to the classes.
KeyClass_IVX = 0
KeyClass_ABC = 1
KeyClass_ivx = 2
KeyClass_abc = 3
KeyClass_123 = 4
KeyClass_sym = 5
# name strings in KeyClass_* numeric order
KeyClassNames = (
    QString(u'IVX'),
    QString(u'ABC'),
    QString(u'ivx'),
    QString(u'abc'),
    QString(u'123'),
    QString(u'*\u00a4\u00a7') )
# stream names as a QStringList in KeyClass_* numeric order
# (used in comboboxes)
StreamNames = QStringList(QString(u'I,II..M')) << \
    QString(u'A,B,..ZZ') << \
    QString(u'i,ii..m') << \
    QString(u'a,b,..zz') << \
    QString(u'1,2,..999') << \
    QString(u'no renumber')
# class-detecting REs in KeyClass_* numeric order
ClassREs = (
    u'[IVXLCD]{1,15}', # ROMAN to DCCCCLXXXXVIII
    u'[A-Z]{1,2}',     # ALPHA to ZZ (should it be ZZZ?)
    u'[ivxlcd]{1,15}', # roman to whatever
    u'[a-z]{1,2}',     # alpha to zz (?)
    u'\d{1,3}',       # decimal to 999
    u'[\*\u00a4\u00a7\u00b6\u2020\u2021]' # star currency section para dagger dbl-dagger
    )

# The regex for finding a Ref to any possible Key class.
# (This is so pythonic I want to choke...)
RefFinderRE = QRegExp( u'\[(' + u'|'.join(ClassREs) + u')\]' )
# The similar regex for finding the head of a Note of any Key class.
NoteFinderRE = QRegExp( u'\[Footnote\s+(' + u'|'.join(ClassREs) + u')\s*\:' )

# Some notes about QTextCursors. A cursor is connected to a document (our main
# document) and has an anchor and a position. If .anchor() != .position() there
# is a selection. Qt doesn't care which is lower (closer to the top of the doc)
# but we take pains herein that .anchor() < .position(), i.e. the cursor is
# "positioned" at the end of the selection, the anchor at the start.

# Given a QTextCursor that selects a Reference, return its line number.
# (Also used for text cursors that index /F and F/ lines.)
def refLineNumber(tc):
    if tc is not None:
        return tc.block().blockNumber() # block number for tc.position()
    return None

# Given a QTextCursor that selects a Note, return its line number, which is
# the block number for the anchor, not necessarily that of the position.
def noteLineNumber(tc):
    if tc is not None:
        return tc.document().findBlock(tc.anchor()).blockNumber()
    return None

# Given a QTextCursor that selects a Note, return the number of lines in it.
def noteLineLength(tc):
    if tc is not None:
        return 1 + tc.blockNumber() - \
            tc.document().findBlock(tc.anchor()).blockNumber() 
    return 0

# Given a QString that is a Key, return the class of the Key.
# single-class Regexes based on ClassREs above, tupled with the code.
ClassQRegExps = (
    (KeyClass_IVX, QRegExp(ClassREs[KeyClass_IVX])),
    (KeyClass_ABC, QRegExp(ClassREs[KeyClass_ABC])),
    (KeyClass_123, QRegExp(ClassREs[KeyClass_123])),
    (KeyClass_ivx, QRegExp(ClassREs[KeyClass_ivx])),
    (KeyClass_abc, QRegExp(ClassREs[KeyClass_abc])),
    (KeyClass_sym, QRegExp(ClassREs[KeyClass_sym]))
    )
def classOfKey(qs):
    for (keyclass,regex) in ClassQRegExps:
        if 0 == regex.indexIn(qs):
            return keyclass
    return None

# Given a QTextCursor that selects a Key (as in a Reference)
# return the class of the Key.
def classOfRefKey(tc):
    return classOfKey(tc.selectedText())

# Given a QTextCursor that selects a Note, return the note's key.
# We assume that tc really selects a Note so that noteFinderRE will
# definitely hit so we don't check its return. All we want is its cap(1).
def keyFromNote(tc):
    NoteFinderRE.indexIn(tc.selectedText())
    return NoteFinderRE.cap(1)

# Given a QTextCursor that selects a Note, return the class of its key.
def classOfNoteKey(tc):
    return classOfKey(keyFromNote(tc))

# Given a QTextCursor that selects a Note, return the leading characters,
# truncated at 40 chars, from the Note.
MaxNoteText = 40
def textFromNote(tc):
    qs = QString()
    if tc is not None:
        qs = tc.selectedText()
        if MaxNoteText < qs.size() :
            qs.truncate(MaxNoteText-3)
            qs.append(u'...')
    return qs

# The following is the database for the table of footnotes.
# This is empty on startup and after the DocHasChanged signal, then built
# by the Refresh button.

TheFootnoteList = [ ]
TheCountOfUnpairedKeys = 0

# Make a database item given ref and note cursors as available.
# Note we copy the text cursors so the caller doesn't have to worry about
# overwriting, reusing, or letting them go out of scope afterward.
def makeDBItem(reftc,notetc):
    keyqs = reftc.selectedText() if reftc is not None else keyFromNote(notetc)
    item = {'K': keyqs,
            'C': classOfKey(keyqs),
            'R': QTextCursor(reftc) if reftc is not None else None,
            'N': QTextCursor(notetc) if notetc is not None else None
            }
    return item

# Append a new matched footnote to the end of the database, given the
# cursors for the reference and the note. It is assumed this is called on
# a top-to-bottom sequential scan so entries will be added in line# sequence.

def addMatchedPair(reftc,notetc):
    global TheFootnoteList
    TheFootnoteList.append(makeDBItem(reftc,notetc))

# insert an unmatched reference into the db in ref line number sequence.
# unmatched refs and notes are expected to be few, so a sequential scan is ok.
def insertUnmatchedRef(reftc):
    global TheFootnoteList
    item = makeDBItem(reftc,None)
    j = refLineNumber(reftc)
    for i in range(len(TheFootnoteList)):
        if j <= refLineNumber(TheFootnoteList[i]['R']) :
            TheFootnoteList.insert(i,item)
            return
    TheFootnoteList.append(item) # unmatched ref after all other refs

# insert an unmatched note in note line number sequence.
def insertUnmatchedNote(notetc):
    global TheFootnoteList
    item = makeDBItem(None,notetc)
    j = noteLineNumber(notetc)
    for i in range(len(TheFootnoteList)):
        if j <= noteLineNumber(notetc) :
            TheFootnoteList.insert(i,item)
            return

# Based on the above spadework, do the Refresh operation
def theRealRefresh():
    global TheFootnoteList,TheCountOfUnpairedKeys
    TheFootnoteList = [] # wipe the slate
    TheCountOfUnpairedKeys = 0
    doc = IMC.editWidget.document() # get handle of document
    # initialize status message and progress bar
    barCount = doc.characterCount()
    pqMsgs.startBar(barCount * 2,"Scanning for notes and references")
    barBias = 0 
    # scan the document from top to bottom finding References and make a
    # list of them as textcursors. doc.find(re,pos) returns a textcursor
    # that .isNull on no hit.
    listOrefs = []
    findtc = QTextCursor(doc) # cursor that points to top of document
    findtc = doc.find(RefFinderRE,findtc)
    while not findtc.isNull() : # while we keep finding things
        # findtc now selects the whole reference [xx] but we want to only
        # select the key. This means incrementing the anchor and decrementing
        # the position; the means to do this are a bit awkward.
        a = findtc.anchor()+1
        p = findtc.position()-1
        findtc.setPosition(a,QTextCursor.MoveAnchor) #click..
        findtc.setPosition(p,QTextCursor.KeepAnchor) #..and drag
        listOrefs.append(QTextCursor(findtc))
        pqMsgs.rollBar(findtc.position())
        findtc = doc.find(RefFinderRE,findtc) # look for the next
    barBias = barCount
    pqMsgs.rollBar(barBias)
    # scan the document again top to bottom now looking for Notes, and make
    # a list of them as textcursors.
    listOnotes = []
    findtc = QTextCursor(doc) # cursor that points to top of document
    findtc = doc.find(NoteFinderRE,findtc)
    while not findtc.isNull():
        # findtc selects "[Footnote key:" now we need to find the closing
        # right bracket, which must be at the end of its line. We will go
        # by text blocks looking for a line that ends like this]
        pqMsgs.rollBar(findtc.anchor()+barBias)
        while True:
            # "drag" to end of line, selecting whole line
            findtc.movePosition(QTextCursor.EndOfBlock,QTextCursor.KeepAnchor)
            if findtc.selectedText().endsWith(u']') :
                break # now selecting whole note
            if findtc.block() == doc.lastBlock() :
                # ran off end of document looking for ...]
                findtc.clearSelection() # just forget this note, it isn't a note
                break # we could tell user, unterminated note. eh.
            else: # there is another line, step to its head and look again
                findtc.movePosition(QTextCursor.NextBlock,QTextCursor.KeepAnchor)
        if findtc.hasSelection() : # we did find the line ending in ]
            listOnotes.append(QTextCursor(findtc))
        findtc = doc.find(NoteFinderRE,findtc) # find next, fail at end of doc

    # Now, listOrefs is all the References and listOnotes is all the Notes,
    # both in sequence by document position. Basically, merge these lists.
    # For each Ref in sequence, find the first Note with a matching key at
    # a higher line number. If there is one, add the matched pair to the db,
    # and delete the note from its list. If there is no match, copy the
    # ref to a list of unmatched refs (because we can't del from the listOrefs
    # inside the loop over it).
    # This is not an MxN process despite appearances, as (a) most refs
    # will find a match, (b) most matches appear quickly and (c) we keep
    # shortening the list of notes.
    listOfOrphanRefs = []
    for reftc in listOrefs:
        hit = False
        refln = refLineNumber(reftc) # note line number for comparison
        for notetc in listOnotes:
            if 0 == reftc.selectedText().compare(keyFromNote(notetc)) and \
            refln < noteLineNumber(notetc) :
                hit = True
                break
        if hit : # a match was found
            addMatchedPair(reftc,notetc)
            listOnotes.remove(notetc)
        else:
            listOfOrphanRefs.append(reftc)
    # All the matches have been made (in heaven?). If there remain any
    # unmatched refs or notes, insert them in the db as well.
    for reftc in listOfOrphanRefs:
        insertUnmatchedRef(reftc)
    for notetc in listOnotes:
        insertUnmatchedNote(notetc)
    TheCountOfUnpairedKeys = len(listOfOrphanRefs)+len(listOnotes)
    # clear the status and progress bar
    pqMsgs.endBar()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# This code implements the Fnote table and its interactions.
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# Implement a concrete table model by subclassing Abstract Table Model.
# The data served is derived from the TheFootnoteList, above.

class myTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super(myTableModel, self).__init__(parent)
        # The header texts for the columns
        self.headerDict = {
            0:"Key", 1:"Class", 2:"Ref line", 3:"Note Line", 4:"Length", 5:"Text"
        }
        # the text alignments for the columns
        self.alignDict = { 0:Qt.AlignCenter, 1: Qt.AlignCenter, 
                           2: Qt.AlignRight, 3: Qt.AlignRight,
                           4: Qt.AlignRight, 5: Qt.AlignLeft }
        # The values for tool/status tips for data and headers
        self.tipDict = { 0: "Actual key text",
                         1: "Assumed class of key for renumbering",
                         2: "Line number of the Reference",
                         3: "First line of the Footnote",
                         4: "Number of lines in the Footnote",
                         5: "Initial text of the Footnote" 
                         }
        # The brushes to painting the background of good and questionable rows
        self.whiteBrush = QBrush(QColor(QString('transparent')))
        self.pinkBrush = QBrush(QColor(QString('lightpink')))
        self.greenBrush = QBrush(QColor(QString('palegreen')))
        # Here save the expansion of one database item for convenient fetching
        self.lastRow = -1
        self.lastTuple = ()
        self.brushForRow = QBrush()

    def columnCount(self,index):
        if index.isValid() : return 0 # we don't have a tree here
        return 6

    def flags(self,index):
        f = Qt.ItemIsEnabled
        #if index.column() ==1 :
            #f |= Qt.ItemIsEditable # column 1 only editable
        return f
    
    def rowCount(self,index):
        if index.isValid() : return 0 # we don't have a tree here
        return len(TheFootnoteList) # initially 0
    
    def headerData(self, col, axis, role):
        if (axis == Qt.Horizontal) and (col >= 0):
            if role == Qt.DisplayRole : # wants actual text
                return QString(self.headerDict[col])
            elif (role == Qt.ToolTipRole) or (role == Qt.StatusTipRole) :
                return QString(self.tipDict[col])
        return QVariant() # we don't do that, whatever it is
    # This method is called whenever the table view wants to know practically
    # anything about the visible aspect of a table cell. The row & column are 
    # in the index, and what it wants to know is expressed by the role.
    def data(self, index, role ):
        # whatever it wants, we need the row data. Get it into self.lastTuple
        if index.row() != self.lastRow :
            # We assume Qt won't ask for any row outside 0..rowCount-1.
            # We TRUST it will go horizontally, hitting a row multiple times,
            # before going on to the next row.
            r = index.row()
            rtc = TheFootnoteList[r]['R']
            ntc = TheFootnoteList[r]['N']
            rln = refLineNumber(rtc)
            nln = noteLineNumber(ntc)
            nll = noteLineLength(ntc) # None if ntc is None
            self.lastTuple = (
                TheFootnoteList[r]['K'], # key as a qstring
                KeyClassNames[TheFootnoteList[r]['C']], # class as qstring
                QString(unicode(rln)) if rtc is not None else QString("?"),
                QString(unicode(nln)) if ntc is not None else QString("?"),
                QString(unicode(nll)),
                textFromNote(ntc)
                )
            self.brushForRow = self.whiteBrush
            if (rtc is None) or (ntc is None):
                self.brushForRow = self.pinkBrush
            elif 10 < nll or 50 < (nln-rln) :
                self.brushForRow = self.greenBrush
        # Now, what was it you wanted?
        if role == Qt.DisplayRole : # wants actual data
            return self.lastTuple[index.column()] # so give it.
        elif (role == Qt.TextAlignmentRole) :
            return self.alignDict[index.column()]
        elif (role == Qt.ToolTipRole) or (role == Qt.StatusTipRole) :
            return QString(self.tipDict[index.column()])
        elif (role == Qt.BackgroundRole) or (role == Qt.BackgroundColorRole):
            return self.brushForRow
        # don't support other roles
        return QVariant()
 
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# This code creates the Fnote panel and implements the other UI widgets.
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# Used during renumbering: given an integer, return an upper- or
# lowercase roman numeral. Cribbed from Mark Pilgrim's "Dive Into Python".
RomanNumeralMap = (('M',  1000),
                   ('CM', 900),
                   ('D',  500),
                   ('CD', 400),
                   ('C',  100),
                   ('XC', 90),
                   ('L',  50),
                   ('XL', 40),
                   ('X',  10),
                   ('IX', 9),
                   ('V',  5),
                   ('IV', 4),
                   ('I',  1))
def toRoman(n,lc):
    """convert integer to Roman numeral"""
    if not (0 < n < 5000):
        raise ValueError, "number out of range (must be 1..4999)"
    if int(n) <> n:
        raise TypError, "decimals can not be converted"
    result = ""
    for numeral, integer in RomanNumeralMap:
        while n >= integer:
            result += numeral
            n -= integer
    qs = QString(result)
    if lc : return qs.toLower()
    return qs
AlphaMap = u'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
def toAlpha(n,lc=False):
    '''convert integer to alpha A..ZZ'''
    if not (0 < n < 17577):
        raise ValueError, "number out of range (must be 1..17577)"
    if int(n) <> n:
        raise TypeError, "decimals can not be converted"
    result = ''
    while True :
        (n,m) = divmod(n-1,26)
        result = AlphaMap[m]+result
        if n == 0 : break
    qs = QString(result)
    if lc : return qs.toLower()
    return qs

    
class fnotePanel(QWidget):
    def __init__(self, parent=None):
        super(fnotePanel, self).__init__(parent)
        # Here we go making a layout. The outer shape is a vbox.
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        # The following things are stacked inside the vbox.
        # 1, the Refresh button, left-justifed in an hbox.
        refreshLayout = QHBoxLayout()
        self.refreshButton = QPushButton("Refresh")
        refreshLayout.addWidget(self.refreshButton,0)
        refreshLayout.addStretch(1) # stretch on right left-aligns the button
        mainLayout.addLayout(refreshLayout)
        self.connect(self.refreshButton, SIGNAL("clicked()"), self.doRefresh)
        # 2, The table of footnotes, represented as a QTableView that displays
        # our myTableModel.
        self.view = QTableView()
        self.view.setCornerButtonEnabled(False)
        self.view.setWordWrap(False)
        self.view.setAlternatingRowColors(False)
        self.view.setSortingEnabled(False)
        mainLayout.addWidget(self.view,1) # It gets all stretch for the panel
        # create the table (empty just now) and display it
        self.table = myTableModel() # 
        self.view.setModel(self.table)
        # Connect the table view's clicked to our clicked slot
        self.connect(self.view, SIGNAL("clicked(QModelIndex)"), self.tableClick)
        # 3, an hbox containing 3 vboxes each containing 2 hboxes... ok, let's
        # start with 6 comboboxes, one for each class.
        self.pickIVX = self.makeStreamMenu(KeyClass_ABC) # initialize both IVX
        self.pickABC = self.makeStreamMenu(KeyClass_ABC) # ..and ABC to A,B
        self.pickivx = self.makeStreamMenu(KeyClass_abc) # similarly
        self.pickabc = self.makeStreamMenu(KeyClass_abc)
        self.pick123 = self.makeStreamMenu(KeyClass_123)
        self.picksym = self.makeStreamMenu()
        # while we are at it let us connect their signals to the methods
        # that enforce their behavior.
        self.connect(self.pickIVX, SIGNAL("activated(int)"),self.IVXpick)
        self.connect(self.pickABC, SIGNAL("activated(int)"),self.ABCpick)
        self.connect(self.pickivx, SIGNAL("activated(int)"),self.ivxpick)
        self.connect(self.pickabc, SIGNAL("activated(int)"),self.abcpick)
        # Now make 6 hboxes each containing a label and the corresponding
        # combobox.
        hbIVX = self.makePair(KeyClassNames[0],self.pickIVX)
        hbABC = self.makePair(KeyClassNames[1],self.pickABC)
        hbivx = self.makePair(KeyClassNames[2],self.pickivx)
        hbabc = self.makePair(KeyClassNames[3],self.pickabc)
        hb123 = self.makePair(KeyClassNames[4],self.pick123)
        hbsym = self.makePair(KeyClassNames[5],self.picksym)
        # Stack up the pairs in three attractive vboxes
        vbIA = self.makeStack(hbABC,hbIVX)
        vbia = self.makeStack(hbabc,hbivx)
        vbns = self.makeStack(hb123,hbsym)
        # Array them across a charming hbox and stick it in our panel
        hbxxx = QHBoxLayout()
        hbxxx.addLayout(vbIA)
        hbxxx.addLayout(vbia)
        hbxxx.addLayout(vbns)
        hbxxx.addStretch(1)
        mainLayout.addLayout(hbxxx)
        # Finally, the action buttons on the bottom in a frame.
        doitgb = QGroupBox("Actions")
        doithb = QHBoxLayout()
        self.renumberButton = QPushButton("Renumber")
        self.moveButton = QPushButton("Move Notes")
        self.asciiButton = QPushButton("ASCII Cvt")
        self.htmlButton = QPushButton("HTML Cvt")
        doithb.addWidget(self.renumberButton,0)
        doithb.addStretch(1)
        doithb.addWidget(self.moveButton)
        doithb.addStretch(1)
        doithb.addWidget(self.asciiButton)
        doithb.addStretch(1)
        doithb.addWidget(self.htmlButton)
        doitgb.setLayout(doithb)
        mainLayout.addWidget(doitgb)
        # and connect the buttons to actions
        self.connect(self.renumberButton, SIGNAL("clicked()"), self.doRenumber)
        self.connect(self.moveButton, SIGNAL("clicked()"), self.doMove)
        self.connect(self.asciiButton, SIGNAL("clicked()"), self.doASCII)
        self.connect(self.htmlButton, SIGNAL("clicked()"), self.doHTML)
        # The renumber streams and a set of lambdas for getting the
        # next number in sequence from them. The lambdas are selected by the
        # value in a stream menu combo box, 0-4 or 5 meaning no-renumber.
        self.streams = [0,0,0,0,0,0]
        self.streamLambdas = [
            lambda s : toRoman(s,False),
            lambda s : toAlpha(s,False),
            lambda s : toRoman(s,True),
            lambda s : toAlpha(s,True),
            lambda s : QString(unicode(s)),
            lambda s : None]
        self.streamMenuList = [
            self.pickIVX,self.pickABC,self.pickivx,
            self.pickabc,self.pick123,self.picksym]
        # Note a count of items over which it is worthwhile to run a 
        # progress bar during renumber, move, etc. Reconsider later: 100? 200?
        self.enoughForABar = 50
    # Convenience function to shorten code when instantiating
    def makeStreamMenu(self,choice=5):
        cb = QComboBox()
        cb.addItems(StreamNames)
        cb.setCurrentIndex(choice)
        return cb
    # Convenience function to shorten code when instantiating
    def makePair(self,qs,cb):
        hb = QHBoxLayout()
        hb.addWidget(QLabel(qs))
        hb.addWidget(cb)
        hb.addStretch(1)
        return hb
    # Convenience function to shorten code when instantiating
    def makeStack(self,pair1,pair2):
        vb = QVBoxLayout()
        vb.addLayout(pair1)
        vb.addLayout(pair2)
        vb.addStretch(1)
        return vb

    # The slot for a click of the Refresh button. Tell the table model we are
    # changing stuff; then call theRealRefresh; the tell table we're good.
    def doRefresh(self):
        self.table.beginResetModel()
        theRealRefresh()
        self.table.endResetModel()
        self.view.resizeColumnsToContents()
    
    # These slots are invoked when a choice is made in the stream popup menu
    # for an ambiguous class, to ensure that contradictory choices aren't made.

    # If the user sets the IVX stream to the same as the ABC stream, or
    # to no-renumber, fine. Otherwise, she is asserting that she has valid
    # IVX footnote keys, in which case ABC needs to be no-renumber.
    def IVXpick(self,pick):
        if (pick != self.pickABC.currentIndex()) or (pick != 5) :
            self.pickABC.setCurrentIndex(5)
    # If the user sets the ABC stream to anything but no-renumber, she is
    # asserting that there are valid ABC keys in which case, keys we have
    # classed as IVX need to use the same stream.
    def ABCpick(self,pick):
        if pick != 5 :
            self.pickIVX.setCurrentIndex(pick)
    # And similarly for lowercase.
    def ivxpick(self,pick):
        if (pick != self.pickabc.currentIndex()) or (pick != 5) :
            self.pickabc.setCurrentIndex(5)
    def abcpick(self,pick):
        if pick != 5 :
            self.pickivx.setCurrentIndex(pick)

    # The slot for a click anywhere in the tableview. If the click is on:
    # * column 0 or 1 (key or class) we jump to the ref line, unless we are on
    #   the ref line in which case we jump to the note line (ping-pong).
    # * column 2 (ref line) we jump to the ref line.
    # * column 3, 4, 5 (note line or note) we jump to the note line.
    # In each case, to "jump" means, set the document cursor to the reftc
    # or the notetc, making the ref or note the current selection.
    def tableClick(self,index):
        r = index.row()
        c = index.column()
        dtc = IMC.editWidget.textCursor()
        rtc = TheFootnoteList[r]['R']
        ntc = TheFootnoteList[r]['N']
        targtc = None
        if c > 2 : # column 3 4 or 5
            targtc = ntc
        elif c == 2 :
            targtc = rtc
        else:  # c == 0 or 1
            dln = dtc.blockNumber()
            rln = refLineNumber(rtc) # None, if rtc is None
            if dln == rln : # True if there is a ref line and we are on it
                targtc = ntc # go to the note
            else: # there isn't a ref line (rtc is None) or there is and we want it
                targtc = rtc
        if targtc is not None:
            IMC.editWidget.setTextCursor(targtc)
    
    # The slots for the main window's docWill/HasChanged signals.
    # Right now, just clear the footnote database, the user can hit
    # refresh when he wants the info. If the refresh proves to be
    # very small performance hit even in a very large book, we could
    # look at calling doRefresh automatically after docHasChanged.
    def docWillChange(self):
        self.table.beginResetModel()
    def docHasChanged(self):
        TheFootnoteList = []
        self.table.endResetModel()

    # Subroutine to check if it is ok to do a major revision such as renumber
    # or move: if there are unpaired keys, display a message and return false.
    def canWeRevise(self,action):
        global TheCountOfUnpairedKeys
        if TheCountOfUnpairedKeys is not 0 :
            pqMsgs.warningMsg(
        "Cannot {0} with orphan notes and anchors".format(action),
        "The count of unpaired anchors and notes is: {0}".format(TheCountOfUnpairedKeys)
                            )
            return False # dinna do it, laddie!
        return True # ok to go ahead
        
    # The slot for the Renumber button. Check to see if any unpaired keys and
    # don't do it if there are any. But if all are matched, go through the
    # database top to bottom (because that is the direction the user expects
    # the number streams to increment). For each key, develop a new key string
    # based on its present class and the stream selection for that class.
    def doRenumber(self):
        global TheFootnoteList
        if not self.canWeRevise(u"Renumber") :
            return
        # If the database is actually empty, just do nothing.
        dbcount = len(TheFootnoteList)
        if dbcount < 1 : return
        # OTOH, if there is significant work to do, start the progress bar.
        if dbcount >= self.enoughForABar : 
            pqMsgs.startBar(dbcount,"Renumbering footnotes...")
        # clear the number streams
        self.streams = [0,0,0,0,0,0]
        # Tell the table model that things are gonna change
        self.docWillChange()
        # create a working cursor and start an undo macro on it.
        worktc = QTextCursor(IMC.editWidget.textCursor())
        worktc.beginEditBlock()
        for i in range(dbcount) : # there's a reason this isn't "for item in..."
            item = TheFootnoteList[i]
            # Note this key's present string value and class number.
            oldkeyqs = item['K']
            oldclass = item['C']
            # Get the renumber stream index for the present class
            renchoice = self.streamMenuList[oldclass].currentIndex()
            # Increment that stream (if no-renumber, increment is harmless)
            self.streams[renchoice] += 1
            # Format the incremented value as a string based on stream choice
            # This produces None if renchoice is 5, no-renumber.
            newkeyqs = self.streamLambdas[renchoice](self.streams[renchoice])
            if newkeyqs is not None: # not no-renumber, so we do it
                # infer the key class of the new key string
                newclass = classOfKey(newkeyqs)
                # ## Replace the key in the note text:
                # First, make a pattern to match the old key. Do it by making
                # a COPY of the old key and appending : to the COPY. We need
                # the colon because the key text might be e.g. "o" or "F".
                targqs = QString(oldkeyqs).append(u':')
                # Cause worktc to select the opening text of the note through
                # the colon, from notetc. Don't select the whole note as we will
                # use QString::replace which replaces every match it finds.
                notetc = item['N']
                worktc.setPosition(notetc.anchor())
                worktc.setPosition(notetc.anchor()+10+targqs.size(),QTextCursor.KeepAnchor)
                # Get that selected text as a QString
                workqs = worktc.selectedText()
                # Find the offset of the old key (s.b. 10 but not anal about spaces)
                targix = workqs.indexOf(targqs,0,Qt.CaseSensitive)
                # Replace the old key text with the new key text
                workqs.replace(targix,oldkeyqs.size(),newkeyqs)
                # put the modified text back in the document, replacing just
                # [Footnote key:. Even this will make Qt mess with the anchor
                # and position of notetc, so set up to recreate that.
                selstart = notetc.anchor()
                selend = notetc.position()-oldkeyqs.size()+newkeyqs.size()
                worktc.insertText(workqs)
                notetc.setPosition(selstart)
                notetc.setPosition(selend,QTextCursor.KeepAnchor)
                # ## Replace the key in the anchor, a simpler job, although
                # we again have to recover the selection
                reftc = item['R']
                selstart = reftc.anchor()
                sellen = newkeyqs.size()
                worktc.setPosition(selstart)
                worktc.setPosition(reftc.position(),QTextCursor.KeepAnchor)
                worktc.insertText(newkeyqs)
                reftc.setPosition(selstart)
                reftc.setPosition(selstart+sellen,QTextCursor.KeepAnchor)
                # Update the database item. The two cursors are already updated.
                # Note that this is Python; "item" is a reference to 
                # TheFootnoteList[i], ergo we are updating the db in place.
                item['K'] = newkeyqs
                item['C'] = newclass
                # end of "newkeyqs is not None"
            if dbcount >= self.enoughForABar and 0 == (i & 3):
                pqMsgs.rollBar(dbcount - i)
            # end of "for i in range(dbcount)"
        # Clean up:
        worktc.endEditBlock()  # End the undo macro
        self.docHasChanged()   # tell the table the data has stabilized
        if dbcount > self.enoughForABar :
            pqMsgs.endBar()    # clear the progress bar

    # The slot for the Move button. Check to see if any unpaired keys and
    # don't do it if there are any. But if all are matched, first find all
    # footnote sections in the document and make a list of them in the form
    # of textcursors. Get user permission, showing section count as a means
    # of validating markup, then move each note that is not in a section,
    # into the section next below it. Update the note cursors in the db.
    def doMove(self):
        global TheFootnoteList
        if not self.canWeRevise(u"Move Notes to /F..F/") :
            return
        # If the database is actually empty, just do nothing.
        dbcount = len(TheFootnoteList)
        if dbcount < 1 : return
        # Create a working text cursor.
        worktc = QTextCursor(IMC.editWidget.textCursor())
        # Search the whole document and find the /F..F/ sections. We could look
        # for lines starting /F and then after finding one, for the F/ line, but
        # the logic gets messy when the user might have forgotten or miscoded
        # the F/. So we use a regex that will cap(0) the entire section. We are
        # not being Mr. Nice Guy and allowing \s* spaces either, it has to be
        # zackly \n/F\n.*\nF/\n.
        sectRegex = QRegExp('\\n/F.*\\nF/\\n')
        sectRegex.setMinimal(True) # minimal match for the .* above
        sectRegex.setCaseSensitivity(Qt.CaseSensitive)
        wholeDocQs = IMC.editWidget.toPlainText() # whole doc as qstring
        sectList = []
        j = sectRegex.indexIn(wholeDocQs,0)
        while j > -1:
            # initialize text cursors to record the start and end positions
            # of each section. Note, cursors point between characters:
            #          sectcA----v
            #          sectcI----v         sectcB---v
            # ... \2029 / F \2029 ..whatever.. \2029 F / \2029
            # Notes are inserted at sectcI which is moved ahead each time. Qt
            # takes care of updating sectcB and other cursors on inserts.
            # The line number of sectcA is that of the first line after /F,
            # and that of sectcB is that of the F/ for comparison.
            sectcA = QTextCursor(worktc)
            sectcA.setPosition(j+4)
            sectcB = QTextCursor(worktc)
            sectcB.setPosition(j+sectRegex.matchedLength()-3)
            sectcI = QTextCursor(sectcA)
            sectList.append( (sectcA,sectcI,sectcB) )
            j = sectRegex.indexIn(wholeDocQs,j+1)
        # Let wholeDocQs go out of scope just in case it is an actual copy
        # of the document. (Should just be a const reference but who knows?)
        wholeDocQs = QString()
        # Did we in fact find any footnote sections?
        if len(sectList) == 0:
            pqMsgs.warningMsg(u"Found no /F..F/ footnote sections.")
            return
        # Since this is a big deal, and /F is easy to mis-code, let's show
        # the count found and get approval.
        if not pqMsgs.okCancelMsg(
            u"Found {0} footnote sections".format(len(sectList)),
            "OK to proceed with the move?") :
            return
        # Right, we're gonna do stuff. If there is significant work to do,
        # start the progress bar.
        if dbcount >= self.enoughForABar : 
            pqMsgs.startBar(dbcount,"Moving Notes to /F..F/ sections")
        # Tell the table model that things are gonna change
        self.docWillChange()
        # Start an undo macro on the working cursor.
        worktc = QTextCursor(IMC.editWidget.textCursor())
        worktc.beginEditBlock()
        # loop over all notes.
        for i in range(dbcount):
            notetc = TheFootnoteList[i]['N']
            nln = noteLineNumber(notetc)
            # Look for the first section whose last line is below nln
            for s in range(len(sectList)):
                (sectcA,sectcI,sectcB) = sectList[s]
                if nln >= refLineNumber(sectcB):
                    # this note starts below this section
                    continue
                # this note starts above the end of this section,
                if nln >= refLineNumber(sectcA):
                    # this note is inside this section already
                    break
                # this note is above and not within the current section,
                # so do the move. Start saving the length of the note as
                # currently known.
                notelen = notetc.position() - notetc.anchor()
                # Extend the note selection over the \2029 after the right bracket.
                notetc.movePosition(QTextCursor.Right,1,QTextCursor.KeepAnchor)
                # point our worktc at the insertion point in this section
                worktc.setPosition(sectcI.position())
                # copy the note text inserting it in the section
                worktc.insertText(notetc.selectedText())
                # save the ending position as the new position of sectcI -- the
                # next inserted note goes there
                sectcI.setPosition(worktc.position())
                # clear the old note text. Have to do this using worktc for
                # the undo-redo macro to record it. When the text is removed,
                # Qt adjusts all cursors that point below it, including sectcI.
                worktc.setPosition(notetc.anchor())
                worktc.setPosition(notetc.position(),QTextCursor.KeepAnchor)
                worktc.removeSelectedText()
                # reset notetc to point to the new note location
                notepos = sectcI.position()-notelen-1
                notetc.setPosition(notepos)
                notetc.setPosition(notepos+notelen,QTextCursor.KeepAnchor)
                break # all done scanning sectList for this note
                # end of "for s in range(len(sectList))"
            if dbcount >= self.enoughForABar and 0 == (i & 3) :
                pqMsgs.rollBar(dbcount - i)
            # end of "for i in range(dbcount)"
        # Clean up:
        worktc.endEditBlock()  # End the undo macro
        self.docHasChanged()   # tell the table the data has stabilized
        if dbcount > self.enoughForABar :
            pqMsgs.endBar()    # clear the progress bar


    # The slot for the HTML button. Make sure the db is clean and there is work
    # to do. Then go through each item and update as follows:
    # Around the reference put:
    # <a id='FA_key' name='FA_key' href='#FN_key' class='fnanchor'>[key]</a>
    # Replace "[Footnote key:" with
    # <div class='footnote' id='FN_key' name='FN_key'>\n\n
    # <span class="fnlabel"><a href='FA_key'>[key]</a></span> text..
    # Replace the final ] with \n\n</div>
    # The idea is that the HTML conversion in pqFlow will see the  \n\n
    # and insert <p> and </p> as usual.
    # We work the list from the bottom up because of nested references.
    # Going top-down, we would rewrite a Note containing a Reference, and
    # that unavoidably messes up the reftc pointing to the nested reference.
    # Going bottom-up, we rewrite the nested Reference before the Note that
    # contains it is rewritten.
    
    def doHTML(self):
        global TheFootnoteList
        if not self.canWeRevise(u"Convert Footnotes to HTML") :
            return
        # If the database is actually empty, just do nothing.
        dbcount = len(TheFootnoteList)
        if dbcount < 1 : return
        # Just in case the user had a spastic twitch and clicked in error,
        if not pqMsgs.okCancelMsg(
            "Going to convert {0} footnotes to HTML".format(dbcount),
            "(Symbol class keys will be skipped)"):
            return
        # Set up a boilerplate string for the Reference replacements.
        # We'll use QString.replace to install the key over $#$
        keyPattern = QString(u"$#$")
        refPattern = QString(u"<a id='FA_$#$' name='FA_$#$' href='#FN_$#$' class='fnanchor'>[$#$]</a>")
        # Set up a regex pattern to recognize [Footnote key:, being forgiving
        # about extra spaces and absorbing spaces after the colon.
        fntPattern = QString(u"\[Footnote\s+$#$\s*:\s*")
        fntRE = QRegExp()
        # Set up a replacement boilerplate for [Footnote key:
        fntRep = QString(u"<div class='footnote' id='FN_$#$' name='FN_$#$'>\u2029\u2029<span class='fnlabel'><a href='FA_$#$>[$#$]</a></span>")
        # Make a working textcursor, start the undo macro, advise the table
        worktc = QTextCursor(IMC.editWidget.textCursor())
        worktc.beginEditBlock()
        self.docWillChange()
        if dbcount >= self.enoughForABar : 
            pqMsgs.startBar(dbcount,"Converting notes to HTML...")
        for i in reversed(range(dbcount)):
            item = TheFootnoteList[i]
            # Don't even try to convert symbol-class keys
            if item['C'] == KeyClass_sym :
                continue
            keyqs = item['K']
            reftc = item['R']
            # note the start position of the anchor, less 1 to include the [
            refstart = reftc.anchor() - 1
            # note the end position, plus 1 for the ]
            refend = reftc.position()+1
            # Copy the ref boilerplate and install the key in it
            refqs = QString(refPattern).replace(keyPattern,keyqs,Qt.CaseSensitive)
            dbg = unicode(refqs)
            # Replace the reference text, using the work cursor.
            worktc.setPosition(refstart)
            worktc.setPosition(refend,QTextCursor.KeepAnchor)
            worktc.insertText(refqs)
            # That also repositioned reftc to the end of the string, bring
            # it back to the beginning again, but now with no selection.
            reftc.setPosition(refstart)
            # Note the start position of the note
            notetc = item['N']
            notestart = notetc.anchor()
            # Note its end position, which includes the closing ]
            noteend = notetc.position()
            # Copy the note boilerplates and install the key in them.
            notepat = QString(fntPattern).replace(keyPattern,keyqs,Qt.CaseSensitive)
            dbg = unicode(notepat)
            noteqs = QString(fntRep).replace(keyPattern,keyqs,Qt.CaseSensitive)
            dbg = unicode(noteqs)
            # Point the work cursor at the note.
            worktc.setPosition(notestart)
            worktc.setPosition(noteend,QTextCursor.KeepAnchor)
            # get the note as a string, truncate the closing ] and put it back.
            oldnote = worktc.selectedText()
            oldnote.chop(1)
            oldnote.append(QString(u"\u2029\u2029</div>"))
            dbg = unicode(oldnote)
            worktc.insertText(oldnote) # worktc now positioned after note
            # use the note string to recognize the length of [Footnote key:sp
            fntRE.setPattern(notepat)
            dbg = fntRE.isValid()
            dbg = unicode(fntRE.pattern())
            j = fntRE.indexIn(oldnote) # assert j==0
            j = fntRE.cap(0).size() # size of the target portion
            # set the work cursor to select just that, and replace it.
            worktc.setPosition(notestart)
            worktc.setPosition(notestart+j,QTextCursor.KeepAnchor)
            worktc.insertText(noteqs)
            # reset notetc to the start of the note, but with no selection
            notetc.setPosition(notestart)
            
            if dbcount >= self.enoughForABar and 0 == (i & 3):
                pqMsgs.rollBar(dbcount - i)
            # end of "for i in range(dbcount)"
        # Clean up:
        worktc.endEditBlock()  # End the undo macro
        self.docHasChanged()   # tell the table the data has stabilized
        if dbcount > self.enoughForABar :
            pqMsgs.endBar()    # clear the progress bar
        
 
    # The slot for the ASCII button. Make sure the db is clean and there is work
    # to do. Then go through each item and note the longest string for each
    # footnote class. Leaving Refs along, update all Notes as follows:
    # Replace "[Footnote key:" with
    # /Q F:2 L:max+5 R:2\n  [key]
    # where max is the width of the widest key of this class, and 5 allows for
    # a two-space indent plus the [] and a space.
    # Replace the final ] with \nQ/\n
    # The idea is to change a footnote into a block quote with exdented [key]
    
    def doASCII(self):
        global TheFootnoteList
        if not self.canWeRevise(u"Convert Footnotes to /Q..Q/") :
            return
        # If the database is actually empty, just do nothing.
        dbcount = len(TheFootnoteList)
        if dbcount < 1 : return
        # Just in case the user had a spastic twitch and clicked in error,
        if not pqMsgs.okCancelMsg(
            "Going to convert {0} footnotes to /Q..Q/".format(dbcount),
            ""):
            return
        # Find the widest key string for each class.
        maxwids = [0,0,0,0,0,0]
        for item in TheFootnoteList:
            maxwids[item['C']] = max(maxwids[item['C']],item['K'].size())
        # Set up a boilerplate string for the replacements.
        keyPattern = QString(u"$#$")
        # Set up a regex pattern to recognize [Footnote key:, being forgiving
        # about extra spaces and absorbing spaces after the colon.
        fntPattern = QString(u"\[Footnote\s+$#$\s*:\s*")
        fntRE = QRegExp()
        # Set up a replacement boilerplate for [Footnote key:
        fntRep = QString(u"/Q F:2 L:### R:2\u2029  [$#$] ")
        # Make a working textcursor, start the undo macro, advise the table
        worktc = QTextCursor(IMC.editWidget.textCursor())
        worktc.beginEditBlock()
        self.docWillChange()
        if dbcount >= self.enoughForABar : 
            pqMsgs.startBar(dbcount,"Converting notes to ASCII...")
        for i in range(dbcount):
            item = TheFootnoteList[i]
            keyqs = item['K']
            # Note the start position of the note
            notetc = item['N']
            notestart = notetc.anchor()
            # Note its end position, which includes the closing ]
            noteend = notetc.position()
            # Copy the note boilerplates and install the key in them.
            notepat = QString(fntPattern).replace(keyPattern,keyqs,Qt.CaseSensitive)
            dbg = unicode(notepat)
            noteqs = QString(fntRep)
            noteqs.replace(keyPattern,keyqs,Qt.CaseSensitive)
            noteqs.replace(QString(u'###'),QString(unicode(5+maxwids[item['C']])))
            dbg = unicode(noteqs)
            # Point the work cursor at the note.
            worktc.setPosition(notestart)
            worktc.setPosition(noteend,QTextCursor.KeepAnchor)
            # get the note as a string, truncate the closing ], add the 
            # newline Q/, and put it back.
            oldnote = worktc.selectedText()
            oldnote.chop(1)
            oldnote.append(QString(u'\u2029Q/\u2029'))
            dbg = unicode(oldnote)
            worktc.insertText(oldnote) # worktc now positioned after note
            # use the note string to recognize the length of [Footnote key:sp
            fntRE.setPattern(notepat)
            dbg = fntRE.isValid()
            dbg = unicode(fntRE.pattern())
            j = fntRE.indexIn(oldnote) # assert j==0
            j = fntRE.cap(0).size() # size of the target portion
            # set the work cursor to select just that, and replace it.
            worktc.setPosition(notestart)
            worktc.setPosition(notestart+j,QTextCursor.KeepAnchor)
            worktc.insertText(noteqs)
            # reset notetc to the start of the note, but with no selection
            notetc.setPosition(notestart)
            
            if dbcount >= self.enoughForABar and 0 == (i & 3):
                pqMsgs.rollBar(dbcount - i)
            # end of "for i in range(dbcount)"
        # Clean up:
        worktc.endEditBlock()  # End the undo macro
        self.docHasChanged()   # tell the table the data has stabilized
        if dbcount > self.enoughForABar :
            pqMsgs.endBar()    # clear the progress bar
       
        
if __name__ == "__main__":
    import sys
    from PyQt4.QtCore import (Qt,QFile,QIODevice,QTextStream,QSettings)
    from PyQt4.QtGui import (QApplication,QPlainTextEdit,QFileDialog,QMainWindow)
    import pqIMC
    app = QApplication(sys.argv) # create an app
    IMC = pqIMC.tricorder() # set up a fake IMC for unit test
    IMC.fontFamily = QString("Courier")
    import pqMsgs
    pqMsgs.IMC = IMC
    IMC.editWidget = QPlainTextEdit()
    IMC.editWidget.setFont(pqMsgs.getMonoFont())
    IMC.settings = QSettings()
    widj = fnotePanel()
    MW = QMainWindow()
    MW.setCentralWidget(widj)
    pqMsgs.makeBarIn(MW.statusBar())
    MW.show()
    utqs = QString('''
This is text[A] with footnotes[2].
This is another[DCCCCLXXXXVIII] reference.
This is another[q] reference.
/F
F/
A lame symbol[\u00a7] reference.
Ref to unmatched key[]
/F
this gets no notes
F/
[Footnote A: footnote A which
extends onto 
three lines]
[Footnot zz: orphan note]
[Footnote 2: footnote 2 which has[A] a nested note]
[Footnote A: nested ref in note 2]
[Footnote DCCCCLXXXXVIII: footnote DCCCCLXXXXVIII]
[Footnote q: footnote q]
[Footnote \u00a7: footnote symbol]

/F
F/

    ''')
    IMC.editWidget.setPlainText(utqs)
    IMC.mainWindow = MW
    IMC.editWidget.show()
    app.exec_()