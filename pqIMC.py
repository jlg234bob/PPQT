# These imports move Python 2.x almost to Python 3.
# They must precede anything except #comments, including even the docstring
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

__version__ = "1.3.0"
__author__  = "David Cortesi"
__copyright__ = "Copyright 2011, 2012, 2013 David Cortesi"
__maintainer__ = "David Cortesi"
__email__ = "tallforasmurf@yahoo.com"
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
How, in a multi-module Python source, do you give different modules
references to objects created in other modules? Also how do you share
constant values that should be defined in one place, as with a C header?
This is our answer, the Inter Module Communicator. Just an object into
which we stuff every attribute that needs to be used from more than
one module. Might be a kludge, might be very clever.

The ppqt module stuffs a reference to IMC into every module it imports,
thus they all refer to the one instance.
'''
from PyQt4.QtCore import (Qt,QChar,QSysInfo,PYQT_VERSION_STR,QT_VERSION_STR)
#
# Stupid star trek reference here.
#
class tricorder():
    def __init__(self):

        # Controls on the edit syntax hiliter, queried in the editor and
        # set by the Main window View menu actions:
        self.scannoHiliteSwitch = False
        self.spellingHiliteSwitch = False

        # Document/file status variables: more than a simple "dirty" flag.
        # Just a brute count of calls to the textChanged signal slot.
        self.editCounter = 0
        # needSpellCheck when a word census has been done, or when a
        # different main dictionary is selected. Cleared when a spellcheck is
        # done, e.g. from the Refresh button in the Word panel.
        self.needSpellCheck = False
        # Stale census has two bits:
        self.staleCensusLoaded = 0x02 # census was stale as of File>Load
        self.staleCensusAcquired = 0x01 # doc changed since last census
        self.staleCensus = 0x00
        # needMetadataSave is a bit set of:
        self.goodwordsChanged = 0x01
        self.notePanelChanged = 0x02
        self.pagePanelChanged = 0x04
        self.bookmarksChanged = 0x08
        self.wordlistsChanged = 0x10
        self.propertyChanged = 0x20
        # a word is added to goodwords, or we do a spellcheck or a word census.
        # Cleared on Save, Save-As or New.
        self.needMetadataSave = 0x00
        # Note that the equivalent switch "needDocumentSave" is kept by the
        # QTextDocument as IMC.editWidget.document().isModified() -- we rely on
        # that because it tracks the undo/redo actions and knows if the user
        # has backed out all changes or not.

        # Other document properties read/written in metadata
        self.bookSaveEncoding = None # encoding for saves: UTF-8 or ISO-8859-1
        self.documentHash = b'' # hash of document contents
        self.metaHash = b'' # hash as read from the .meta file
        self.bookMainDict = None # QString of preferred main dict for this book

        # These values are used in forming the word classification
        # flag for words in the word census. Prepared in the census
        # in pqEdit, referenced in pqWord.
        self.WordHasUpper = 0x01
        self.WordHasLower = 0x02
        self.WordHasDigit = 0x04
        self.WordHasHyphen = 0x08
        self.WordHasApostrophe = 0x10
        self.WordMisspelt = 0x80

        # These values are used to encode folio controls for the
        # Page/folio table. Initialized in pqEdit when opening a new file,
        # used in pqWord and (eventually) in html conversion.
        self.FolioFormatArabic = 0x00
        self.FolioFormatUCRom = 0x01
        self.FolioFormatLCRom = 0x02
        self.FolioFormatSame = 0x03 # the "ditto" format
        self.FolioRuleAdd1 = 0x00
        self.FolioRuleSet = 0x01
        self.FolioRuleSkip = 0x02

        # Pointers initialized in ppqt, filled in in pqEdit,
        # and referenced everywhere else
        self.settings = None # QSettings for global save/restore app values
        self.appBasePath = None # path to the our dist folder for extras, dict, fonts
        self.dictPath = None # path to folder where we look for dictionaries
        self.scannoList = None # list loaded from a scannos file for hiliting
        self.goodWordList = None # good words
        self.badWordList = None # bad words
        self.wordCensus = None # census of words (tokens actually)
        self.charCensus = None # census of characters
        self.pageTable = None # list of page separators
        self.currentImageNumber = None # qstring e.g. "002" of png file
        self.editWidget = None # main QPlainTextEdit set up in pqMain
        self.spellCheck = None # spellcheck object from pqSpell
        self.mainWindow = None # ref to main window

        # Pointers initialized in pqMain to various major objects
        self.bookPath = None # absolute path to book file
        self.bookDirPath = None # absolute path to book directory
        self.bookType = None # book file suffix used to detect .hmt(l)
        self.defaultFontFamily = None # name of preferred font, usually 'Liberation Mono'
        self.fontFamily = None # last-chosen font
        self.fontSize = 12 # last-chosen font size in Edit panel
        self.pngPanel = None # ref to Pngs panel
        self.notesEditor = None # ref to Notes panel
        self.findPanel = None # ref to Find panel
        self.statusBar = None # ref to status bar of main window
        self.progressBar = None # ref to progress bar in status bar

        # constant value for the line-delimiter used by QPlainTextEdit
        self.QtLineDelim = QChar(0x2029)
        # constant value for the zero-width-non-joiner used as a marker in reflow
        self.ZWNJ = QChar(0x200C)

        # Keystrokes checked by editor and other panels that monitor KeyEvent signals.
        # In rough order of frequency of use, we support:
        # ^g and ^G, search again forward/backward,
        # ^f start search,
        # ^t and ^T replace and search forward/backward,
        # ^1-9 bookmarks
        # ^F start search with selection
        # ^= replace,
        # ^-alt-1-9 set bookmarks
        # ^+ and ^- for zoom in/out
        # ctl-plus can also appear as ctl-shft-equal and ctl-sht-plus!
        # ^l and ^-alt-l, ^p and ^-alt-p for the Notes panel
        # Define these in a way easy to check in a keyEvent slot, and also put
        # them in python lists for quick lookup.
        self.keypadDeModifier = int(0xffffffff ^ Qt.KeypadModifier)
        self.ctl_G = Qt.ControlModifier | Qt.Key_G
        self.ctl_shft_G = Qt.ShiftModifier | self.ctl_G
        self.ctl_F = Qt.ControlModifier | Qt.Key_F
        self.ctl_shft_F = Qt.ShiftModifier | self.ctl_F
        self.ctl_T = Qt.ControlModifier | Qt.Key_T
        self.ctl_shft_T = Qt.ShiftModifier | self.ctl_T
        self.ctl_1 = Qt.ControlModifier | Qt.Key_1
        self.ctl_2 = Qt.ControlModifier | Qt.Key_2
        self.ctl_3 = Qt.ControlModifier | Qt.Key_3
        self.ctl_4 = Qt.ControlModifier | Qt.Key_4
        self.ctl_5 = Qt.ControlModifier | Qt.Key_5
        self.ctl_6 = Qt.ControlModifier | Qt.Key_6
        self.ctl_7 = Qt.ControlModifier | Qt.Key_7
        self.ctl_8 = Qt.ControlModifier | Qt.Key_8
        self.ctl_9 = Qt.ControlModifier | Qt.Key_9
        self.ctl_shft_1 = Qt.ShiftModifier | self.ctl_1
        self.ctl_shft_2 = Qt.ShiftModifier | self.ctl_2
        self.ctl_shft_3 = Qt.ShiftModifier | self.ctl_3
        self.ctl_shft_4 = Qt.ShiftModifier | self.ctl_4
        self.ctl_shft_5 = Qt.ShiftModifier | self.ctl_5
        self.ctl_shft_6 = Qt.ShiftModifier | self.ctl_6
        self.ctl_shft_7 = Qt.ShiftModifier | self.ctl_7
        self.ctl_shft_8 = Qt.ShiftModifier | self.ctl_8
        self.ctl_shft_9 = Qt.ShiftModifier | self.ctl_9
        self.ctl_alt_1 = Qt.AltModifier | self.ctl_1
        self.ctl_alt_2 = Qt.AltModifier | self.ctl_2
        self.ctl_alt_3 = Qt.AltModifier | self.ctl_3
        self.ctl_alt_4 = Qt.AltModifier | self.ctl_4
        self.ctl_alt_5 = Qt.AltModifier | self.ctl_5
        self.ctl_alt_6 = Qt.AltModifier | self.ctl_6
        self.ctl_alt_7 = Qt.AltModifier | self.ctl_7
        self.ctl_alt_8 = Qt.AltModifier | self.ctl_8
        self.ctl_alt_9 = Qt.AltModifier | self.ctl_9
        self.ctl_minus = Qt.ControlModifier | Qt.Key_Minus
        self.ctl_equal = Qt.ControlModifier | Qt.Key_Equal
        self.ctl_plus = Qt.ControlModifier | Qt.Key_Plus
        self.ctl_shft_equal = Qt.ShiftModifier | self.ctl_equal
        self.ctl_shft_plus = Qt.ShiftModifier | self.ctl_plus
        self.ctl_M = Qt.ControlModifier | Qt.Key_M
        self.ctl_alt_M = Qt.AltModifier | self.ctl_M
        self.ctl_L = Qt.ControlModifier | Qt.Key_L
        self.ctl_alt_L = Qt.AltModifier | self.ctl_L
        self.ctl_P = Qt.ControlModifier | Qt.Key_P
        self.ctl_alt_P = Qt.AltModifier | self.ctl_P
        self.ctl_Left = Qt.ControlModifier | Qt.Key_Left
        self.ctl_left_pad = self.ctl_Left | Qt.KeypadModifier
        self.ctl_LBracket = Qt.ControlModifier | Qt.Key_BracketLeft
        self.ctl_B = Qt.ControlModifier | Qt.Key_B
        self.keysOfInterest = [
                self.ctl_G, self.ctl_shft_G, self.ctl_F, self.ctl_shft_F,
                self.ctl_T, self.ctl_shft_T, self.ctl_equal,
                self.ctl_1, self.ctl_2, self.ctl_3, self.ctl_4, self.ctl_5,
                self.ctl_6, self.ctl_7, self.ctl_8, self.ctl_9,
                self.ctl_shft_1, self.ctl_shft_2, self.ctl_shft_3,
                self.ctl_shft_4, self.ctl_shft_5, self.ctl_shft_6,
                self.ctl_shft_7, self.ctl_shft_8, self.ctl_shft_9,
                self.ctl_alt_1, self.ctl_alt_2, self.ctl_alt_3,
                self.ctl_alt_4,  self.ctl_alt_5,  self.ctl_alt_6,
                self.ctl_alt_7, self.ctl_alt_8,  self.ctl_alt_9,
                self.ctl_minus, self.ctl_plus, self.ctl_shft_equal,
                self.ctl_shft_plus,
                self.ctl_M,self.ctl_alt_M,self.ctl_P,self.ctl_alt_P]
        self.backKeys = [self.ctl_B, self.ctl_Left, self.ctl_LBracket, self.ctl_left_pad]
        self.zoomKeys = [self.ctl_minus, self.ctl_plus,
                         self.ctl_shft_equal, self.ctl_shft_plus]
        self.findKeys = [self.ctl_G, self.ctl_shft_G, self.ctl_F, self.ctl_shft_F,
                        self.ctl_T, self.ctl_equal, self.ctl_shft_T]
        self.markKeys = [self.ctl_1, self.ctl_2, self.ctl_3, self.ctl_4, self.ctl_5,
                self.ctl_6, self.ctl_7, self.ctl_8, self.ctl_9 ]
        self.markSetKeys = [self.ctl_alt_1, self.ctl_alt_2, self.ctl_alt_3,
                self.ctl_alt_4,  self.ctl_alt_5,  self.ctl_alt_6,  self.ctl_alt_7,
                self.ctl_alt_8,  self.ctl_alt_9 ]
        self.markShiftKeys = [self.ctl_shft_1, self.ctl_shft_2, self.ctl_shft_3,
                self.ctl_shft_4, self.ctl_shft_5, self.ctl_shft_6,
                self.ctl_shft_7, self.ctl_shft_8, self.ctl_shft_9 ]

        # A list of the 252 Named Entities of HTML 4. The names are indexed
        # by the unicode characters they translate. To complete an entity
        # prepend & and append ;, thus quot -> &quot; (This list was lifted from
        # http://en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references
        # and processed into this form using regex changes in BBEdit.)
        self.namedEntityDict = {
u'\u0022' : u'quot', # quotation mark (= APL quote)
u'\u0026' : u'amp', # ampersand
u'\u0027' : u'apos', # apostrophe (= apostrophe-quote); see below
u'\u003C' : u'lt', # less-than sign
u'\u003E' : u'gt', # greater-than sign
u'\u00A0' : u'nbsp', # no-break space (= non-breaking space)[d]
u'\u00A1' : u'iexcl', # inverted exclamation mark
u'\u00A2' : u'cent', # cent sign
u'\u00A3' : u'pound', # pound sign
u'\u00A4' : u'curren', # currency sign
u'\u00A5' : u'yen', # yen sign (= yuan sign)
u'\u00A6' : u'brvbar', # broken bar (= broken vertical bar)
u'\u00A7' : u'sect', # section sign
u'\u00A8' : u'uml', # diaeresis (= spacing diaeresis); see Germanic umlaut
u'\u00A9' : u'copy', # copyright symbol
u'\u00AA' : u'ordf', # feminine ordinal indicator
u'\u00AB' : u'laquo', # left-pointing double angle quotation mark (= left pointing guillemet)
u'\u00AC' : u'not', # not sign
u'\u00AD' : u'shy', # soft hyphen (= discretionary hyphen)
u'\u00AE' : u'reg', # registered sign ( = registered trademark symbol)
u'\u00AF' : u'macr', # macron (= spacing macron = overline = APL overbar)
u'\u00B0' : u'deg', # degree symbol
u'\u00B1' : u'plusmn', # plus-minus sign (= plus-or-minus sign)
u'\u00B2' : u'sup2', # superscript two (= superscript digit two = squared)
u'\u00B3' : u'sup3', # superscript three (= superscript digit three = cubed)
u'\u00B4' : u'acute', # acute accent (= spacing acute)
u'\u00B5' : u'micro', # micro sign
u'\u00B6' : u'para', # pilcrow sign ( = paragraph sign)
u'\u00B7' : u'middot', # middle dot (= Georgian comma = Greek middle dot)
u'\u00B8' : u'cedil', # cedilla (= spacing cedilla)
u'\u00B9' : u'sup1', # superscript one (= superscript digit one)
u'\u00BA' : u'ordm', # masculine ordinal indicator
u'\u00BB' : u'raquo', # right-pointing double angle quotation mark (= right pointing guillemet)
u'\u00BC' : u'frac14', # vulgar fraction one quarter (= fraction one quarter)
u'\u00BD' : u'frac12', # vulgar fraction one half (= fraction one half)
u'\u00BE' : u'frac34', # vulgar fraction three quarters (= fraction three quarters)
u'\u00BF' : u'iquest', # inverted question mark (= turned question mark)
u'\u00C0' : u'Agrave', # Latin capital letter A with grave accent (= Latin capital letter A grave)
u'\u00C1' : u'Aacute', # Latin capital letter A with acute accent
u'\u00C2' : u'Acirc', # Latin capital letter A with circumflex
u'\u00C3' : u'Atilde', # Latin capital letter A with tilde
u'\u00C4' : u'Auml', # Latin capital letter A with diaeresis
u'\u00C5' : u'Aring', # Latin capital letter A with ring above (= Latin capital letter A ring)
u'\u00C6' : u'AElig', # Latin capital letter AE (= Latin capital ligature AE)
u'\u00C7' : u'Ccedil', # Latin capital letter C with cedilla
u'\u00C8' : u'Egrave', # Latin capital letter E with grave accent
u'\u00C9' : u'Eacute', # Latin capital letter E with acute accent
u'\u00CA' : u'Ecirc', # Latin capital letter E with circumflex
u'\u00CB' : u'Euml', # Latin capital letter E with diaeresis
u'\u00CC' : u'Igrave', # Latin capital letter I with grave accent
u'\u00CD' : u'Iacute', # Latin capital letter I with acute accent
u'\u00CE' : u'Icirc', # Latin capital letter I with circumflex
u'\u00CF' : u'Iuml', # Latin capital letter I with diaeresis
u'\u00D0' : u'ETH', # Latin capital letter Eth
u'\u00D1' : u'Ntilde', # Latin capital letter N with tilde
u'\u00D2' : u'Ograve', # Latin capital letter O with grave accent
u'\u00D3' : u'Oacute', # Latin capital letter O with acute accent
u'\u00D4' : u'Ocirc', # Latin capital letter O with circumflex
u'\u00D5' : u'Otilde', # Latin capital letter O with tilde
u'\u00D6' : u'Ouml', # Latin capital letter O with diaeresis
u'\u00D7' : u'times', # multiplication sign
u'\u00D8' : u'Oslash', # Latin capital letter O with stroke (= Latin capital letter O slash)
u'\u00D9' : u'Ugrave', # Latin capital letter U with grave accent
u'\u00DA' : u'Uacute', # Latin capital letter U with acute accent
u'\u00DB' : u'Ucirc', # Latin capital letter U with circumflex
u'\u00DC' : u'Uuml', # Latin capital letter U with diaeresis
u'\u00DD' : u'Yacute', # Latin capital letter Y with acute accent
u'\u00DE' : u'THORN', # Latin capital letter THORN
u'\u00DF' : u'szlig', # Latin small letter sharp s (= ess-zed); see German Eszett
u'\u00E0' : u'agrave', # Latin small letter a with grave accent
u'\u00E1' : u'aacute', # Latin small letter a with acute accent
u'\u00E2' : u'acirc', # Latin small letter a with circumflex
u'\u00E3' : u'atilde', # Latin small letter a with tilde
u'\u00E4' : u'auml', # Latin small letter a with diaeresis
u'\u00E5' : u'aring', # Latin small letter a with ring above
u'\u00E6' : u'aelig', # Latin small letter ae (= Latin small ligature ae)
u'\u00E7' : u'ccedil', # Latin small letter c with cedilla
u'\u00E8' : u'egrave', # Latin small letter e with grave accent
u'\u00E9' : u'eacute', # Latin small letter e with acute accent
u'\u00EA' : u'ecirc', # Latin small letter e with circumflex
u'\u00EB' : u'euml', # Latin small letter e with diaeresis
u'\u00EC' : u'igrave', # Latin small letter i with grave accent
u'\u00ED' : u'iacute', # Latin small letter i with acute accent
u'\u00EE' : u'icirc', # Latin small letter i with circumflex
u'\u00EF' : u'iuml', # Latin small letter i with diaeresis
u'\u00F0' : u'eth', # Latin small letter eth
u'\u00F1' : u'ntilde', # Latin small letter n with tilde
u'\u00F2' : u'ograve', # Latin small letter o with grave accent
u'\u00F3' : u'oacute', # Latin small letter o with acute accent
u'\u00F4' : u'ocirc', # Latin small letter o with circumflex
u'\u00F5' : u'otilde', # Latin small letter o with tilde
u'\u00F6' : u'ouml', # Latin small letter o with diaeresis
u'\u00F7' : u'divide', # division sign (= obelus)
u'\u00F8' : u'oslash', # Latin small letter o with stroke (= Latin small letter o slash)
u'\u00F9' : u'ugrave', # Latin small letter u with grave accent
u'\u00FA' : u'uacute', # Latin small letter u with acute accent
u'\u00FB' : u'ucirc', # Latin small letter u with circumflex
u'\u00FC' : u'uuml', # Latin small letter u with diaeresis
u'\u00FD' : u'yacute', # Latin small letter y with acute accent
u'\u00FE' : u'thorn', # Latin small letter thorn
u'\u00FF' : u'yuml', # Latin small letter y with diaeresis
u'\u0152' : u'OElig', # Latin capital ligature oe[e]
u'\u0153' : u'oelig', # Latin small ligature oe[e]
u'\u0160' : u'Scaron', # Latin capital letter s with caron
u'\u0161' : u'scaron', # Latin small letter s with caron
u'\u0178' : u'Yuml', # Latin capital letter y with diaeresis
u'\u0192' : u'fnof', # Latin small letter f with hook (= function = florin)
u'\u02C6' : u'circ', # modifier letter circumflex accent
u'\u02DC' : u'tilde', # small tilde
u'\u0391' : u'Alpha', # Greek capital letter Alpha
u'\u0392' : u'Beta', # Greek capital letter Beta
u'\u0393' : u'Gamma', # Greek capital letter Gamma
u'\u0394' : u'Delta', # Greek capital letter Delta
u'\u0395' : u'Epsilon', # Greek capital letter Epsilon
u'\u0396' : u'Zeta', # Greek capital letter Zeta
u'\u0397' : u'Eta', # Greek capital letter Eta
u'\u0398' : u'Theta', # Greek capital letter Theta
u'\u0399' : u'Iota', # Greek capital letter Iota
u'\u039A' : u'Kappa', # Greek capital letter Kappa
u'\u039B' : u'Lambda', # Greek capital letter Lambda
u'\u039C' : u'Mu', # Greek capital letter Mu
u'\u039D' : u'Nu', # Greek capital letter Nu
u'\u039E' : u'Xi', # Greek capital letter Xi
u'\u039F' : u'Omicron', # Greek capital letter Omicron
u'\u03A0' : u'Pi', # Greek capital letter Pi
u'\u03A1' : u'Rho', # Greek capital letter Rho
u'\u03A3' : u'Sigma', # Greek capital letter Sigma
u'\u03A4' : u'Tau', # Greek capital letter Tau
u'\u03A5' : u'Upsilon', # Greek capital letter Upsilon
u'\u03A6' : u'Phi', # Greek capital letter Phi
u'\u03A7' : u'Chi', # Greek capital letter Chi
u'\u03A8' : u'Psi', # Greek capital letter Psi
u'\u03A9' : u'Omega', # Greek capital letter Omega
u'\u03B1' : u'alpha', # Greek small letter alpha
u'\u03B2' : u'beta', # Greek small letter beta
u'\u03B3' : u'gamma', # Greek small letter gamma
u'\u03B4' : u'delta', # Greek small letter delta
u'\u03B5' : u'epsilon', # Greek small letter epsilon
u'\u03B6' : u'zeta', # Greek small letter zeta
u'\u03B7' : u'eta', # Greek small letter eta
u'\u03B8' : u'theta', # Greek small letter theta
u'\u03B9' : u'iota', # Greek small letter iota
u'\u03BA' : u'kappa', # Greek small letter kappa
u'\u03BB' : u'lambda', # Greek small letter lambda
u'\u03BC' : u'mu', # Greek small letter mu
u'\u03BD' : u'nu', # Greek small letter nu
u'\u03BE' : u'xi', # Greek small letter xi
u'\u03BF' : u'omicron', # HTMLsymbol	NEW	Greek small letter omicron
u'\u03C0' : u'pi', # Greek small letter pi
u'\u03C1' : u'rho', # Greek small letter rho
u'\u03C2' : u'sigmaf', # Greek small letter final sigma
u'\u03C3' : u'sigma', # Greek small letter sigma
u'\u03C4' : u'tau', # Greek small letter tau
u'\u03C5' : u'upsilon', # Greek small letter upsilon
u'\u03C6' : u'phi', # Greek small letter phi
u'\u03C7' : u'chi', # Greek small letter chi
u'\u03C8' : u'psi', # Greek small letter psi
u'\u03C9' : u'omega', # Greek small letter omega
u'\u03D1' : u'thetasym', # NEW	Greek theta symbol
u'\u03D2' : u'upsih', # NEW	Greek Upsilon with hook symbol
u'\u03D6' : u'piv', # Greek pi symbol
u'\u2002' : u'ensp', # en space[d]
u'\u2003' : u'emsp', # em space[d]
u'\u2009' : u'thinsp', # thin space[d]
u'\u200C' : u'zwnj', # zero-width non-joiner
u'\u200D' : u'zwj', # zero-width joiner
u'\u200E' : u'lrm', # NEW RFC 2070	left-to-right mark
u'\u200F' : u'rlm', # NEW RFC 2070	right-to-left mark
u'\u2013' : u'ndash', # en dash
u'\u2014' : u'mdash', # em dash
u'\u2018' : u'lsquo', # left single quotation mark
u'\u2019' : u'rsquo', # right single quotation mark
u'\u201A' : u'sbquo', # HTMLspecial	NEW	single low-9 quotation mark
u'\u201C' : u'ldquo', # left double quotation mark
u'\u201D' : u'rdquo', # right double quotation mark
u'\u201E' : u'bdquo', # HTMLspecial	NEW	double low-9 quotation mark
u'\u2020' : u'dagger', # dagger, obelisk
u'\u2021' : u'Dagger', # double dagger, double obelisk
u'\u2022' : u'bull', # bullet (= black small circle)[f]
u'\u2026' : u'hellip', # horizontal ellipsis (= three dot leader)
u'\u2030' : u'permil', # per mille sign
u'\u2032' : u'prime', # prime (= minutes = feet)
u'\u2033' : u'Prime', # double prime (= seconds = inches)
u'\u2039' : u'lsaquo', # proposed	single left-pointing angle quotation mark[g]
u'\u203A' : u'rsaquo', # proposed	single right-pointing angle quotation mark[g]
u'\u203E' : u'oline', # NEW	overline (= spacing overscore)
u'\u2044' : u'frasl', # NEW	fraction slash (= solidus)
u'\u20AC' : u'euro', # HTMLspecial	NEW	euro sign
u'\u2111' : u'image', # black-letter capital I (= imaginary part)
u'\u2118' : u'weierp', # script capital P (= power set = Weierstrass p)
u'\u211C' : u'real', # black-letter capital R (= real part symbol)
u'\u2122' : u'trade', # trademark symbol
u'\u2135' : u'alefsym', # NEW	alef symbol (= first transfinite cardinal)[h]
u'\u2190' : u'larr', # leftwards arrow
u'\u2191' : u'uarr', # upwards arrow
u'\u2192' : u'rarr', # rightwards arrow
u'\u2193' : u'darr', # downwards arrow
u'\u2194' : u'harr', # left right arrow
u'\u21B5' : u'crarr', # NEW	downwards arrow with corner leftwards (= carriage return)
u'\u21D0' : u'lArr', # leftwards double arrow[i]
u'\u21D1' : u'uArr', # upwards double arrow
u'\u21D2' : u'rArr', # rightwards double arrow[j]
u'\u21D3' : u'dArr', # downwards double arrow
u'\u21D4' : u'hArr', # left right double arrow
u'\u2200' : u'forall', # for all
u'\u2202' : u'part', # partial differential
u'\u2203' : u'exist', # there exists
u'\u2205' : u'empty', # empty set (= null set = diameter)
u'\u2207' : u'nabla', # nabla (= backward difference)
u'\u2208' : u'isin', # element of
u'\u2209' : u'notin', # not an element of
u'\u220B' : u'ni', # contains as member
u'\u220F' : u'prod', # n-ary product (= product sign)[k]
u'\u2211' : u'sum', # n-ary summation[l]
u'\u2212' : u'minus', # minus sign
u'\u2217' : u'lowast', # asterisk operator
u'\u221A' : u'radic', # square root (= radical sign)
u'\u221D' : u'prop', # proportional to
u'\u221E' : u'infin', # infinity
u'\u2220' : u'ang', # angle
u'\u2227' : u'and', # logical and (= wedge)
u'\u2228' : u'or', # logical or (= vee)
u'\u2229' : u'cap', # intersection (= cap)
u'\u222A' : u'cup', # union (= cup)
u'\u222B' : u'int', # integral
u'\u2234' : u'there4', # therefore sign
u'\u223C' : u'sim', # tilde operator (= varies with = similar to)[m]
u'\u2245' : u'cong', # congruent to
u'\u2248' : u'asymp', # almost equal to (= asymptotic to)
u'\u2260' : u'ne', # not equal to
u'\u2261' : u'equiv', # identical to; sometimes used for 'equivalent to'
u'\u2264' : u'le', # less-than or equal to
u'\u2265' : u'ge', # greater-than or equal to
u'\u2282' : u'sub', # subset of
u'\u2283' : u'sup', # superset of[n]
u'\u2284' : u'nsub', # not a subset of
u'\u2286' : u'sube', # subset of or equal to
u'\u2287' : u'supe', # superset of or equal to
u'\u2295' : u'oplus', # circled plus (= direct sum)
u'\u2297' : u'otimes', # circled times (= vector product)
u'\u22A5' : u'perp', # up tack (= orthogonal to = perpendicular)[o]
u'\u22C5' : u'sdot', # dot operator[p]
u'\u2308' : u'lceil', # left ceiling (= APL upstile)
u'\u2309' : u'rceil', # right ceiling
u'\u230A' : u'lfloor', # left floor (= APL downstile)
u'\u230B' : u'rfloor', # right floor
u'\u2329' : u'lang', # left-pointing angle bracket (= bra)[q]
u'\u232A' : u'rang', # right-pointing angle bracket (= ket)[r]
u'\u25CA' : u'loz', # lozenge
u'\u2660' : u'spades', # black spade suit[f]
u'\u2663' : u'clubs', # black club suit (= shamrock)[f]
u'\u2665' : u'hearts', # black heart suit (= valentine)[f]
u'\u2666' : u'diams' # black diamond suit[f]
                        }
        # Identify the platform and operating system, in case we find a reason to care
        self.version_pyqt = PYQT_VERSION_STR # python string eg '4.9.5'
        self.version_qt = QT_VERSION_STR # python string e.g. '4.8.0'
        try:
            junk = QSysInfo.WindowsVersion
            self.osType = 'Win'
        except: # that static var does not exist, so,
            try:
                junk = QSysInfo.MacintoshVersion
                self.osType = 'Mac'
            except: # that doesn't exist either, ergo:
                self.osType = 'Linux'
