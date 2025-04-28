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
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 854,763 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.Size( 500,400 ), wx.DefaultSize )

        mainBoxSizer = wx.BoxSizer( wx.VERTICAL )

        mainBoxSizer.SetMinSize( wx.Size( 640,-1 ) )
        self.mainScrollableWindow = wx.ScrolledWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 640,480 ), wx.HSCROLL|wx.VSCROLL )
        self.mainScrollableWindow.SetScrollRate( 5, 5 )
        programsWrapSizer = wx.WrapSizer( wx.VERTICAL, wx.WRAPSIZER_DEFAULT_FLAGS )

        programsWrapSizer.SetMinSize( wx.Size( 640,480 ) )
        Program_1 = wx.StaticBoxSizer( wx.StaticBox( self.mainScrollableWindow, wx.ID_ANY, _(u"Heating circuit 1") ), wx.VERTICAL )

        fgSizer453 = wx.FlexGridSizer( 0, 1, 0, 0 )
        fgSizer453.SetFlexibleDirection( wx.BOTH )
        fgSizer453.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        ProgramInputs13 = wx.StaticBoxSizer( wx.StaticBox( Program_1.GetStaticBox(), wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )

        Sensor0_value23 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText123 = wx.StaticText( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText123.Wrap( -1 )

        Sensor0_value23.Add( self.m_staticText123, 0, wx.ALL, 5 )

        self.m_spinCtrl123 = wx.SpinCtrl( ProgramInputs13.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value23.Add( self.m_spinCtrl123, 0, wx.ALL, 5 )

        self.m_slider623 = wx.Slider( ProgramInputs13.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value23.Add( self.m_slider623, 0, wx.ALL, 5 )

        self.m_checkBox123 = wx.CheckBox( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value23.Add( self.m_checkBox123, 0, wx.ALL, 5 )

        self.m_checkBox223 = wx.CheckBox( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox223.SetValue(True)
        Sensor0_value23.Add( self.m_checkBox223, 0, wx.ALL, 5 )

        self.m_radioBtn223 = wx.RadioButton( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn223.SetValue( True )
        Sensor0_value23.Add( self.m_radioBtn223, 0, wx.ALL, 5 )

        self.m_radioBtn323 = wx.RadioButton( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value23.Add( self.m_radioBtn323, 0, wx.ALL, 5 )


        ProgramInputs13.Add( Sensor0_value23, 1, wx.EXPAND, 5 )

        Sensor0_value133 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText1133 = wx.StaticText( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1133.Wrap( -1 )

        Sensor0_value133.Add( self.m_staticText1133, 0, wx.ALL, 5 )

        self.m_spinCtrl1133 = wx.SpinCtrl( ProgramInputs13.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value133.Add( self.m_spinCtrl1133, 0, wx.ALL, 5 )

        self.m_slider6133 = wx.Slider( ProgramInputs13.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value133.Add( self.m_slider6133, 0, wx.ALL, 5 )

        self.m_checkBox1133 = wx.CheckBox( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value133.Add( self.m_checkBox1133, 0, wx.ALL, 5 )

        self.m_checkBox2133 = wx.CheckBox( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox2133.SetValue(True)
        Sensor0_value133.Add( self.m_checkBox2133, 0, wx.ALL, 5 )

        self.m_radioBtn2123 = wx.RadioButton( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn2123.SetValue( True )
        Sensor0_value133.Add( self.m_radioBtn2123, 0, wx.ALL, 5 )

        self.m_radioBtn3123 = wx.RadioButton( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value133.Add( self.m_radioBtn3123, 0, wx.ALL, 5 )


        ProgramInputs13.Add( Sensor0_value133, 1, wx.EXPAND, 5 )

        Sensor0_value1113 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText11113 = wx.StaticText( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText11113.Wrap( -1 )

        Sensor0_value1113.Add( self.m_staticText11113, 0, wx.ALL, 5 )

        self.m_spinCtrl11113 = wx.SpinCtrl( ProgramInputs13.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value1113.Add( self.m_spinCtrl11113, 0, wx.ALL, 5 )

        self.m_slider61113 = wx.Slider( ProgramInputs13.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value1113.Add( self.m_slider61113, 0, wx.ALL, 5 )

        self.m_checkBox11113 = wx.CheckBox( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1113.Add( self.m_checkBox11113, 0, wx.ALL, 5 )

        self.m_checkBox21113 = wx.CheckBox( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox21113.SetValue(True)
        Sensor0_value1113.Add( self.m_checkBox21113, 0, wx.ALL, 5 )

        self.m_radioBtn21123 = wx.RadioButton( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn21123.SetValue( True )
        Sensor0_value1113.Add( self.m_radioBtn21123, 0, wx.ALL, 5 )

        self.m_radioBtn31123 = wx.RadioButton( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1113.Add( self.m_radioBtn31123, 0, wx.ALL, 5 )


        ProgramInputs13.Add( Sensor0_value1113, 1, wx.EXPAND, 5 )

        Sensor0_value1213 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText11213 = wx.StaticText( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText11213.Wrap( -1 )

        Sensor0_value1213.Add( self.m_staticText11213, 0, wx.ALL, 5 )

        self.m_spinCtrl11213 = wx.SpinCtrl( ProgramInputs13.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value1213.Add( self.m_spinCtrl11213, 0, wx.ALL, 5 )

        self.m_slider61213 = wx.Slider( ProgramInputs13.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value1213.Add( self.m_slider61213, 0, wx.ALL, 5 )

        self.m_checkBox11213 = wx.CheckBox( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1213.Add( self.m_checkBox11213, 0, wx.ALL, 5 )

        self.m_checkBox21213 = wx.CheckBox( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox21213.SetValue(True)
        Sensor0_value1213.Add( self.m_checkBox21213, 0, wx.ALL, 5 )

        self.m_radioBtn211113 = wx.RadioButton( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn211113.SetValue( True )
        Sensor0_value1213.Add( self.m_radioBtn211113, 0, wx.ALL, 5 )

        self.m_radioBtn311113 = wx.RadioButton( ProgramInputs13.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1213.Add( self.m_radioBtn311113, 0, wx.ALL, 5 )


        ProgramInputs13.Add( Sensor0_value1213, 1, wx.EXPAND, 5 )


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


        Program_1.Add( fgSizer453, 1, wx.EXPAND, 5 )


        programsWrapSizer.Add( Program_1, 1, wx.EXPAND, 5 )

        Program_2 = wx.StaticBoxSizer( wx.StaticBox( self.mainScrollableWindow, wx.ID_ANY, _(u"Heating circuit 1") ), wx.VERTICAL )

        fgSizer4534 = wx.FlexGridSizer( 0, 1, 0, 0 )
        fgSizer4534.SetFlexibleDirection( wx.BOTH )
        fgSizer4534.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        ProgramInputs134 = wx.StaticBoxSizer( wx.StaticBox( Program_2.GetStaticBox(), wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )

        Sensor0_value234 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText1234 = wx.StaticText( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1234.Wrap( -1 )

        Sensor0_value234.Add( self.m_staticText1234, 0, wx.ALL, 5 )

        self.m_spinCtrl1234 = wx.SpinCtrl( ProgramInputs134.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value234.Add( self.m_spinCtrl1234, 0, wx.ALL, 5 )

        self.m_slider6234 = wx.Slider( ProgramInputs134.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value234.Add( self.m_slider6234, 0, wx.ALL, 5 )

        self.m_checkBox1234 = wx.CheckBox( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value234.Add( self.m_checkBox1234, 0, wx.ALL, 5 )

        self.m_checkBox2234 = wx.CheckBox( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox2234.SetValue(True)
        Sensor0_value234.Add( self.m_checkBox2234, 0, wx.ALL, 5 )

        self.m_radioBtn2234 = wx.RadioButton( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn2234.SetValue( True )
        Sensor0_value234.Add( self.m_radioBtn2234, 0, wx.ALL, 5 )

        self.m_radioBtn3234 = wx.RadioButton( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value234.Add( self.m_radioBtn3234, 0, wx.ALL, 5 )


        ProgramInputs134.Add( Sensor0_value234, 1, wx.EXPAND, 5 )

        Sensor0_value1334 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText11334 = wx.StaticText( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText11334.Wrap( -1 )

        Sensor0_value1334.Add( self.m_staticText11334, 0, wx.ALL, 5 )

        self.m_spinCtrl11334 = wx.SpinCtrl( ProgramInputs134.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value1334.Add( self.m_spinCtrl11334, 0, wx.ALL, 5 )

        self.m_slider61334 = wx.Slider( ProgramInputs134.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value1334.Add( self.m_slider61334, 0, wx.ALL, 5 )

        self.m_checkBox11334 = wx.CheckBox( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1334.Add( self.m_checkBox11334, 0, wx.ALL, 5 )

        self.m_checkBox21334 = wx.CheckBox( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox21334.SetValue(True)
        Sensor0_value1334.Add( self.m_checkBox21334, 0, wx.ALL, 5 )

        self.m_radioBtn21234 = wx.RadioButton( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn21234.SetValue( True )
        Sensor0_value1334.Add( self.m_radioBtn21234, 0, wx.ALL, 5 )

        self.m_radioBtn31234 = wx.RadioButton( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1334.Add( self.m_radioBtn31234, 0, wx.ALL, 5 )


        ProgramInputs134.Add( Sensor0_value1334, 1, wx.EXPAND, 5 )

        Sensor0_value11134 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText111134 = wx.StaticText( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText111134.Wrap( -1 )

        Sensor0_value11134.Add( self.m_staticText111134, 0, wx.ALL, 5 )

        self.m_spinCtrl111134 = wx.SpinCtrl( ProgramInputs134.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value11134.Add( self.m_spinCtrl111134, 0, wx.ALL, 5 )

        self.m_slider611134 = wx.Slider( ProgramInputs134.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value11134.Add( self.m_slider611134, 0, wx.ALL, 5 )

        self.m_checkBox111134 = wx.CheckBox( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value11134.Add( self.m_checkBox111134, 0, wx.ALL, 5 )

        self.m_checkBox211134 = wx.CheckBox( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox211134.SetValue(True)
        Sensor0_value11134.Add( self.m_checkBox211134, 0, wx.ALL, 5 )

        self.m_radioBtn211234 = wx.RadioButton( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn211234.SetValue( True )
        Sensor0_value11134.Add( self.m_radioBtn211234, 0, wx.ALL, 5 )

        self.m_radioBtn311234 = wx.RadioButton( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value11134.Add( self.m_radioBtn311234, 0, wx.ALL, 5 )


        ProgramInputs134.Add( Sensor0_value11134, 1, wx.EXPAND, 5 )

        Sensor0_value12134 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText112134 = wx.StaticText( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText112134.Wrap( -1 )

        Sensor0_value12134.Add( self.m_staticText112134, 0, wx.ALL, 5 )

        self.m_spinCtrl112134 = wx.SpinCtrl( ProgramInputs134.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value12134.Add( self.m_spinCtrl112134, 0, wx.ALL, 5 )

        self.m_slider612134 = wx.Slider( ProgramInputs134.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value12134.Add( self.m_slider612134, 0, wx.ALL, 5 )

        self.m_checkBox112134 = wx.CheckBox( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value12134.Add( self.m_checkBox112134, 0, wx.ALL, 5 )

        self.m_checkBox212134 = wx.CheckBox( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox212134.SetValue(True)
        Sensor0_value12134.Add( self.m_checkBox212134, 0, wx.ALL, 5 )

        self.m_radioBtn2111134 = wx.RadioButton( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn2111134.SetValue( True )
        Sensor0_value12134.Add( self.m_radioBtn2111134, 0, wx.ALL, 5 )

        self.m_radioBtn3111134 = wx.RadioButton( ProgramInputs134.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value12134.Add( self.m_radioBtn3111134, 0, wx.ALL, 5 )


        ProgramInputs134.Add( Sensor0_value12134, 1, wx.EXPAND, 5 )


        fgSizer4534.Add( ProgramInputs134, 1, wx.EXPAND, 5 )

        ProgramOutputs134 = wx.StaticBoxSizer( wx.StaticBox( Program_2.GetStaticBox(), wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )

        bSizer14234 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle234 = wx.StaticText( ProgramOutputs134.GetStaticBox(), wx.ID_ANY, _(u"Valve"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle234.Wrap( -1 )

        bSizer14234.Add( self.OutputTitle234, 0, wx.ALL, 5 )

        self.m_gauge1134 = wx.Gauge( ProgramOutputs134.GetStaticBox(), wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge1134.SetValue( 0 )
        bSizer14234.Add( self.m_gauge1134, 0, wx.ALL, 5 )


        ProgramOutputs134.Add( bSizer14234, 1, wx.EXPAND, 5 )

        bSizer141134 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle1134 = wx.StaticText( ProgramOutputs134.GetStaticBox(), wx.ID_ANY, _(u"Pump"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle1134.Wrap( -1 )

        bSizer141134.Add( self.OutputTitle1134, 0, wx.ALL, 5 )

        self.m_toggleBtn1134 = wx.ToggleButton( ProgramOutputs134.GetStaticBox(), wx.ID_ANY, _(u"MyButton"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_toggleBtn1134.SetValue( True )
        bSizer141134.Add( self.m_toggleBtn1134, 0, wx.ALL, 5 )


        ProgramOutputs134.Add( bSizer141134, 1, wx.EXPAND, 5 )


        fgSizer4534.Add( ProgramOutputs134, 1, wx.EXPAND, 5 )


        Program_2.Add( fgSizer4534, 1, wx.EXPAND, 5 )


        programsWrapSizer.Add( Program_2, 1, wx.EXPAND, 5 )

        Program_3 = wx.StaticBoxSizer( wx.StaticBox( self.mainScrollableWindow, wx.ID_ANY, _(u"Heating circuit 1") ), wx.VERTICAL )

        fgSizer4533 = wx.FlexGridSizer( 0, 1, 0, 0 )
        fgSizer4533.SetFlexibleDirection( wx.BOTH )
        fgSizer4533.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        ProgramInputs133 = wx.StaticBoxSizer( wx.StaticBox( Program_3.GetStaticBox(), wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )

        Sensor0_value233 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText1233 = wx.StaticText( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1233.Wrap( -1 )

        Sensor0_value233.Add( self.m_staticText1233, 0, wx.ALL, 5 )

        self.m_spinCtrl1233 = wx.SpinCtrl( ProgramInputs133.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value233.Add( self.m_spinCtrl1233, 0, wx.ALL, 5 )

        self.m_slider6233 = wx.Slider( ProgramInputs133.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value233.Add( self.m_slider6233, 0, wx.ALL, 5 )

        self.m_checkBox1233 = wx.CheckBox( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value233.Add( self.m_checkBox1233, 0, wx.ALL, 5 )

        self.m_checkBox2233 = wx.CheckBox( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox2233.SetValue(True)
        Sensor0_value233.Add( self.m_checkBox2233, 0, wx.ALL, 5 )

        self.m_radioBtn2233 = wx.RadioButton( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn2233.SetValue( True )
        Sensor0_value233.Add( self.m_radioBtn2233, 0, wx.ALL, 5 )

        self.m_radioBtn3233 = wx.RadioButton( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value233.Add( self.m_radioBtn3233, 0, wx.ALL, 5 )


        ProgramInputs133.Add( Sensor0_value233, 1, wx.EXPAND, 5 )

        Sensor0_value1333 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText11333 = wx.StaticText( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText11333.Wrap( -1 )

        Sensor0_value1333.Add( self.m_staticText11333, 0, wx.ALL, 5 )

        self.m_spinCtrl11333 = wx.SpinCtrl( ProgramInputs133.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value1333.Add( self.m_spinCtrl11333, 0, wx.ALL, 5 )

        self.m_slider61333 = wx.Slider( ProgramInputs133.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value1333.Add( self.m_slider61333, 0, wx.ALL, 5 )

        self.m_checkBox11333 = wx.CheckBox( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1333.Add( self.m_checkBox11333, 0, wx.ALL, 5 )

        self.m_checkBox21333 = wx.CheckBox( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox21333.SetValue(True)
        Sensor0_value1333.Add( self.m_checkBox21333, 0, wx.ALL, 5 )

        self.m_radioBtn21233 = wx.RadioButton( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn21233.SetValue( True )
        Sensor0_value1333.Add( self.m_radioBtn21233, 0, wx.ALL, 5 )

        self.m_radioBtn31233 = wx.RadioButton( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1333.Add( self.m_radioBtn31233, 0, wx.ALL, 5 )


        ProgramInputs133.Add( Sensor0_value1333, 1, wx.EXPAND, 5 )

        Sensor0_value11133 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText111133 = wx.StaticText( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText111133.Wrap( -1 )

        Sensor0_value11133.Add( self.m_staticText111133, 0, wx.ALL, 5 )

        self.m_spinCtrl111133 = wx.SpinCtrl( ProgramInputs133.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value11133.Add( self.m_spinCtrl111133, 0, wx.ALL, 5 )

        self.m_slider611133 = wx.Slider( ProgramInputs133.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value11133.Add( self.m_slider611133, 0, wx.ALL, 5 )

        self.m_checkBox111133 = wx.CheckBox( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value11133.Add( self.m_checkBox111133, 0, wx.ALL, 5 )

        self.m_checkBox211133 = wx.CheckBox( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox211133.SetValue(True)
        Sensor0_value11133.Add( self.m_checkBox211133, 0, wx.ALL, 5 )

        self.m_radioBtn211233 = wx.RadioButton( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn211233.SetValue( True )
        Sensor0_value11133.Add( self.m_radioBtn211233, 0, wx.ALL, 5 )

        self.m_radioBtn311233 = wx.RadioButton( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value11133.Add( self.m_radioBtn311233, 0, wx.ALL, 5 )


        ProgramInputs133.Add( Sensor0_value11133, 1, wx.EXPAND, 5 )

        Sensor0_value12133 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText112133 = wx.StaticText( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText112133.Wrap( -1 )

        Sensor0_value12133.Add( self.m_staticText112133, 0, wx.ALL, 5 )

        self.m_spinCtrl112133 = wx.SpinCtrl( ProgramInputs133.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value12133.Add( self.m_spinCtrl112133, 0, wx.ALL, 5 )

        self.m_slider612133 = wx.Slider( ProgramInputs133.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value12133.Add( self.m_slider612133, 0, wx.ALL, 5 )

        self.m_checkBox112133 = wx.CheckBox( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value12133.Add( self.m_checkBox112133, 0, wx.ALL, 5 )

        self.m_checkBox212133 = wx.CheckBox( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox212133.SetValue(True)
        Sensor0_value12133.Add( self.m_checkBox212133, 0, wx.ALL, 5 )

        self.m_radioBtn2111133 = wx.RadioButton( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn2111133.SetValue( True )
        Sensor0_value12133.Add( self.m_radioBtn2111133, 0, wx.ALL, 5 )

        self.m_radioBtn3111133 = wx.RadioButton( ProgramInputs133.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value12133.Add( self.m_radioBtn3111133, 0, wx.ALL, 5 )


        ProgramInputs133.Add( Sensor0_value12133, 1, wx.EXPAND, 5 )


        fgSizer4533.Add( ProgramInputs133, 1, wx.EXPAND, 5 )

        ProgramOutputs133 = wx.StaticBoxSizer( wx.StaticBox( Program_3.GetStaticBox(), wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )

        bSizer14233 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle233 = wx.StaticText( ProgramOutputs133.GetStaticBox(), wx.ID_ANY, _(u"Valve"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle233.Wrap( -1 )

        bSizer14233.Add( self.OutputTitle233, 0, wx.ALL, 5 )

        self.m_gauge1133 = wx.Gauge( ProgramOutputs133.GetStaticBox(), wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge1133.SetValue( 0 )
        bSizer14233.Add( self.m_gauge1133, 0, wx.ALL, 5 )


        ProgramOutputs133.Add( bSizer14233, 1, wx.EXPAND, 5 )

        bSizer141133 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle1133 = wx.StaticText( ProgramOutputs133.GetStaticBox(), wx.ID_ANY, _(u"Pump"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle1133.Wrap( -1 )

        bSizer141133.Add( self.OutputTitle1133, 0, wx.ALL, 5 )

        self.m_toggleBtn1133 = wx.ToggleButton( ProgramOutputs133.GetStaticBox(), wx.ID_ANY, _(u"MyButton"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_toggleBtn1133.SetValue( True )
        bSizer141133.Add( self.m_toggleBtn1133, 0, wx.ALL, 5 )


        ProgramOutputs133.Add( bSizer141133, 1, wx.EXPAND, 5 )


        fgSizer4533.Add( ProgramOutputs133, 1, wx.EXPAND, 5 )


        Program_3.Add( fgSizer4533, 1, wx.EXPAND, 5 )


        programsWrapSizer.Add( Program_3, 1, wx.EXPAND, 5 )

        Program_4 = wx.StaticBoxSizer( wx.StaticBox( self.mainScrollableWindow, wx.ID_ANY, _(u"Heating circuit 1") ), wx.VERTICAL )

        fgSizer4532 = wx.FlexGridSizer( 0, 1, 0, 0 )
        fgSizer4532.SetFlexibleDirection( wx.BOTH )
        fgSizer4532.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        ProgramInputs132 = wx.StaticBoxSizer( wx.StaticBox( Program_4.GetStaticBox(), wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )

        Sensor0_value232 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText1232 = wx.StaticText( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1232.Wrap( -1 )

        Sensor0_value232.Add( self.m_staticText1232, 0, wx.ALL, 5 )

        self.m_spinCtrl1232 = wx.SpinCtrl( ProgramInputs132.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value232.Add( self.m_spinCtrl1232, 0, wx.ALL, 5 )

        self.m_slider6232 = wx.Slider( ProgramInputs132.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value232.Add( self.m_slider6232, 0, wx.ALL, 5 )

        self.m_checkBox1232 = wx.CheckBox( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value232.Add( self.m_checkBox1232, 0, wx.ALL, 5 )

        self.m_checkBox2232 = wx.CheckBox( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox2232.SetValue(True)
        Sensor0_value232.Add( self.m_checkBox2232, 0, wx.ALL, 5 )

        self.m_radioBtn2232 = wx.RadioButton( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn2232.SetValue( True )
        Sensor0_value232.Add( self.m_radioBtn2232, 0, wx.ALL, 5 )

        self.m_radioBtn3232 = wx.RadioButton( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value232.Add( self.m_radioBtn3232, 0, wx.ALL, 5 )


        ProgramInputs132.Add( Sensor0_value232, 1, wx.EXPAND, 5 )

        Sensor0_value1332 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText11332 = wx.StaticText( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText11332.Wrap( -1 )

        Sensor0_value1332.Add( self.m_staticText11332, 0, wx.ALL, 5 )

        self.m_spinCtrl11332 = wx.SpinCtrl( ProgramInputs132.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value1332.Add( self.m_spinCtrl11332, 0, wx.ALL, 5 )

        self.m_slider61332 = wx.Slider( ProgramInputs132.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value1332.Add( self.m_slider61332, 0, wx.ALL, 5 )

        self.m_checkBox11332 = wx.CheckBox( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1332.Add( self.m_checkBox11332, 0, wx.ALL, 5 )

        self.m_checkBox21332 = wx.CheckBox( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox21332.SetValue(True)
        Sensor0_value1332.Add( self.m_checkBox21332, 0, wx.ALL, 5 )

        self.m_radioBtn21232 = wx.RadioButton( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn21232.SetValue( True )
        Sensor0_value1332.Add( self.m_radioBtn21232, 0, wx.ALL, 5 )

        self.m_radioBtn31232 = wx.RadioButton( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1332.Add( self.m_radioBtn31232, 0, wx.ALL, 5 )


        ProgramInputs132.Add( Sensor0_value1332, 1, wx.EXPAND, 5 )

        Sensor0_value11132 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText111132 = wx.StaticText( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText111132.Wrap( -1 )

        Sensor0_value11132.Add( self.m_staticText111132, 0, wx.ALL, 5 )

        self.m_spinCtrl111132 = wx.SpinCtrl( ProgramInputs132.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value11132.Add( self.m_spinCtrl111132, 0, wx.ALL, 5 )

        self.m_slider611132 = wx.Slider( ProgramInputs132.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value11132.Add( self.m_slider611132, 0, wx.ALL, 5 )

        self.m_checkBox111132 = wx.CheckBox( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value11132.Add( self.m_checkBox111132, 0, wx.ALL, 5 )

        self.m_checkBox211132 = wx.CheckBox( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox211132.SetValue(True)
        Sensor0_value11132.Add( self.m_checkBox211132, 0, wx.ALL, 5 )

        self.m_radioBtn211232 = wx.RadioButton( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn211232.SetValue( True )
        Sensor0_value11132.Add( self.m_radioBtn211232, 0, wx.ALL, 5 )

        self.m_radioBtn311232 = wx.RadioButton( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value11132.Add( self.m_radioBtn311232, 0, wx.ALL, 5 )


        ProgramInputs132.Add( Sensor0_value11132, 1, wx.EXPAND, 5 )

        Sensor0_value12132 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText112132 = wx.StaticText( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText112132.Wrap( -1 )

        Sensor0_value12132.Add( self.m_staticText112132, 0, wx.ALL, 5 )

        self.m_spinCtrl112132 = wx.SpinCtrl( ProgramInputs132.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value12132.Add( self.m_spinCtrl112132, 0, wx.ALL, 5 )

        self.m_slider612132 = wx.Slider( ProgramInputs132.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value12132.Add( self.m_slider612132, 0, wx.ALL, 5 )

        self.m_checkBox112132 = wx.CheckBox( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value12132.Add( self.m_checkBox112132, 0, wx.ALL, 5 )

        self.m_checkBox212132 = wx.CheckBox( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox212132.SetValue(True)
        Sensor0_value12132.Add( self.m_checkBox212132, 0, wx.ALL, 5 )

        self.m_radioBtn2111132 = wx.RadioButton( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn2111132.SetValue( True )
        Sensor0_value12132.Add( self.m_radioBtn2111132, 0, wx.ALL, 5 )

        self.m_radioBtn3111132 = wx.RadioButton( ProgramInputs132.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value12132.Add( self.m_radioBtn3111132, 0, wx.ALL, 5 )


        ProgramInputs132.Add( Sensor0_value12132, 1, wx.EXPAND, 5 )


        fgSizer4532.Add( ProgramInputs132, 1, wx.EXPAND, 5 )

        ProgramOutputs132 = wx.StaticBoxSizer( wx.StaticBox( Program_4.GetStaticBox(), wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )

        bSizer14232 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle232 = wx.StaticText( ProgramOutputs132.GetStaticBox(), wx.ID_ANY, _(u"Valve"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle232.Wrap( -1 )

        bSizer14232.Add( self.OutputTitle232, 0, wx.ALL, 5 )

        self.m_gauge1132 = wx.Gauge( ProgramOutputs132.GetStaticBox(), wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge1132.SetValue( 0 )
        bSizer14232.Add( self.m_gauge1132, 0, wx.ALL, 5 )


        ProgramOutputs132.Add( bSizer14232, 1, wx.EXPAND, 5 )

        bSizer141132 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle1132 = wx.StaticText( ProgramOutputs132.GetStaticBox(), wx.ID_ANY, _(u"Pump"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle1132.Wrap( -1 )

        bSizer141132.Add( self.OutputTitle1132, 0, wx.ALL, 5 )

        self.m_toggleBtn1132 = wx.ToggleButton( ProgramOutputs132.GetStaticBox(), wx.ID_ANY, _(u"MyButton"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_toggleBtn1132.SetValue( True )
        bSizer141132.Add( self.m_toggleBtn1132, 0, wx.ALL, 5 )


        ProgramOutputs132.Add( bSizer141132, 1, wx.EXPAND, 5 )


        fgSizer4532.Add( ProgramOutputs132, 1, wx.EXPAND, 5 )


        Program_4.Add( fgSizer4532, 1, wx.EXPAND, 5 )


        programsWrapSizer.Add( Program_4, 1, wx.EXPAND, 5 )

        Program_5 = wx.StaticBoxSizer( wx.StaticBox( self.mainScrollableWindow, wx.ID_ANY, _(u"Heating circuit 1") ), wx.VERTICAL )

        fgSizer4531 = wx.FlexGridSizer( 0, 1, 0, 0 )
        fgSizer4531.SetFlexibleDirection( wx.BOTH )
        fgSizer4531.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        ProgramInputs131 = wx.StaticBoxSizer( wx.StaticBox( Program_5.GetStaticBox(), wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )

        Sensor0_value231 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText1231 = wx.StaticText( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1231.Wrap( -1 )

        Sensor0_value231.Add( self.m_staticText1231, 0, wx.ALL, 5 )

        self.m_spinCtrl1231 = wx.SpinCtrl( ProgramInputs131.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value231.Add( self.m_spinCtrl1231, 0, wx.ALL, 5 )

        self.m_slider6231 = wx.Slider( ProgramInputs131.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value231.Add( self.m_slider6231, 0, wx.ALL, 5 )

        self.m_checkBox1231 = wx.CheckBox( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value231.Add( self.m_checkBox1231, 0, wx.ALL, 5 )

        self.m_checkBox2231 = wx.CheckBox( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox2231.SetValue(True)
        Sensor0_value231.Add( self.m_checkBox2231, 0, wx.ALL, 5 )

        self.m_radioBtn2231 = wx.RadioButton( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn2231.SetValue( True )
        Sensor0_value231.Add( self.m_radioBtn2231, 0, wx.ALL, 5 )

        self.m_radioBtn3231 = wx.RadioButton( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value231.Add( self.m_radioBtn3231, 0, wx.ALL, 5 )


        ProgramInputs131.Add( Sensor0_value231, 1, wx.EXPAND, 5 )

        Sensor0_value1331 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText11331 = wx.StaticText( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText11331.Wrap( -1 )

        Sensor0_value1331.Add( self.m_staticText11331, 0, wx.ALL, 5 )

        self.m_spinCtrl11331 = wx.SpinCtrl( ProgramInputs131.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value1331.Add( self.m_spinCtrl11331, 0, wx.ALL, 5 )

        self.m_slider61331 = wx.Slider( ProgramInputs131.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value1331.Add( self.m_slider61331, 0, wx.ALL, 5 )

        self.m_checkBox11331 = wx.CheckBox( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1331.Add( self.m_checkBox11331, 0, wx.ALL, 5 )

        self.m_checkBox21331 = wx.CheckBox( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox21331.SetValue(True)
        Sensor0_value1331.Add( self.m_checkBox21331, 0, wx.ALL, 5 )

        self.m_radioBtn21231 = wx.RadioButton( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn21231.SetValue( True )
        Sensor0_value1331.Add( self.m_radioBtn21231, 0, wx.ALL, 5 )

        self.m_radioBtn31231 = wx.RadioButton( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value1331.Add( self.m_radioBtn31231, 0, wx.ALL, 5 )


        ProgramInputs131.Add( Sensor0_value1331, 1, wx.EXPAND, 5 )

        Sensor0_value11131 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText111131 = wx.StaticText( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText111131.Wrap( -1 )

        Sensor0_value11131.Add( self.m_staticText111131, 0, wx.ALL, 5 )

        self.m_spinCtrl111131 = wx.SpinCtrl( ProgramInputs131.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value11131.Add( self.m_spinCtrl111131, 0, wx.ALL, 5 )

        self.m_slider611131 = wx.Slider( ProgramInputs131.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value11131.Add( self.m_slider611131, 0, wx.ALL, 5 )

        self.m_checkBox111131 = wx.CheckBox( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value11131.Add( self.m_checkBox111131, 0, wx.ALL, 5 )

        self.m_checkBox211131 = wx.CheckBox( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox211131.SetValue(True)
        Sensor0_value11131.Add( self.m_checkBox211131, 0, wx.ALL, 5 )

        self.m_radioBtn211231 = wx.RadioButton( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn211231.SetValue( True )
        Sensor0_value11131.Add( self.m_radioBtn211231, 0, wx.ALL, 5 )

        self.m_radioBtn311231 = wx.RadioButton( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value11131.Add( self.m_radioBtn311231, 0, wx.ALL, 5 )


        ProgramInputs131.Add( Sensor0_value11131, 1, wx.EXPAND, 5 )

        Sensor0_value12131 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText112131 = wx.StaticText( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Direct flow temp"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText112131.Wrap( -1 )

        Sensor0_value12131.Add( self.m_staticText112131, 0, wx.ALL, 5 )

        self.m_spinCtrl112131 = wx.SpinCtrl( ProgramInputs131.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        Sensor0_value12131.Add( self.m_spinCtrl112131, 0, wx.ALL, 5 )

        self.m_slider612131 = wx.Slider( ProgramInputs131.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        Sensor0_value12131.Add( self.m_slider612131, 0, wx.ALL, 5 )

        self.m_checkBox112131 = wx.CheckBox( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value12131.Add( self.m_checkBox112131, 0, wx.ALL, 5 )

        self.m_checkBox212131 = wx.CheckBox( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox212131.SetValue(True)
        Sensor0_value12131.Add( self.m_checkBox212131, 0, wx.ALL, 5 )

        self.m_radioBtn2111131 = wx.RadioButton( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.m_radioBtn2111131.SetValue( True )
        Sensor0_value12131.Add( self.m_radioBtn2111131, 0, wx.ALL, 5 )

        self.m_radioBtn3111131 = wx.RadioButton( ProgramInputs131.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
        Sensor0_value12131.Add( self.m_radioBtn3111131, 0, wx.ALL, 5 )


        ProgramInputs131.Add( Sensor0_value12131, 1, wx.EXPAND, 5 )


        fgSizer4531.Add( ProgramInputs131, 1, wx.EXPAND, 5 )

        ProgramOutputs131 = wx.StaticBoxSizer( wx.StaticBox( Program_5.GetStaticBox(), wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )

        bSizer14231 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle231 = wx.StaticText( ProgramOutputs131.GetStaticBox(), wx.ID_ANY, _(u"Valve"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle231.Wrap( -1 )

        bSizer14231.Add( self.OutputTitle231, 0, wx.ALL, 5 )

        self.m_gauge1131 = wx.Gauge( ProgramOutputs131.GetStaticBox(), wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge1131.SetValue( 0 )
        bSizer14231.Add( self.m_gauge1131, 0, wx.ALL, 5 )


        ProgramOutputs131.Add( bSizer14231, 1, wx.EXPAND, 5 )

        bSizer141131 = wx.BoxSizer( wx.HORIZONTAL )

        self.OutputTitle1131 = wx.StaticText( ProgramOutputs131.GetStaticBox(), wx.ID_ANY, _(u"Pump"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.OutputTitle1131.Wrap( -1 )

        bSizer141131.Add( self.OutputTitle1131, 0, wx.ALL, 5 )

        self.m_toggleBtn1131 = wx.ToggleButton( ProgramOutputs131.GetStaticBox(), wx.ID_ANY, _(u"MyButton"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_toggleBtn1131.SetValue( True )
        bSizer141131.Add( self.m_toggleBtn1131, 0, wx.ALL, 5 )


        ProgramOutputs131.Add( bSizer141131, 1, wx.EXPAND, 5 )


        fgSizer4531.Add( ProgramOutputs131, 1, wx.EXPAND, 5 )


        Program_5.Add( fgSizer4531, 1, wx.EXPAND, 5 )


        programsWrapSizer.Add( Program_5, 1, wx.EXPAND, 5 )


        self.mainScrollableWindow.SetSizer( programsWrapSizer )
        self.mainScrollableWindow.Layout()
        mainBoxSizer.Add( self.mainScrollableWindow, 1, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( mainBoxSizer )
        self.Layout()

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


