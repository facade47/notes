#!/usr/bin/env python
#notes.py
#Simple, locally stored note-taking application based on "Megasolid Idiom"
#Megasolid Idiom code is licensed under the MIT License:
#https://github.com/mfitzp/15-minute-apps#license (Retrieved 6/23/19)
#Requires these packages: python-pyqt5, python-pythonmagick

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *
import PythonMagick

import os, sys, base64, datetime
import uuid
import dehtml

def getNotesFolder():
    notesfolder = ""
    try:
        with open(self.path, 'r') as f:
            notesfolder = f.read()
    except Exception as e:
        directory = os.path.dirname(os.path.realpath(__file__)) + '/notes/deleted'
        if not os.path.exists(directory):
            os.makedirs(directory)
        cfgfile = open(NOTES_FOLDER_CFG, 'w+')
        notesfolder = os.path.join(PROGRAM_LOCATION, "notes")
        cfgfile.write(notesfolder)
        cfgfile.close()
    return notesfolder

FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14, 18, 24, 36, 48, 64, 72, 96, 144, 288]
IMAGE_EXTENSIONS = ['.jpg','.png','.bmp']
HTML_EXTENSIONS = ['.htm', '.html']
DEFAULT_IMAGE_TYPE = 'png'
MAX_IMAGE_SIZE = 150
MAX_TITLE_LEN = 50
PROGRAM_LOCATION = os.path.dirname(os.path.realpath(__file__))
BUFFER = os.path.join(PROGRAM_LOCATION, 'buffer')
NUM_CHARS_TIL_SAVE = 1000
NOTES_FOLDER_CFG = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'notes.cfg')
NOTES_FOLDER = getNotesFolder()

if not os.path.exists(BUFFER): os.makedirs(BUFFER)
    
def splitext(p):
    return os.path.splitext(p)[1].lower()

class Note(QListWidgetItem):
    def __init__(self, path):
        super(Note, self).__init__()
        self.path = path
        self.setTitle()
        self.lmd = os.path.getmtime(self.path)

    def __repr__(self):
        return self.path

    def setTitle(self, fulltext=None):
        if fulltext: pass
        else:
            try:
                with open(self.path, 'r') as f:
                    fulltext = f.read()
            except Exception as e:
                print(str(e))
        html = False
        try: html = (fulltext.split('\n', 1)[0].split()[0] == '<!DOCTYPE')
        except: pass
        if html: fulltext = dehtml.dehtml(fulltext)
        self.title = fulltext.strip().split('\n', 1)[0][:MAX_TITLE_LEN]
        if not self.title: self.title = "Untitled"
        self.setText(self.title)
        return self.title

    @staticmethod
    def sortNotes(notes):
        import operator
        sortkey = operator.attrgetter("lmd")
        return sorted(notes, key=sortkey, reverse=True)

class NoteListWidget(QListWidget):
    def __init__(self, parent, notes):
        super(NoteListWidget, self).__init__(parent)
        self.parent = parent
        self.notes = notes
        for n in self.notes:
            self.addItem(n)
        self.setCurrentRow(0)
        self.currentItemChanged.connect(self.item_changed)

    def item_changed(self, newItem):
        self.parent.switchNote(newItem)

    def add_note(self, newItem):
        self.insertItem(0, newItem)
        self.notes.insert(0, newItem)
        self.setCurrentRow(0)

    def updateTitle(self, fullText):
        a = self.currentItem()
        return a.setTitle(fullText)

    def removeNote(self):
        i = self.currentRow()
        self.blockSignals(True)
        self.takeItem(i)
        self.blockSignals(False)
        del self.notes[i]
        i -= 1
        if i < 0: i = 0
        self.setCurrentRow(i)
        if self.notes: self.parent.switchNote(self.notes[i])
        else: self.parent.new_file()

    def to_top_of_list(self):
        currentRow = self.currentRow()
        if currentRow:
            self.blockSignals(True)
            n = self.notes[currentRow]
            del self.notes[currentRow]
            self.notes.insert(0, n)
            currentItem = self.takeItem(currentRow)
            self.insertItem(0, currentItem)
            self.setCurrentRow(0)
            self.blockSignals(False)

