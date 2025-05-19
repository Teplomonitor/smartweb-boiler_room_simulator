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
        Program_1 = wx.StaticBoxSizer( wx.StaticBox( self.mainScrollableWindow, wx.ID_ANY, _(u"Heating circuit 1") ), wx.VERTICAL )

        fgSizer453 = wx.FlexGridSizer( 0, 1, 10, 0 )
        fgSizer453.SetFlexibleDirection( wx.BOTH )
        fgSizer453.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        ProgramInputs13 = wx.StaticBoxSizer( wx.StaticBox( Program_1.GetStaticBox(), wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )

        sbSizer17 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl123 = wx.SpinCtrl( sbSizer17.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer17.Add( self.m_spinCtrl123, 0, wx.ALL, 5 )

        self.m_slider623 = wx.Slider( sbSizer17.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer17.Add( self.m_slider623, 0, wx.ALL, 5 )

        self.m_checkBox123 = wx.CheckBox( sbSizer17.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17.Add( self.m_checkBox123, 0, wx.ALL, 5 )

        self.m_checkBox223 = wx.CheckBox( sbSizer17.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox223.SetValue(True)
        sbSizer17.Add( self.m_checkBox223, 0, wx.ALL, 5 )

        self.m_radioBtn223 = wx.RadioButton( sbSizer17.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn223.SetValue( True )
        sbSizer17.Add( self.m_radioBtn223, 0, wx.ALL, 5 )

        self.m_radioBtn323 = wx.RadioButton( sbSizer17.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17.Add( self.m_radioBtn323, 0, wx.ALL, 5 )


        ProgramInputs13.Add( sbSizer17, 1, wx.EXPAND, 5 )

        sbSizer171 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl1235 = wx.SpinCtrl( sbSizer171.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer171.Add( self.m_spinCtrl1235, 0, wx.ALL, 5 )

        self.m_slider6235 = wx.Slider( sbSizer171.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer171.Add( self.m_slider6235, 0, wx.ALL, 5 )

        self.m_checkBox1235 = wx.CheckBox( sbSizer171.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer171.Add( self.m_checkBox1235, 0, wx.ALL, 5 )

        self.m_checkBox2235 = wx.CheckBox( sbSizer171.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox2235.SetValue(True)
        sbSizer171.Add( self.m_checkBox2235, 0, wx.ALL, 5 )

        self.m_radioBtn2235 = wx.RadioButton( sbSizer171.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn2235.SetValue( True )
        sbSizer171.Add( self.m_radioBtn2235, 0, wx.ALL, 5 )

        self.m_radioBtn3235 = wx.RadioButton( sbSizer171.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer171.Add( self.m_radioBtn3235, 0, wx.ALL, 5 )


        ProgramInputs13.Add( sbSizer171, 1, wx.EXPAND, 5 )

        sbSizer172 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl1236 = wx.SpinCtrl( sbSizer172.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer172.Add( self.m_spinCtrl1236, 0, wx.ALL, 5 )

        self.m_slider6236 = wx.Slider( sbSizer172.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer172.Add( self.m_slider6236, 0, wx.ALL, 5 )

        self.m_checkBox1236 = wx.CheckBox( sbSizer172.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer172.Add( self.m_checkBox1236, 0, wx.ALL, 5 )

        self.m_checkBox2236 = wx.CheckBox( sbSizer172.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox2236.SetValue(True)
        sbSizer172.Add( self.m_checkBox2236, 0, wx.ALL, 5 )

        self.m_radioBtn2236 = wx.RadioButton( sbSizer172.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn2236.SetValue( True )
        sbSizer172.Add( self.m_radioBtn2236, 0, wx.ALL, 5 )

        self.m_radioBtn3236 = wx.RadioButton( sbSizer172.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer172.Add( self.m_radioBtn3236, 0, wx.ALL, 5 )


        ProgramInputs13.Add( sbSizer172, 1, wx.EXPAND, 5 )


        fgSizer453.Add( ProgramInputs13, 1, wx.EXPAND, 5 )

        ProgramOutputs13 = wx.StaticBoxSizer( wx.StaticBox( Program_1.GetStaticBox(), wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )

        bSizer1423 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle23 = wx.StaticText( ProgramOutputs13.GetStaticBox(), wx.ID_ANY, _(u"Valve"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle23.Wrap( -1 )

        bSizer1423.Add( self.OutputTitle23, 0, wx.ALL, 5 )

        self.m_gauge113 = wx.Gauge( ProgramOutputs13.GetStaticBox(), wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge113.SetValue( 0 )
        bSizer1423.Add( self.m_gauge113, 0, wx.ALL, 5 )


        ProgramOutputs13.Add( bSizer1423, 1, wx.EXPAND, 5 )

        bSizer14113 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle113 = wx.StaticText( ProgramOutputs13.GetStaticBox(), wx.ID_ANY, _(u"Pump"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle113.Wrap( -1 )

        bSizer14113.Add( self.OutputTitle113, 0, wx.ALL, 5 )

        self.m_toggleBtn113 = wx.ToggleButton( ProgramOutputs13.GetStaticBox(), wx.ID_ANY, _(u"MyButton"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_toggleBtn113.SetValue( True )
        bSizer14113.Add( self.m_toggleBtn113, 0, wx.ALL, 5 )


        ProgramOutputs13.Add( bSizer14113, 1, wx.EXPAND, 5 )


        fgSizer453.Add( ProgramOutputs13, 1, wx.EXPAND, 5 )


        Program_1.Add( fgSizer453, 1, 0, 5 )


        programsWrapSizer.Add( Program_1, 1, 0, 5 )

        Program_2 = wx.StaticBoxSizer( wx.StaticBox( self.mainScrollableWindow, wx.ID_ANY, _(u"Heating circuit 1") ), wx.VERTICAL )

        fgSizer45311 = wx.FlexGridSizer( 0, 1, 10, 0 )
        fgSizer45311.SetFlexibleDirection( wx.BOTH )
        fgSizer45311.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        ProgramInputs1311 = wx.StaticBoxSizer( wx.StaticBox( Program_2.GetStaticBox(), wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )

        sbSizer1731 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs1311.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl12311 = wx.SpinCtrl( sbSizer1731.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer1731.Add( self.m_spinCtrl12311, 0, wx.ALL, 5 )

        self.m_slider62311 = wx.Slider( sbSizer1731.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer1731.Add( self.m_slider62311, 0, wx.ALL, 5 )

        self.m_checkBox12311 = wx.CheckBox( sbSizer1731.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer1731.Add( self.m_checkBox12311, 0, wx.ALL, 5 )

        self.m_checkBox22311 = wx.CheckBox( sbSizer1731.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox22311.SetValue(True)
        sbSizer1731.Add( self.m_checkBox22311, 0, wx.ALL, 5 )

        self.m_radioBtn22311 = wx.RadioButton( sbSizer1731.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn22311.SetValue( True )
        sbSizer1731.Add( self.m_radioBtn22311, 0, wx.ALL, 5 )

        self.m_radioBtn32311 = wx.RadioButton( sbSizer1731.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer1731.Add( self.m_radioBtn32311, 0, wx.ALL, 5 )


        ProgramInputs1311.Add( sbSizer1731, 1, wx.EXPAND, 5 )

        sbSizer17111 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs1311.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl123511 = wx.SpinCtrl( sbSizer17111.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer17111.Add( self.m_spinCtrl123511, 0, wx.ALL, 5 )

        self.m_slider623511 = wx.Slider( sbSizer17111.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer17111.Add( self.m_slider623511, 0, wx.ALL, 5 )

        self.m_checkBox123511 = wx.CheckBox( sbSizer17111.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17111.Add( self.m_checkBox123511, 0, wx.ALL, 5 )

        self.m_checkBox223511 = wx.CheckBox( sbSizer17111.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox223511.SetValue(True)
        sbSizer17111.Add( self.m_checkBox223511, 0, wx.ALL, 5 )

        self.m_radioBtn223511 = wx.RadioButton( sbSizer17111.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn223511.SetValue( True )
        sbSizer17111.Add( self.m_radioBtn223511, 0, wx.ALL, 5 )

        self.m_radioBtn323511 = wx.RadioButton( sbSizer17111.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17111.Add( self.m_radioBtn323511, 0, wx.ALL, 5 )


        ProgramInputs1311.Add( sbSizer17111, 1, wx.EXPAND, 5 )

        sbSizer17211 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs1311.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl123611 = wx.SpinCtrl( sbSizer17211.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer17211.Add( self.m_spinCtrl123611, 0, wx.ALL, 5 )

        self.m_slider623611 = wx.Slider( sbSizer17211.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer17211.Add( self.m_slider623611, 0, wx.ALL, 5 )

        self.m_checkBox123611 = wx.CheckBox( sbSizer17211.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17211.Add( self.m_checkBox123611, 0, wx.ALL, 5 )

        self.m_checkBox223611 = wx.CheckBox( sbSizer17211.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox223611.SetValue(True)
        sbSizer17211.Add( self.m_checkBox223611, 0, wx.ALL, 5 )

        self.m_radioBtn223611 = wx.RadioButton( sbSizer17211.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn223611.SetValue( True )
        sbSizer17211.Add( self.m_radioBtn223611, 0, wx.ALL, 5 )

        self.m_radioBtn323611 = wx.RadioButton( sbSizer17211.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17211.Add( self.m_radioBtn323611, 0, wx.ALL, 5 )


        ProgramInputs1311.Add( sbSizer17211, 1, wx.EXPAND, 5 )


        fgSizer45311.Add( ProgramInputs1311, 1, wx.EXPAND, 5 )

        ProgramOutputs1311 = wx.StaticBoxSizer( wx.StaticBox( Program_2.GetStaticBox(), wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )

        bSizer142311 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle2311 = wx.StaticText( ProgramOutputs1311.GetStaticBox(), wx.ID_ANY, _(u"Valve"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle2311.Wrap( -1 )

        bSizer142311.Add( self.OutputTitle2311, 0, wx.ALL, 5 )

        self.m_gauge11311 = wx.Gauge( ProgramOutputs1311.GetStaticBox(), wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge11311.SetValue( 0 )
        bSizer142311.Add( self.m_gauge11311, 0, wx.ALL, 5 )


        ProgramOutputs1311.Add( bSizer142311, 1, wx.EXPAND, 5 )

        bSizer1411311 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle11311 = wx.StaticText( ProgramOutputs1311.GetStaticBox(), wx.ID_ANY, _(u"Pump"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle11311.Wrap( -1 )

        bSizer1411311.Add( self.OutputTitle11311, 0, wx.ALL, 5 )

        self.m_toggleBtn11311 = wx.ToggleButton( ProgramOutputs1311.GetStaticBox(), wx.ID_ANY, _(u"MyButton"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_toggleBtn11311.SetValue( True )
        bSizer1411311.Add( self.m_toggleBtn11311, 0, wx.ALL, 5 )


        ProgramOutputs1311.Add( bSizer1411311, 1, wx.EXPAND, 5 )


        fgSizer45311.Add( ProgramOutputs1311, 1, wx.EXPAND, 5 )


        Program_2.Add( fgSizer45311, 1, 0, 5 )


        programsWrapSizer.Add( Program_2, 1, 0, 5 )

        Program_3 = wx.StaticBoxSizer( wx.StaticBox( self.mainScrollableWindow, wx.ID_ANY, _(u"Heating circuit 1") ), wx.VERTICAL )

        fgSizer45312 = wx.FlexGridSizer( 0, 1, 10, 0 )
        fgSizer45312.SetFlexibleDirection( wx.BOTH )
        fgSizer45312.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        ProgramInputs1312 = wx.StaticBoxSizer( wx.StaticBox( Program_3.GetStaticBox(), wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )

        sbSizer1732 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs1312.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl12312 = wx.SpinCtrl( sbSizer1732.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer1732.Add( self.m_spinCtrl12312, 0, wx.ALL, 5 )

        self.m_slider62312 = wx.Slider( sbSizer1732.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer1732.Add( self.m_slider62312, 0, wx.ALL, 5 )

        self.m_checkBox12312 = wx.CheckBox( sbSizer1732.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer1732.Add( self.m_checkBox12312, 0, wx.ALL, 5 )

        self.m_checkBox22312 = wx.CheckBox( sbSizer1732.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox22312.SetValue(True)
        sbSizer1732.Add( self.m_checkBox22312, 0, wx.ALL, 5 )

        self.m_radioBtn22312 = wx.RadioButton( sbSizer1732.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn22312.SetValue( True )
        sbSizer1732.Add( self.m_radioBtn22312, 0, wx.ALL, 5 )

        self.m_radioBtn32312 = wx.RadioButton( sbSizer1732.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer1732.Add( self.m_radioBtn32312, 0, wx.ALL, 5 )


        ProgramInputs1312.Add( sbSizer1732, 1, wx.EXPAND, 5 )

        sbSizer17112 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs1312.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl123512 = wx.SpinCtrl( sbSizer17112.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer17112.Add( self.m_spinCtrl123512, 0, wx.ALL, 5 )

        self.m_slider623512 = wx.Slider( sbSizer17112.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer17112.Add( self.m_slider623512, 0, wx.ALL, 5 )

        self.m_checkBox123512 = wx.CheckBox( sbSizer17112.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17112.Add( self.m_checkBox123512, 0, wx.ALL, 5 )

        self.m_checkBox223512 = wx.CheckBox( sbSizer17112.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox223512.SetValue(True)
        sbSizer17112.Add( self.m_checkBox223512, 0, wx.ALL, 5 )

        self.m_radioBtn223512 = wx.RadioButton( sbSizer17112.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn223512.SetValue( True )
        sbSizer17112.Add( self.m_radioBtn223512, 0, wx.ALL, 5 )

        self.m_radioBtn323512 = wx.RadioButton( sbSizer17112.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17112.Add( self.m_radioBtn323512, 0, wx.ALL, 5 )


        ProgramInputs1312.Add( sbSizer17112, 1, wx.EXPAND, 5 )

        sbSizer17212 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs1312.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl123612 = wx.SpinCtrl( sbSizer17212.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer17212.Add( self.m_spinCtrl123612, 0, wx.ALL, 5 )

        self.m_slider623612 = wx.Slider( sbSizer17212.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer17212.Add( self.m_slider623612, 0, wx.ALL, 5 )

        self.m_checkBox123612 = wx.CheckBox( sbSizer17212.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17212.Add( self.m_checkBox123612, 0, wx.ALL, 5 )

        self.m_checkBox223612 = wx.CheckBox( sbSizer17212.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox223612.SetValue(True)
        sbSizer17212.Add( self.m_checkBox223612, 0, wx.ALL, 5 )

        self.m_radioBtn223612 = wx.RadioButton( sbSizer17212.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn223612.SetValue( True )
        sbSizer17212.Add( self.m_radioBtn223612, 0, wx.ALL, 5 )

        self.m_radioBtn323612 = wx.RadioButton( sbSizer17212.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17212.Add( self.m_radioBtn323612, 0, wx.ALL, 5 )


        ProgramInputs1312.Add( sbSizer17212, 1, wx.EXPAND, 5 )


        fgSizer45312.Add( ProgramInputs1312, 1, wx.EXPAND, 5 )

        ProgramOutputs1312 = wx.StaticBoxSizer( wx.StaticBox( Program_3.GetStaticBox(), wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )

        bSizer142312 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle2312 = wx.StaticText( ProgramOutputs1312.GetStaticBox(), wx.ID_ANY, _(u"Valve"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle2312.Wrap( -1 )

        bSizer142312.Add( self.OutputTitle2312, 0, wx.ALL, 5 )

        self.m_gauge11312 = wx.Gauge( ProgramOutputs1312.GetStaticBox(), wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge11312.SetValue( 0 )
        bSizer142312.Add( self.m_gauge11312, 0, wx.ALL, 5 )


        ProgramOutputs1312.Add( bSizer142312, 1, wx.EXPAND, 5 )

        bSizer1411312 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle11312 = wx.StaticText( ProgramOutputs1312.GetStaticBox(), wx.ID_ANY, _(u"Pump"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle11312.Wrap( -1 )

        bSizer1411312.Add( self.OutputTitle11312, 0, wx.ALL, 5 )

        self.m_toggleBtn11312 = wx.ToggleButton( ProgramOutputs1312.GetStaticBox(), wx.ID_ANY, _(u"MyButton"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_toggleBtn11312.SetValue( True )
        bSizer1411312.Add( self.m_toggleBtn11312, 0, wx.ALL, 5 )


        ProgramOutputs1312.Add( bSizer1411312, 1, wx.EXPAND, 5 )


        fgSizer45312.Add( ProgramOutputs1312, 1, wx.EXPAND, 5 )


        Program_3.Add( fgSizer45312, 1, 0, 5 )


        programsWrapSizer.Add( Program_3, 1, 0, 5 )

        Program_4 = wx.StaticBoxSizer( wx.StaticBox( self.mainScrollableWindow, wx.ID_ANY, _(u"Heating circuit 1") ), wx.VERTICAL )

        fgSizer45313 = wx.FlexGridSizer( 0, 1, 10, 0 )
        fgSizer45313.SetFlexibleDirection( wx.BOTH )
        fgSizer45313.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        ProgramInputs1313 = wx.StaticBoxSizer( wx.StaticBox( Program_4.GetStaticBox(), wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )

        sbSizer1733 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs1313.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl12313 = wx.SpinCtrl( sbSizer1733.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer1733.Add( self.m_spinCtrl12313, 0, wx.ALL, 5 )

        self.m_slider62313 = wx.Slider( sbSizer1733.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer1733.Add( self.m_slider62313, 0, wx.ALL, 5 )

        self.m_checkBox12313 = wx.CheckBox( sbSizer1733.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer1733.Add( self.m_checkBox12313, 0, wx.ALL, 5 )

        self.m_checkBox22313 = wx.CheckBox( sbSizer1733.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox22313.SetValue(True)
        sbSizer1733.Add( self.m_checkBox22313, 0, wx.ALL, 5 )

        self.m_radioBtn22313 = wx.RadioButton( sbSizer1733.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn22313.SetValue( True )
        sbSizer1733.Add( self.m_radioBtn22313, 0, wx.ALL, 5 )

        self.m_radioBtn32313 = wx.RadioButton( sbSizer1733.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer1733.Add( self.m_radioBtn32313, 0, wx.ALL, 5 )


        ProgramInputs1313.Add( sbSizer1733, 1, wx.EXPAND, 5 )

        sbSizer17113 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs1313.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl123513 = wx.SpinCtrl( sbSizer17113.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer17113.Add( self.m_spinCtrl123513, 0, wx.ALL, 5 )

        self.m_slider623513 = wx.Slider( sbSizer17113.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer17113.Add( self.m_slider623513, 0, wx.ALL, 5 )

        self.m_checkBox123513 = wx.CheckBox( sbSizer17113.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17113.Add( self.m_checkBox123513, 0, wx.ALL, 5 )

        self.m_checkBox223513 = wx.CheckBox( sbSizer17113.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox223513.SetValue(True)
        sbSizer17113.Add( self.m_checkBox223513, 0, wx.ALL, 5 )

        self.m_radioBtn223513 = wx.RadioButton( sbSizer17113.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn223513.SetValue( True )
        sbSizer17113.Add( self.m_radioBtn223513, 0, wx.ALL, 5 )

        self.m_radioBtn323513 = wx.RadioButton( sbSizer17113.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17113.Add( self.m_radioBtn323513, 0, wx.ALL, 5 )


        ProgramInputs1313.Add( sbSizer17113, 1, wx.EXPAND, 5 )

        sbSizer17213 = wx.StaticBoxSizer( wx.StaticBox( ProgramInputs1313.GetStaticBox(), wx.ID_ANY, _(u"label") ), wx.HORIZONTAL )

        self.m_spinCtrl123613 = wx.SpinCtrl( sbSizer17213.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        sbSizer17213.Add( self.m_spinCtrl123613, 0, wx.ALL, 5 )

        self.m_slider623613 = wx.Slider( sbSizer17213.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer17213.Add( self.m_slider623613, 0, wx.ALL, 5 )

        self.m_checkBox123613 = wx.CheckBox( sbSizer17213.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17213.Add( self.m_checkBox123613, 0, wx.ALL, 5 )

        self.m_checkBox223613 = wx.CheckBox( sbSizer17213.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox223613.SetValue(True)
        sbSizer17213.Add( self.m_checkBox223613, 0, wx.ALL, 5 )

        self.m_radioBtn223613 = wx.RadioButton( sbSizer17213.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn223613.SetValue( True )
        sbSizer17213.Add( self.m_radioBtn223613, 0, wx.ALL, 5 )

        self.m_radioBtn323613 = wx.RadioButton( sbSizer17213.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer17213.Add( self.m_radioBtn323613, 0, wx.ALL, 5 )


        ProgramInputs1313.Add( sbSizer17213, 1, wx.EXPAND, 5 )


        fgSizer45313.Add( ProgramInputs1313, 1, wx.EXPAND, 5 )

        ProgramOutputs1313 = wx.StaticBoxSizer( wx.StaticBox( Program_4.GetStaticBox(), wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )

        bSizer142313 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle2313 = wx.StaticText( ProgramOutputs1313.GetStaticBox(), wx.ID_ANY, _(u"Valve"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle2313.Wrap( -1 )

        bSizer142313.Add( self.OutputTitle2313, 0, wx.ALL, 5 )

        self.m_gauge11313 = wx.Gauge( ProgramOutputs1313.GetStaticBox(), wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge11313.SetValue( 0 )
        bSizer142313.Add( self.m_gauge11313, 0, wx.ALL, 5 )


        ProgramOutputs1313.Add( bSizer142313, 1, wx.EXPAND, 5 )

        bSizer1411313 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle11313 = wx.StaticText( ProgramOutputs1313.GetStaticBox(), wx.ID_ANY, _(u"Pump"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle11313.Wrap( -1 )

        bSizer1411313.Add( self.OutputTitle11313, 0, wx.ALL, 5 )

        self.m_toggleBtn11313 = wx.ToggleButton( ProgramOutputs1313.GetStaticBox(), wx.ID_ANY, _(u"MyButton"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_toggleBtn11313.SetValue( True )
        bSizer1411313.Add( self.m_toggleBtn11313, 0, wx.ALL, 5 )


        ProgramOutputs1313.Add( bSizer1411313, 1, wx.EXPAND, 5 )


        fgSizer45313.Add( ProgramOutputs1313, 1, wx.EXPAND, 5 )


        Program_4.Add( fgSizer45313, 1, 0, 5 )


        programsWrapSizer.Add( Program_4, 1, 0, 5 )


        self.mainScrollableWindow.SetSizer( programsWrapSizer )
        self.mainScrollableWindow.Layout()
        mainBoxSizer.Add( self.mainScrollableWindow, 1, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( mainBoxSizer )
        self.Layout()

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


