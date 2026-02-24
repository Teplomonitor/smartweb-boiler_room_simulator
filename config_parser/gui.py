# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
## http://www.wxformbuilder.org/
##
###########################################################################

import wx
import wx.xrc
import config_parser.convert


import gettext
_ = gettext.gettext

###########################################################################
## Class MainFrame
###########################################################################
class MainFrame ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 700,600 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.Size( 500,660 ), wx.Size( 600,700 ) )

        fgSizer2 = wx.FlexGridSizer( 2, 1, 0, 0 )
        fgSizer2.SetFlexibleDirection( wx.BOTH )
        fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        fgSizer2.SetMinSize( wx.Size( 400,600 ) )
        bSizer6 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer6.SetMinSize( wx.Size( 100,100 ) )
        self.m_textCtrl2 = wx.TextCtrl( self, wx.ID_ANY, _('''
{
  "controller": {
    "type": "X_S62",
    "title": "SWX 173"
  },
  "programs": [
    {
      "id": 164,
      "type": 42,
      "title": "Смеситель",
      "input_mappings": [
        173
      ],
      "output_mappings": [
        8365,
        8621
      ]
    }
  ]
}'''
        
        ), wx.DefaultPosition, wx.Size( 300,300 ), wx.HSCROLL|wx.TE_CHARWRAP|wx.TE_LEFT|wx.TE_MULTILINE|wx.TE_WORDWRAP )
        self.m_textCtrl2.SetMaxLength( 100 )
        self.m_textCtrl2.SetMinSize( wx.Size( 300,400 ) )

        bSizer6.Add( self.m_textCtrl2, 0, wx.ALL, 5 )

        self.m_textCtrl3 = wx.TextCtrl( self, wx.ID_ANY, _(''), wx.DefaultPosition, wx.Size( 300,300 ), wx.HSCROLL|wx.TE_CHARWRAP|wx.TE_LEFT|wx.TE_MULTILINE|wx.TE_WORDWRAP )
        self.m_textCtrl3.SetMinSize( wx.Size( 300,400 ) )

        bSizer6.Add( self.m_textCtrl3, 0, wx.ALL, 5 )


        fgSizer2.Add( bSizer6, 1, wx.EXPAND, 5 )

        bSizer7 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, _(u"Выберите файл с конфигом"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1.Wrap( -1 )

        bSizer7.Add( self.m_staticText1, 0, wx.ALL, 5 )

        self.m_filePicker1 = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, _(u"Select a file"), _(u"*.*"), wx.DefaultPosition, wx.Size( 500,-1 ), wx.FLP_DEFAULT_STYLE|wx.FLP_OPEN|wx.FLP_SMALL )
        bSizer7.Add( self.m_filePicker1, 0, wx.ALL, 5 )

        self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, _(u"Конвертните конфиг в пресет"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText3.Wrap( -1 )

        bSizer7.Add( self.m_staticText3, 0, wx.ALL, 5 )

        self.ConvertButton = wx.Button( self, wx.ID_ANY, _(u"Convert"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer7.Add( self.ConvertButton, 0, wx.ALL, 5 )

        self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, _(u"Выберите, куда сохранить пресет"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText2.Wrap( -1 )

        bSizer7.Add( self.m_staticText2, 0, wx.ALL, 5 )

        self.m_filePicker2 = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, _(u"Select a file"), _(u"*.*"), wx.DefaultPosition, wx.Size( 500,-1 ), wx.FLP_CHANGE_DIR|wx.FLP_OVERWRITE_PROMPT|wx.FLP_SAVE|wx.FLP_SMALL|wx.FLP_USE_TEXTCTRL )
        bSizer7.Add( self.m_filePicker2, 0, wx.ALL, 5 )


        fgSizer2.Add( bSizer7, 1, wx.ALIGN_CENTER, 5 )


        self.SetSizer( fgSizer2 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.Bind( wx.EVT_CLOSE, self.doClose )
        self.m_filePicker1.Bind( wx.EVT_FILEPICKER_CHANGED, self.OnFileSelect )
        self.ConvertButton.Bind( wx.EVT_BUTTON, self.OnConvert )
        self.m_filePicker2.Bind( wx.EVT_FILEPICKER_CHANGED, self.OnSaveFileSelect )

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
