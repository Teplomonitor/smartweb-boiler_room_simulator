
import threading

import wx
import wx.xrc

import gettext
_ = gettext.gettext

from gui.inputChannel import Channel as GuiInputChannel

###########################################################################
## Class MainFrame
###########################################################################

class MainFrame ( wx.Frame ):
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
		
		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.doClose )
		
	# Virtual event handlers, override them in your derived class
	def doClose( self, event ):
		event.Skip()
		exit(0)
	
	def __init__( self, parent ):
		self.makeFrame(parent)
		
	def addInput(self, ProgramInputsBox, programInput):
		inputTitle = programInput.getTitle()
		ProgramInputBoxSizer = wx.StaticBoxSizer( wx.StaticBox( ProgramInputsBox.GetStaticBox(), wx.ID_ANY, _(inputTitle) ), wx.HORIZONTAL )
		
		inputValueSpinCtrl = wx.SpinCtrlDouble( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 0, 0.1 )
		ProgramInputBoxSizer.Add( inputValueSpinCtrl, 0, wx.ALL, 5 )
		
		inputValueSlider = wx.Slider( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		ProgramInputBoxSizer.Add( inputValueSlider, 0, wx.ALL, 5 )
		
		inputShortCheckbox = wx.CheckBox( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
		ProgramInputBoxSizer.Add( inputShortCheckbox, 0, wx.ALL, 5 )
		
		inputOpenCheckbox = wx.CheckBox( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
	#	inputOpenCheckbox.SetValue(True)
		ProgramInputBoxSizer.Add( inputOpenCheckbox, 0, wx.ALL, 5 )
		
		inputAutoRadiobutton = wx.RadioButton( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Auto"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
		inputAutoRadiobutton.SetValue( True )
		ProgramInputBoxSizer.Add( inputAutoRadiobutton, 0, wx.ALL, 5 )
		
		inputManualRadioButton = wx.RadioButton( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Manual"), wx.DefaultPosition, wx.DefaultSize, 0 )
		ProgramInputBoxSizer.Add( inputManualRadioButton, 0, wx.ALL, 5 )
		
		ProgramInputsBox.Add( ProgramInputBoxSizer, 1, wx.EXPAND, 5 )
		
		guiChannel = GuiInputChannel(
			inputValueSpinCtrl,
			inputValueSlider, 
			inputShortCheckbox,
			inputOpenCheckbox,
			inputAutoRadiobutton,
			inputManualRadioButton
			)
		
		programInput.setGui(guiChannel)

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
		inputFound = False
		for programInput in programInputs:
			if programInput.isMapped():
				self.addInput(ProgramInputsBox, programInput)
				inputFound = True
		
		if inputFound:
			ProgramIOBoxSizer.Add( ProgramInputsBox, 1, wx.EXPAND, 5 )
		
		ProgramOutputsBox = wx.StaticBoxSizer( wx.StaticBox( ProgramBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )
		
		
		programOutputs = programInfo.getOutputs()
		outputFound = False
		for programOutput in programOutputs:
			if programOutput.isMapped():
				self.addOutput(ProgramOutputsBox, programOutput)
				outputFound = True
			
		if outputFound:
			ProgramIOBoxSizer.Add( ProgramOutputsBox, 1, wx.EXPAND, 5 )
		
		
		ProgramBoxSizer.Add( ProgramIOBoxSizer, 1, 0, 5 )
		
		
		self.programsWrapSizer.Add( ProgramBoxSizer, 1, 0, 5 )
		
		
	def __del__( self ):
		pass


class guiThread():
	def __init__(self, thread_name, thread_ID):
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		
		self._app = wx.App()
		self._frame = wx.Frame(None, title='Simple application')
		self._ex = MainFrame(self._frame)
		
	def addProgram(self, programInfo):
#		self._ex.Show(False)
		self._ex.addProgram(programInfo)
		self._ex.mainScrollableWindow.Layout()
		self._ex.Layout()
#		self._ex.Show(True)

	def run(self):
		self._ex.Show()
		self._app.MainLoop()
			