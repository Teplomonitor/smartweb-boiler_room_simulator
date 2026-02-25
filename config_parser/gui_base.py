# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-0-g80c4cb6)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

import gettext
_ = gettext.gettext

###########################################################################
## Class MainFrame
###########################################################################

class MainFrame ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 650,650 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.Size( 650,650 ), wx.Size( 800,650 ) )

        fgSizer2 = wx.FlexGridSizer( 2, 1, 0, 0 )
        fgSizer2.AddGrowableCol( 0 )
        fgSizer2.AddGrowableRow( 1 )
        fgSizer2.SetFlexibleDirection( wx.HORIZONTAL )
        fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        fgSizer2.SetMinSize( wx.Size( 600,600 ) )
        bSizer6 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer6.SetMinSize( wx.Size( 600,100 ) )
        self.m_textCtrl2 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 300,300 ), wx.TE_CHARWRAP|wx.TE_LEFT|wx.TE_MULTILINE|wx.TE_WORDWRAP )
        self.m_textCtrl2.SetMaxLength( 300 )
        self.m_textCtrl2.SetMinSize( wx.Size( 300,400 ) )
        self.m_textCtrl2.SetMaxSize( wx.Size( 800,-1 ) )

        bSizer6.Add( self.m_textCtrl2, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_textCtrl3 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 300,300 ), wx.HSCROLL|wx.TE_CHARWRAP|wx.TE_LEFT|wx.TE_MULTILINE|wx.TE_WORDWRAP )
        self.m_textCtrl3.SetMaxLength( 200 )
        self.m_textCtrl3.SetMinSize( wx.Size( 300,400 ) )

        bSizer6.Add( self.m_textCtrl3, 0, wx.ALL, 5 )


        fgSizer2.Add( bSizer6, 1, wx.ALIGN_CENTER_HORIZONTAL, 5 )

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

    def OnFileSelect( self, event ):
        event.Skip()

    def OnConvert( self, event ):
        event.Skip()

    def OnSaveFileSelect( self, event ):
        event.Skip()


