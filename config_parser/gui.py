# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
## http://www.wxformbuilder.org/
##
###########################################################################

import wx

import config_parser.convert
from config_parser.gui_base import MainFrame as MainFrameBase 


import gettext
_ = gettext.gettext

###########################################################################
## Class MainFrame
###########################################################################
class MainFrame ( MainFrameBase ):

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def doClose( self, event ):
        event.Skip()
        exit(0)

    def OnFileSelect( self, event ):
        event.Skip()
        filepath = self.m_filePicker1.GetPath()
        print(self.m_filePicker1.GetPath())
        self.open_file(filepath)

    def OnConvert( self, event ):
        event.Skip()
        inputText  = self.m_textCtrl2.GetValue()
        outputText = config_parser.convert.convertConfigToPreset(inputText)
        
        self.m_textCtrl3.SetValue(outputText)
        
    def OnSaveFileSelect( self, event ):
        event.Skip()
        filepath = self.m_filePicker2.GetPath()
        print(self.m_filePicker2.GetPath())
        self.save_file(filepath)
        
# открываем файл в текстовое поле
    def open_file(self, filepath):
        if filepath != "":
            with open(filepath, "r", encoding="utf-8") as file:
                text =file.read()
                self.m_textCtrl2.Clear()
                self.m_textCtrl2.SetValue(text)
                
    # сохраняем текст из текстового поля в файл
    def save_file(self, filepath):
        if filepath != "":
            text = self.m_textCtrl3.GetValue()
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(text)

class guiThread():
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(guiThread, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if hasattr(self, '_initDone'):
            return
        
        self._app = wx.App()
        self._frame = wx.Frame(None, title='Simple application')
        self._ex = MainFrame(self._frame)
        self._ex.Show()
        
        self._initDone = True
        
    def run(self):
        self._app.MainLoop()
