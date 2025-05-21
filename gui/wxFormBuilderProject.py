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
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 732,763 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.Size( 500,400 ), wx.DefaultSize )

        mainBoxSizer = wx.BoxSizer( wx.VERTICAL )

        mainBoxSizer.SetMinSize( wx.Size( 640,-1 ) )
        self.mainScrollableWindow = wx.ScrolledWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 640,480 ), wx.HSCROLL|wx.VSCROLL )
        self.mainScrollableWindow.SetScrollRate( 5, 5 )
        programsWrapSizer = wx.WrapSizer( wx.VERTICAL, wx.WRAPSIZER_DEFAULT_FLAGS )

        programsWrapSizer.SetMinSize( wx.Size( 640,480 ) )
        ProgramBoxSizer = wx.StaticBoxSizer( wx.StaticBox( self.mainScrollableWindow, wx.ID_ANY, _(u"Heating circuit 1") ), wx.VERTICAL )

        ProgramIOBoxSizer = wx.FlexGridSizer( 0, 1, 10, 0 )
        ProgramIOBoxSizer.SetFlexibleDirection( wx.BOTH )
        ProgramIOBoxSizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        ProgramInputsBox = wx.StaticBoxSizer( wx.StaticBox( ProgramBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )

        ProgramInput1BoxSizer = wx.StaticBoxSizer( wx.StaticBox( ProgramInputsBox.GetStaticBox(), wx.ID_ANY, _(u"InputTitle") ), wx.HORIZONTAL )

        self.m_spinCtrlDouble1 = wx.SpinCtrlDouble( ProgramInput1BoxSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER, 0, 100, 0, 0.1 )
        self.m_spinCtrlDouble1.SetDigits( 0 )
        ProgramInput1BoxSizer.Add( self.m_spinCtrlDouble1, 0, wx.ALL, 5 )

        self.inputValueSlider = wx.Slider( ProgramInput1BoxSizer.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        ProgramInput1BoxSizer.Add( self.inputValueSlider, 0, wx.ALL, 5 )

        self.inputShortCheckbox = wx.CheckBox( ProgramInput1BoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        ProgramInput1BoxSizer.Add( self.inputShortCheckbox, 0, wx.ALL, 5 )

        self.inputOpenCheckbox = wx.CheckBox( ProgramInput1BoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        ProgramInput1BoxSizer.Add( self.inputOpenCheckbox, 0, wx.ALL, 5 )

        self.inputAutoRadiobutton = wx.RadioButton( ProgramInput1BoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.inputAutoRadiobutton.SetValue( True )
        ProgramInput1BoxSizer.Add( self.inputAutoRadiobutton, 0, wx.ALL, 5 )

        self.inputManualRadioButton = wx.RadioButton( ProgramInput1BoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        ProgramInput1BoxSizer.Add( self.inputManualRadioButton, 0, wx.ALL, 5 )


        ProgramInputsBox.Add( ProgramInput1BoxSizer, 1, wx.EXPAND, 5 )

        ProgramInput2BoxSizer = wx.StaticBoxSizer( wx.StaticBox( ProgramInputsBox.GetStaticBox(), wx.ID_ANY, _(u"InputTitle") ), wx.HORIZONTAL )

        self.inputValueSpinCtrl1 = wx.SpinCtrl( ProgramInput2BoxSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        ProgramInput2BoxSizer.Add( self.inputValueSpinCtrl1, 0, wx.ALL, 5 )

        self.inputValueSlider1 = wx.Slider( ProgramInput2BoxSizer.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        ProgramInput2BoxSizer.Add( self.inputValueSlider1, 0, wx.ALL, 5 )

        self.inputShortCheckbox1 = wx.CheckBox( ProgramInput2BoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        ProgramInput2BoxSizer.Add( self.inputShortCheckbox1, 0, wx.ALL, 5 )

        self.inputOpenCheckbox1 = wx.CheckBox( ProgramInput2BoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        ProgramInput2BoxSizer.Add( self.inputOpenCheckbox1, 0, wx.ALL, 5 )

        self.inputAutoRadiobutton1 = wx.RadioButton( ProgramInput2BoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.inputAutoRadiobutton1.SetValue( True )
        ProgramInput2BoxSizer.Add( self.inputAutoRadiobutton1, 0, wx.ALL, 5 )

        self.inputManualRadioButton1 = wx.RadioButton( ProgramInput2BoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        ProgramInput2BoxSizer.Add( self.inputManualRadioButton1, 0, wx.ALL, 5 )


        ProgramInputsBox.Add( ProgramInput2BoxSizer, 1, wx.EXPAND, 5 )


        ProgramIOBoxSizer.Add( ProgramInputsBox, 1, wx.EXPAND, 5 )

        ProgramOutputsBox = wx.StaticBoxSizer( wx.StaticBox( ProgramBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )

        OutputBoxSizer = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle = wx.StaticText( ProgramOutputsBox.GetStaticBox(), wx.ID_ANY, _(u"Output title"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle.Wrap( -1 )

        self.OutputTitle.SetMinSize( wx.Size( 120,-1 ) )

        OutputBoxSizer.Add( self.OutputTitle, 0, wx.ALL, 5 )

        self.outputValueGauge = wx.Gauge( ProgramOutputsBox.GetStaticBox(), wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.outputValueGauge.SetValue( 0 )
        OutputBoxSizer.Add( self.outputValueGauge, 0, wx.ALL, 5 )


        ProgramOutputsBox.Add( OutputBoxSizer, 1, wx.EXPAND, 5 )

        OutputBoxSizer2 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle2 = wx.StaticText( ProgramOutputsBox.GetStaticBox(), wx.ID_ANY, _(u"Pump"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle2.Wrap( -1 )

        OutputBoxSizer2.Add( self.OutputTitle2, 0, wx.ALL, 5 )

        self.Output2ToggleButton = wx.ToggleButton( ProgramOutputsBox.GetStaticBox(), wx.ID_ANY, _(u"MyButton"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.Output2ToggleButton.SetValue( True )
        OutputBoxSizer2.Add( self.Output2ToggleButton, 0, wx.ALL, 5 )


        ProgramOutputsBox.Add( OutputBoxSizer2, 1, wx.EXPAND, 5 )


        ProgramIOBoxSizer.Add( ProgramOutputsBox, 1, wx.EXPAND, 5 )


        ProgramBoxSizer.Add( ProgramIOBoxSizer, 1, 0, 5 )


        programsWrapSizer.Add( ProgramBoxSizer, 1, 0, 5 )


        self.mainScrollableWindow.SetSizer( programsWrapSizer )
        self.mainScrollableWindow.Layout()
        mainBoxSizer.Add( self.mainScrollableWindow, 1, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( mainBoxSizer )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.Bind( wx.EVT_CLOSE, self.doClose )
        self.m_spinCtrlDouble1.Bind( wx.EVT_SPINCTRLDOUBLE, self.onSpin )
        self.m_spinCtrlDouble1.Bind( wx.EVT_TEXT_ENTER, self.onSpinText )
        self.inputValueSlider.Bind( wx.EVT_SCROLL, self.onScroll )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def doClose( self, event ):
        event.Skip()

    def onSpin( self, event ):
        event.Skip()

    def onSpinText( self, event ):
        event.Skip()

    def onScroll( self, event ):
        event.Skip()