class TextEdit(QTextEdit):

    #[source] is a QMimeData object.
    #canInsertFromMimeData() and insertFromMimeData() are called when an image is dropped onto the window.
    def canInsertFromMimeData(self, source):

        if source.hasImage():
            return True
        else:
            return super(TextEdit, self).canInsertFromMimeData(source)

    def insertFromMimeData(self, source):

        cursor = self.textCursor()
        document = self.document()

        if source.hasUrls():

            for u in source.urls():
                file_ext = splitext(str(u.toLocalFile()))
                if u.isLocalFile() and file_ext in IMAGE_EXTENSIONS:
                    loc = os.path.join(BUFFER, 'temp-image.' + DEFAULT_IMAGE_TYPE)
                    image = PythonMagick.Image( u.toLocalFile().encode('ascii', errors='xmlcharrefreplace') )
                    if image.size().width() > MAX_IMAGE_SIZE: 
                        image.resize(PythonMagick.Geometry(MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
                    image.write( loc )
                    f = open(loc, 'rb')
                    heximg = base64.b64encode(f.read())
                    f.close()
                    if cursor.positionInBlock() != 0: cursor.insertBlock()
                    cursor.insertHtml('<img src="data:image/' + DEFAULT_IMAGE_TYPE + ';base64,' + heximg + '" />')
                    cursor.insertBlock()

                else:
                    # If we hit a non-image or non-local URL break the loop and fall out
                    # to the super call & let Qt handle it
                    break

            else:
                # If all were valid images, finish here.
                return


        elif source.hasImage():
            print "Passing on insertFromMimeData->source.hasImage()."
            #I have no idea if this code works, and I'm not sure what condition triggers this. --facade
            #loc = BUFFER + 'temp-image'
            #source.imageData().save(loc)
            #image = PythonMagick.Image( loc )
            #image.resize(PythonMagick.Geometry(150, 150))
            #image.write( loc )
            #qimage = QMimeData()
            #qimage.setImageData(QImage( loc ))
            #uuid = uuid.uuid4().hex
            #document.addResource(QTextDocument.ImageResource, uuid, qimage)
            #cursor.insertImage(uuid)
            #return

        super(TextEdit, self).insertFromMimeData(source)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        
        super(MainWindow, self).__init__(*args, **kwargs)

        self.path = None #holds the path of the currently open file.
        self.changed = 0

        self.editor = TextEdit()
        self.editor.setAutoFormatting(QTextEdit.AutoAll)
        self.editor.selectionChanged.connect(self.update_format)
        self.editor.textChanged.connect(self.auto_save)
        self.editor.cursorPositionChanged.connect(self.updateIconColor)
        self.editor.setFont(QFont('Ubuntu', 12))
        self.editor.setFontPointSize(12)
        self.set_menu_and_toolbar()

        notes = self.getNotes(NOTES_FOLDER)
        notes = Note.sortNotes(notes)
        self.notewidget = NoteListWidget(self, notes)
        self.openFile(notes[0].path, notes[0].title)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.notewidget)
        self.splitter.addWidget(self.editor)
        self.splitter.setSizes([75,150])

        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_format()
        self.notewidget.setFocus()
        self.show()

    def block_signals(self, objects, b):
        for o in objects:
            o.blockSignals(b)

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def getNotes(self, dirName):
        fileList = os.listdir(dirName)
        notes = list()
        for entry in fileList:
            fullPath = os.path.join(dirName, entry)
            if not os.path.isdir(fullPath): notes.append(Note(fullPath))
        if not notes:
            firstnote = os.path.join(dirName, self.getNewFilename())
            f = open(firstnote, 'w+')
            f.close()
            notes.append(Note(firstnote))
        return notes

    def switchNote(self, newNote):
        if newNote:
            if os.path.exists(self.path): self.file_save_now()
            self.openFile(newNote.path)
            self.update_title(newNote.title)
        else:
            self.new_file()

    def openFile(self, path, title=''):
        try:
            with open(path, 'rU') as f:
                text = f.read()

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            # Qt will automatically try and guess the format as txt/html
            self.editor.blockSignals(True)
            self.editor.setText(text)
            self.editor.blockSignals(False)
            #Nasty way to fix it so that program font is set to the same as the first char in html file...
            #Move the cursor forward to send the selectionChanged signal which triggers update_format on the selection,
            #Then move the cursor back to the first position.
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.Right)
            self.editor.setTextCursor(cursor)
            cursor.movePosition(QTextCursor.Left)
            self.editor.setTextCursor(cursor)
            self.update_format()
            self.update_title(title)
            self.changed = 0

    def new_file(self):
        path = self.getNewFilename()
        f = open(path, 'w+')
        self.notewidget.add_note(Note(path))
        self.editor.setDocumentTitle(str(datetime.datetime.now().strftime("%B %d, %Y %I:%M %p")))

    def getNewFilename(self):
        digits = 6 #supports 1,000,000 notes
        num = 1
        numstr = self.numToStr(num, digits)
        while os.path.exists( os.path.join( NOTES_FOLDER, "note%s.html"%numstr ) ):
            num += 1
            numstr = self.numToStr( num )
            if len(str(num)) > digits:
                print "You literally have 1" + (digits * "0") + "notes.  I can't handle this, exiting."
                exit()
        return os.path.join(NOTES_FOLDER, "note%s.html"%numstr)
            
        
    def numToStr(self, num, minDigits=6):
        return ( (minDigits - len(str(num))) * "0" ) + str(num)

    def auto_save(self):
        #DO NOT CALL DIRECTLY, this should only be triggered by a QT signal.
        #Auto-save every x characters
        if self.changed > NUM_CHARS_TIL_SAVE:
            path = self.path
            text = self.editor.toHtml() if splitext(path) in HTML_EXTENSIONS else self.editor.toPlainText()
            try:
                with open(self.path, 'w') as f:
                    f.write(text)
            except Exception as e:
                self.dialog_critical(str(e))
            self.changed = 0
        else:
            self.changed += 1
            #TODO: till need to work on case where first line is blank, second line has one char, third line has many,
            #and the client deletes the second line
            if self.isFirstLine(): 
                t = self.notewidget.updateTitle(self.editor.toPlainText())
                self.update_title(t)
            if self.changed == 1: self.to_top_of_list()

    def isFirstLine(self):
        bc = self.editor.textCursor().blockNumber()
        if bc == 0: return True
        else:
            lines = self.editor.document().blockCount()
            for l in range(0, lines):
                if l > bc: return False
                elif l < bc and self.editor.toPlainText().split('\n')[l].strip(): return False
                elif l == bc and self.editor.toPlainText().split('\n')[l].strip(): return True
        return False

    def file_save_now(self):
        #Save if the file is changed
        if self.changed:
            path = self.path
            text = self.editor.toHtml() if splitext(path) in HTML_EXTENSIONS else self.editor.toPlainText()
            try:
                with open(self.path, 'w') as f:
                    f.write(text)
            except Exception as e:
                self.dialog_critical(str(e))

    def file_saveas(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export file", "", "HTML documents (*.html);;Text documents (*.txt);;All files (*.*)")
        if not path:
            # If dialog is cancelled, will return ''
            return
        text = self.editor.toHtml() if splitext(path) in HTML_EXTENSIONS else self.editor.toPlainText()
        try:
            with open(path, 'w') as f:
                f.write(text)
        except Exception as e:
            self.dialog_critical(str(e))
        else:
            self.update_title()

    def delete_file(self):
        dpath = os.path.join(NOTES_FOLDER, 'deleted', os.path.split(self.path)[1])
        ext = os.path.splitext(os.path.split(self.path)[1])[1]
        i = 1
        while os.path.exists(dpath):
            dpath = os.path.join(NOTES_FOLDER, 'deleted', os.path.splitext(os.path.split(self.path)[1])[0] + '-' + self.numToStr(i) + ext)
            i += 1
        os.rename(self.path, dpath)
        self.notewidget.removeNote()

    def file_print(self):
        dlg = QPrintDialog()
        if dlg.exec_():
            self.editor.print_(dlg.printer())

    def update_title(self, title=''):
        self.setWindowTitle("%s - Notes" % (title if title else "Untitled"))

    def to_top_of_list(self):
        self.notewidget.to_top_of_list()

    def setApp(self, app):
        app.aboutToQuit.connect(self.closeEvent)
    
    def closeEvent(self, evt=None):
        #I do not understand WHY WHY WHY the aboutToClose() signal is sent twice..????
        self.file_save_now()

    def toggleHsv(self):
        #toggles the hsv picker ON
        self.spinColEdit.show()
        really_here = self.mapToGlobal(self.previewPanel.rect().bottomRight())
        bottom_corner= really_here.x()+29
        pop_here = really_here.y()+27
        self.spinColEdit.move(bottom_corner, pop_here)

    #toggles OFF the hsv picker
    def eventFilter(self, source, event):
        if source is self.spinColEdit and event.type() in (QEvent.Close, QEvent.Hide, QEvent.HideToParent):
            self.previewPanel.setChecked(False)
            self.editor.setFocus()
        return QWidget.eventFilter(self, source, event)

    def updateTextColor(self, color):
        px=QPixmap(128,128)
        px.fill(color)
        self.previewPanel.setIcon(QIcon(px))
        self.spinColEdit.setCurrentColor(color)
        self.editor.setTextColor(color)

    def updateIconColor(self):
        color = self.editor.textColor()
        px=QPixmap(128,128)
        px.fill(color)
        self.spinColEdit.blockSignals(True)
        self.spinColEdit.setCurrentColor(color)
        self.spinColEdit.blockSignals(False)
        self.previewPanel.setIcon(QIcon(px))

    def insert_picture(self):
        path, _ = QFileDialog.getOpenFileName(self, "Insert image", "", "PNG Images (*.png);;JPEG images (*.jpg);;All files (*.*)")
        try:
            file_ext = splitext(path)
            if file_ext in IMAGE_EXTENSIONS:
                cursor = self.editor.textCursor()
                loc = os.path.join(BUFFER, 'temp-image.' + DEFAULT_IMAGE_TYPE)
                image = PythonMagick.Image( path.encode('ascii', errors='xmlcharrefreplace') )
                if image.size().width() > MAX_IMAGE_SIZE: 
                    image.resize(PythonMagick.Geometry(MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
                image.write( loc )
                f = open(loc, 'rb')
                heximg = base64.b64encode(f.read())
                f.close()
                if cursor.positionInBlock() != 0: cursor.insertBlock()
                cursor.insertHtml('<img src="data:image/' + DEFAULT_IMAGE_TYPE + ';base64,' + heximg + '" />')
                cursor.insertBlock()
        except Exception as e:
            self.dialog_critical(str(e))

    def set_menu_and_toolbar(self):
        file_toolbar = QToolBar("File")
        file_toolbar.setIconSize(QSize(14, 14))
        self.addToolBar(file_toolbar)
        file_menu = self.menuBar().addMenu("&File")

        new_file_action = QAction(QIcon(os.path.join('images', 'ui-tab--plus.png')), "New Note", self)
        new_file_action.triggered.connect(self.new_file)
        file_menu.addAction(new_file_action)
        file_toolbar.addAction(new_file_action)

        saveas_file_action = QAction(QIcon(os.path.join('images', 'disk--pencil.png')), "Export...", self)
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)
        file_toolbar.addAction(saveas_file_action)

        print_action = QAction(QIcon(os.path.join('images', 'printer.png')), "Print...", self)
        print_action.triggered.connect(self.file_print)
        file_menu.addAction(print_action)
        file_toolbar.addAction(print_action)

        delete_file_action = QAction(QIcon(os.path.join('images', 'trash.gif')), "Delete Note", self)
        delete_file_action.triggered.connect(self.delete_file)
        file_menu.addAction(delete_file_action)
        file_toolbar.addAction(delete_file_action)

        edit_toolbar = QToolBar("Edit")
        edit_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(edit_toolbar)
        edit_menu = self.menuBar().addMenu("&Edit")

        undo_action = QAction(QIcon(os.path.join('images', 'arrow-curve-180-left.png')), "Undo", self)
        undo_action.triggered.connect(self.editor.undo)
        edit_toolbar.addAction(undo_action)
        edit_menu.addAction(undo_action)

        redo_action = QAction(QIcon(os.path.join('images', 'arrow-curve.png')), "Redo", self)
        redo_action.triggered.connect(self.editor.redo)
        edit_toolbar.addAction(redo_action)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction(QIcon(os.path.join('images', 'scissors.png')), "Cut", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_toolbar.addAction(cut_action)
        edit_menu.addAction(cut_action)

        copy_action = QAction(QIcon(os.path.join('images', 'document-copy.png')), "Copy", self)
        cut_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_toolbar.addAction(copy_action)
        edit_menu.addAction(copy_action)

        paste_action = QAction(QIcon(os.path.join('images', 'clipboard-paste-document-text.png')), "Paste", self)
        cut_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_toolbar.addAction(paste_action)
        edit_menu.addAction(paste_action)

        select_action = QAction(QIcon(os.path.join('images', 'selection-input.png')), "Select all", self)
        cut_action.setShortcut(QKeySequence.SelectAll)
        select_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_action)

        edit_menu.addSeparator()

        insert_picture_action = QAction(QIcon(os.path.join('images', 'camera.png')), "Insert Picture...", self)
        insert_picture_action.triggered.connect(self.insert_picture)
        edit_menu.addAction(insert_picture_action)

        edit_menu.addSeparator()

        self.editor.setLineWrapMode( True )

        format_toolbar = QToolBar("Format")
        format_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(format_toolbar)
        format_menu = self.menuBar().addMenu("&Format")

        # We need references to these actions/settings to update as selection changes, so attach to self.
        self.fonts = QFontComboBox()
        self.fonts.currentFontChanged.connect(self.editor.setCurrentFont)
        format_toolbar.addWidget(self.fonts)

        self.fontsize = QComboBox()
        self.fontsize.addItems([str(s) for s in FONT_SIZES])

        # Connect to the signal producing the text of the current selection. Convert the string to float
        # and set as the pointsize. We could also use the index + retrieve from FONT_SIZES.
        self.fontsize.currentIndexChanged[str].connect(lambda s: self.editor.setFontPointSize(float(s)) )
        format_toolbar.addWidget(self.fontsize)

        self.color=None
        self.previewPanel = QPushButton()
        self.previewPanel.setCheckable(True)
        self.spinColEdit =  QColorDialog(self)
        self.spinColEdit.setOption(QColorDialog.DontUseNativeDialog)
        self.spinColEdit.setOption(QColorDialog.NoButtons)
        self.spinColEdit.setWindowFlags(Qt.Popup)
        if isinstance(self.color, QColor):
            self._color = self.color
        elif isinstance(self.color, str):
            self._color = QColor(self.color)
        else:
            self._color = QColor()
        self._picking = False
        self.previewPanel.clicked.connect(self.toggleHsv)
        self.spinColEdit.currentColorChanged.connect(self.updateTextColor)
        self.spinColEdit.installEventFilter(self)
        self.spinColEdit.setCurrentColor(self._color)
        format_toolbar.addWidget(self.previewPanel)

        self.bold_action = QAction(QIcon(os.path.join('images', 'edit-bold.png')), "Bold", self)
        self.bold_action.setShortcut(QKeySequence.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.toggled.connect(lambda x: self.editor.setFontWeight(QFont.Bold if x else QFont.Normal))
        format_toolbar.addAction(self.bold_action)
        format_menu.addAction(self.bold_action)

        self.italic_action = QAction(QIcon(os.path.join('images', 'edit-italic.png')), "Italic", self)
        self.italic_action.setShortcut(QKeySequence.Italic)
        self.italic_action.setCheckable(True)
        self.italic_action.toggled.connect(self.editor.setFontItalic)
        format_toolbar.addAction(self.italic_action)
        format_menu.addAction(self.italic_action)

        self.underline_action = QAction(QIcon(os.path.join('images', 'edit-underline.png')), "Underline", self)
        self.underline_action.setShortcut(QKeySequence.Underline)
        self.underline_action.setCheckable(True)
        self.underline_action.toggled.connect(self.editor.setFontUnderline)
        format_toolbar.addAction(self.underline_action)
        format_menu.addAction(self.underline_action)

        format_menu.addSeparator()

        self.alignl_action = QAction(QIcon(os.path.join('images', 'edit-alignment.png')), "Align left", self)
        self.alignl_action.setCheckable(True)
        self.alignl_action.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignLeft))
        format_toolbar.addAction(self.alignl_action)
        format_menu.addAction(self.alignl_action)

        self.alignc_action = QAction(QIcon(os.path.join('images', 'edit-alignment-center.png')), "Align center", self)
        self.alignc_action.setCheckable(True)
        self.alignc_action.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignCenter))
        format_toolbar.addAction(self.alignc_action)
        format_menu.addAction(self.alignc_action)

        self.alignr_action = QAction(QIcon(os.path.join('images', 'edit-alignment-right.png')), "Align right", self)
        self.alignr_action.setCheckable(True)
        self.alignr_action.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignRight))
        format_toolbar.addAction(self.alignr_action)
        format_menu.addAction(self.alignr_action)

        self.alignj_action = QAction(QIcon(os.path.join('images', 'edit-alignment-justify.png')), "Justify", self)
        self.alignj_action.setCheckable(True)
        self.alignj_action.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignJustify))
        format_toolbar.addAction(self.alignj_action)
        format_menu.addAction(self.alignj_action)

        format_group = QActionGroup(self)
        format_group.setExclusive(True)
        format_group.addAction(self.alignl_action)
        format_group.addAction(self.alignc_action)
        format_group.addAction(self.alignr_action)
        format_group.addAction(self.alignj_action)

        about_action = QAction(QIcon(os.path.join('images', 'question.png')), "About File", self)
        about_action.triggered.connect(self.about)
        format_toolbar.addAction(about_action)

        format_menu.addSeparator()

    def about(self):
        created = self.editor.documentTitle()
        modified = datetime.datetime.fromtimestamp(int(os.path.getmtime(self.path))).strftime("%B %d, %Y %I:%M %p")
        text = "About this note:\n\nCreated: " + created + "\nLast Modified: " + modified + "\nFile location: " + self.path
        msgbox = QMessageBox()
        msgbox.setText(text)
        msgbox.exec_()

    def update_format(self):
        """
        Update the font format toolbar/actions when a new text selection is made. This is neccessary to keep
        toolbars/etc. in sync with the current edit state.
        :return:
        """
        # A list of all format-related widgets/actions, so we can disable/enable signals when updating.
        self._format_actions = [
            self.fonts,
            self.fontsize,
            self.bold_action,
            self.italic_action,
            self.underline_action,
            # We don't need to disable signals for alignment, as they are paragraph-wide.
        ]
        # Disable signals for all format widgets, so changing values here does not trigger further formatting.
        self.block_signals(self._format_actions, True)

        self.fonts.setCurrentFont(self.editor.currentFont())
        # Nasty, but we get the font-size as a float but want it was an int
        self.fontsize.setCurrentText(str(int(self.editor.fontPointSize())))

        self.italic_action.setChecked(self.editor.fontItalic())
        self.underline_action.setChecked(self.editor.fontUnderline())
        self.bold_action.setChecked(self.editor.fontWeight() == QFont.Bold)

        self.alignl_action.setChecked(self.editor.alignment() == Qt.AlignLeft)
        self.alignc_action.setChecked(self.editor.alignment() == Qt.AlignCenter)
        self.alignr_action.setChecked(self.editor.alignment() == Qt.AlignRight)
        self.alignj_action.setChecked(self.editor.alignment() == Qt.AlignJustify)

        self.updateIconColor()

        self.block_signals(self._format_actions, False)

if __name__ == '__main__':
    os.environ["QT_LOGGING_RULES"] = "qt5ct.debug=false"
    app = QApplication(sys.argv)
    app.setApplicationName("Notes")
    window = MainWindow()
    window.setApp(app)
    app.exec_()
