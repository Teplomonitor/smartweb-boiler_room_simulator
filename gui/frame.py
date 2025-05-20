
import threading

import wx
import wx.xrc

import gettext
_ = gettext.gettext


###########################################################################
## Class MainFrame
###########################################################################

class MainFrame ( wx.Frame ):

	def test(self, parent):
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

		self.inputValueSpinCtrl = wx.SpinCtrl( ProgramInput1BoxSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
		ProgramInput1BoxSizer.Add( self.inputValueSpinCtrl, 0, wx.ALL, 5 )

		self.inputValueSlider = wx.Slider( ProgramInput1BoxSizer.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		ProgramInput1BoxSizer.Add( self.inputValueSlider, 0, wx.ALL, 5 )

		self.inputShortCheckbox = wx.CheckBox( ProgramInput1BoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
		ProgramInput1BoxSizer.Add( self.inputShortCheckbox, 0, wx.ALL, 5 )

		self.inputOpenCheckbox = wx.CheckBox( ProgramInput1BoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.inputOpenCheckbox.SetValue(True)
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
		self.inputOpenCheckbox1.SetValue(True)
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

	def makeFrame(self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 854,763 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.Size( 500,400 ), wx.DefaultSize )

		mainBoxSizer = wx.BoxSizer( wx.VERTICAL )

		mainBoxSizer.SetMinSize( wx.Size( 640,-1 ) )
		self.mainScrollableWindow = wx.ScrolledWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 640,480 ), wx.HSCROLL|wx.VSCROLL )
		self.mainScrollableWindow.SetScrollRate( 5, 5 )
		self.programsWrapSizer = wx.WrapSizer( wx.VERTICAL, wx.WRAPSIZER_DEFAULT_FLAGS )

		self.programsWrapSizer.SetMinSize( wx.Size( 640,480 ) )
		
		self.mainScrollableWindow.SetSizer( self.programsWrapSizer )
		self.mainScrollableWindow.Layout()
		mainBoxSizer.Add( self.mainScrollableWindow, 1, wx.EXPAND |wx.ALL, 5 )


		self.SetSizer( mainBoxSizer )
		self.Layout()

		self.Centre( wx.BOTH )
		
	def __init__( self, parent ):
		self.makeFrame(parent)
#		self.test(parent)
		
	def addInput(self, ProgramInputsBox, programInput):
		inputTitle = programInput.getTitle()
		ProgramInputBoxSizer = wx.StaticBoxSizer( wx.StaticBox( ProgramInputsBox.GetStaticBox(), wx.ID_ANY, _(inputTitle) ), wx.HORIZONTAL )
		
		self.inputValueSpinCtrl = wx.SpinCtrl( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
		ProgramInputBoxSizer.Add( self.inputValueSpinCtrl, 0, wx.ALL, 5 )
		
		self.inputValueSlider = wx.Slider( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		ProgramInputBoxSizer.Add( self.inputValueSlider, 0, wx.ALL, 5 )
		
		self.inputShortCheckbox = wx.CheckBox( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
		ProgramInputBoxSizer.Add( self.inputShortCheckbox, 0, wx.ALL, 5 )
		
		self.inputOpenCheckbox = wx.CheckBox( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
	#	self.inputOpenCheckbox.SetValue(True)
		ProgramInputBoxSizer.Add( self.inputOpenCheckbox, 0, wx.ALL, 5 )
		
		self.inputAutoRadiobutton = wx.RadioButton( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
		self.inputAutoRadiobutton.SetValue( True )
		ProgramInputBoxSizer.Add( self.inputAutoRadiobutton, 0, wx.ALL, 5 )
		
		self.inputManualRadioButton = wx.RadioButton( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
		ProgramInputBoxSizer.Add( self.inputManualRadioButton, 0, wx.ALL, 5 )
		
		ProgramInputsBox.Add( ProgramInputBoxSizer, 1, wx.EXPAND, 5 )

	def addOutput(self, ProgramOutputsBox, programOutput):
		outputTitle = programOutput.getTitle()
		OutputBoxSizer = wx.BoxSizer( wx.HORIZONTAL )
		
		self.OutputTitle = wx.StaticText( ProgramOutputsBox.GetStaticBox(), wx.ID_ANY, _(outputTitle), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.OutputTitle.Wrap( -1 )
		
		OutputBoxSizer.Add( self.OutputTitle, 0, wx.ALL, 5 )
		
		self.outputValueGauge = wx.Gauge( ProgramOutputsBox.GetStaticBox(), wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		self.outputValueGauge.SetValue( 0 )
		OutputBoxSizer.Add( self.outputValueGauge, 0, wx.ALL, 5 )
		
		
		ProgramOutputsBox.Add( OutputBoxSizer, 1, wx.EXPAND, 5 )
	
	def addProgram(self, programInfo):
#		return
		ProgramBoxSizer = wx.StaticBoxSizer( wx.StaticBox( self.mainScrollableWindow, wx.ID_ANY, _(programInfo.getTitle()) ), wx.VERTICAL )
		
		ProgramIOBoxSizer = wx.FlexGridSizer( 0, 1, 10, 0 )
		ProgramIOBoxSizer.SetFlexibleDirection( wx.BOTH )
		ProgramIOBoxSizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		ProgramInputsBox = wx.StaticBoxSizer( wx.StaticBox( ProgramBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )
		
		programInputs = programInfo.getInputs()
		
		for programInput in programInputs:
			self.addInput(ProgramInputsBox, programInput)
			
		ProgramIOBoxSizer.Add( ProgramInputsBox, 1, wx.EXPAND, 5 )
		
		ProgramOutputsBox = wx.StaticBoxSizer( wx.StaticBox( ProgramBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )
		
		
		programOutputs = programInfo.getOutputs()
		
		for programOutput in programOutputs:
			self.addOutput(ProgramOutputsBox, programOutput)
			
			
		ProgramIOBoxSizer.Add( ProgramOutputsBox, 1, wx.EXPAND, 5 )
		
		
		ProgramBoxSizer.Add( ProgramIOBoxSizer, 1, 0, 5 )
		
		
		self.programsWrapSizer.Add( ProgramBoxSizer, 1, 0, 5 )
		
		
	def __del__( self ):
		pass


class guiThread(threading.Thread):
	
	def __init__(self, thread_name, thread_ID):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		
		
	def addProgram(self, programInfo):
#		return
#		self._ex.Show(False)
		self._ex.addProgram(programInfo)
#		self._ex.mainScrollableWindow.SetSizer( self._ex.programsWrapSizer )
		self._ex.mainScrollableWindow.Layout()
		self._ex.Layout()
#		self._ex.Show(True)

	def run(self):
		self._app = wx.App()
		self._frame = wx.Frame(None, title='Simple application')
		self._ex = MainFrame(self._frame)
		self._ex.Show()
		self._app.MainLoop()
			