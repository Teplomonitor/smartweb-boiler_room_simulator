

try:
	import wx
	import gettext
	_ = gettext.gettext
	
except ImportError:
	print('import gui fail. Please install wxPython if you wish to use gui: pip install -U wxPython')

import main

from gui.parameter import GuiParameterApi  as GuiParameterApi
from gui.parameter import GuiInputChannel  as GuiInputChannel
from gui.parameter import GuiOutputChannel as GuiOutputChannel

from presets.preset import getPresetFilesList   as getPresetFilesList

import scenario.scenario as sc

guiThreadSingleton = None

###########################################################################
## Class MainFrame
###########################################################################

class PresetItem(object):
	def __init__(self, preset):
		self._preset = preset
	
	def loadPreset(self):
		main.loadPreset(self._preset)
		
	def onPresetSelect(self, event):
		event.Skip()
		self.loadPreset()

class ScenarioItem(object):
	def __init__(self, scenario):
		self._scenario = scenario
	
	def startScenario(self):
		sc.startScenario(self._scenario)

	def onScenarioSelect(self, event):
		event.Skip()
		self.startScenario()

class MainFrame ( wx.Frame ):
	
	def addPresetsMenu(self):
		loadPresetSubmenu = wx.Menu()
		
		presetList = getPresetFilesList()
		
		for preset in presetList:
			presetItem = PresetItem(preset)
			presetMenuItem = wx.MenuItem( loadPresetSubmenu, wx.ID_ANY, _(preset), wx.EmptyString, wx.ITEM_NORMAL )
			loadPresetSubmenu.Append( presetMenuItem )
			self.Bind( wx.EVT_MENU, presetItem.onPresetSelect, id = presetMenuItem.GetId() )

		self.m_menu1.AppendSubMenu( loadPresetSubmenu, _(u"Load preset") )
		
	def addScenarioMenu(self):
		startScenarioSubmenu = wx.Menu()
		
		scenarioList = sc.getScenarioFilesList()
		scenarioList.insert(0, 'all')

		appendSeparator = True
		for scenario in scenarioList:
			scenarioItem     = ScenarioItem(scenario)
			scenarioMenuItem = wx.MenuItem( startScenarioSubmenu, wx.ID_ANY, _(scenario), wx.EmptyString, wx.ITEM_NORMAL )
			startScenarioSubmenu.Append( scenarioMenuItem )
			self.Bind( wx.EVT_MENU, scenarioItem.onScenarioSelect, id = scenarioMenuItem.GetId() )
			
			if appendSeparator:
				appendSeparator = False
				startScenarioSubmenu.AppendSeparator()

		self.m_menu1.AppendSubMenu( startScenarioSubmenu, _(u"Scenario") )

	def makeFrame(self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 1020,800 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.Size( 500,400 ), wx.DefaultSize )

		mainBoxSizer = wx.BoxSizer( wx.VERTICAL )

		mainBoxSizer.SetMinSize( wx.Size( 640,-1 ) )
		self.mainScrollableWindow = wx.ScrolledWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 640,480 ), wx.HSCROLL|wx.VSCROLL )
		self.mainScrollableWindow.SetScrollRate( 5, 5 )
		self.mainScrollableWindow.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_INACTIVECAPTION ) )

		self.programsWrapSizer = wx.WrapSizer( wx.VERTICAL, wx.WRAPSIZER_DEFAULT_FLAGS )

		self.programsWrapSizer.SetMinSize( wx.Size( 640,480 ) )

		self.mainScrollableWindow.SetSizer( self.programsWrapSizer )
		self.mainScrollableWindow.Layout()
		mainBoxSizer.Add( self.mainScrollableWindow, 1, wx.EXPAND |wx.ALL, 5 )


		self.SetSizer( mainBoxSizer )
		self.Layout()
		self.m_menubar1 = wx.MenuBar( 0 )
		self.m_menu1 = wx.Menu()
		
		self.addPresetsMenu()
		
		self.addScenarioMenu()
		
		self.m_menuItem1 = wx.MenuItem( self.m_menu1, wx.ID_ANY, _(u"Save log")+ u"\t" + u"Ctrl+S", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.Append( self.m_menuItem1 )

		self.m_menuItem2 = wx.MenuItem( self.m_menu1, wx.ID_ANY, _(u"Exit")+ u"\t" + u"Ctrl+Q", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.Append( self.m_menuItem2 )

		self.m_menubar1.Append( self.m_menu1, _(u"File") )

		self.SetMenuBar( self.m_menubar1 )

		self.Centre( wx.BOTH )
		
		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.doClose )
		self.Bind( wx.EVT_MENU, self.OnLogSaveButtonPress, id = self.m_menuItem1.GetId() )
		self.Bind( wx.EVT_MENU, self.OnExitButtonPress   , id = self.m_menuItem2.GetId() )

	# Virtual event handlers, override them in your derived class
	def doClose( self, event ):
		event.Skip()
		main.MainStop()
		guiThread().Clear()
		exit(0)
	
	def OnLogSaveButtonPress( self, event ):
		event.Skip()
		self._guithread.saveProgramPlots()

	def OnExitButtonPress( self, event ):
		self.doClose(event)

	def __init__( self, parent , guithread):
		self.makeFrame(parent)
		self._guithread = guithread
		
	def addInput(self, ProgramInputsBox, programInput):
		inputTitle = programInput.getTitle()
		inputUnits = programInput.getUnits()
		
		ProgramInputBoxSizer = wx.StaticBoxSizer( wx.StaticBox( ProgramInputsBox.GetStaticBox(), wx.ID_ANY, _(f'{inputTitle} ({inputUnits})') ), wx.HORIZONTAL )
		
		inputValueSpinCtrl = wx.SpinCtrlDouble( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER, 0, 100, 0, 0.1 )
		ProgramInputBoxSizer.Add( inputValueSpinCtrl, 0, wx.ALL, 5 )
		
		inputValueSlider = wx.Slider( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		ProgramInputBoxSizer.Add( inputValueSlider, 0, wx.ALL, 5 )
		
		inputShortCheckbox = wx.CheckBox( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Short"), wx.DefaultPosition, wx.DefaultSize, 0 )
		ProgramInputBoxSizer.Add( inputShortCheckbox, 0, wx.ALL, 5 )
		
		inputOpenCheckbox = wx.CheckBox( ProgramInputBoxSizer.GetStaticBox(), wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
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
		
		inputValueSpinCtrl.Bind( wx.EVT_SPINCTRLDOUBLE, programInput.onSpin    )
		inputValueSpinCtrl.Bind( wx.EVT_TEXT_ENTER    , programInput.onSpinText)
		inputValueSlider  .Bind( wx.EVT_SCROLL        , programInput.onScroll  )
		inputShortCheckbox.Bind( wx.EVT_CHECKBOX      , programInput.onShort   )
		inputOpenCheckbox .Bind( wx.EVT_CHECKBOX      , programInput.onOpen    )
		inputAutoRadiobutton  .Bind(wx.EVT_RADIOBUTTON, programInput.onAuto  )
		inputManualRadioButton.Bind(wx.EVT_RADIOBUTTON, programInput.onManual)
		
		programInput.setGui(guiChannel)

	def addOutput(self, ProgramOutputsBox, programOutput):
		outputTitle = programOutput.getTitle()
		OutputBoxSizer = wx.BoxSizer( wx.HORIZONTAL )
		
		self.OutputTitle = wx.StaticText( ProgramOutputsBox.GetStaticBox(), wx.ID_ANY, _(outputTitle), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.OutputTitle.Wrap( -1 )
		self.OutputTitle.SetMinSize( wx.Size( 120,-1 ) )
		
		OutputBoxSizer.Add( self.OutputTitle, 0, wx.ALL, 5 )
		
		outputValueGauge = wx.Gauge( ProgramOutputsBox.GetStaticBox(), wx.ID_ANY, 254, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		outputValueGauge.SetValue( 0 )
		OutputBoxSizer.Add( outputValueGauge, 0, wx.ALL, 5 )
		
		ProgramOutputsBox.Add( OutputBoxSizer, 1, wx.EXPAND, 5 )
		
		guiChannel = GuiOutputChannel(
			outputValueGauge
			)
		
		programOutput.setGui(guiChannel)
	
	def addParameter(self, ProgramParametersBox, programParameter):
		parameterTitle = programParameter.getTitle()
		parameterUnits = programParameter.getUnits()
		ProgramParameterBox = wx.StaticBoxSizer( wx.StaticBox( ProgramParametersBox.GetStaticBox(), wx.ID_ANY, _(f'{parameterTitle} ({parameterUnits})') ), wx.HORIZONTAL )

		parameterSpinCtrl = wx.SpinCtrlDouble( ProgramParameterBox.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER, 0, 100, 0, 0.1 )
		parameterSpinCtrl.SetDigits( 0 )
		ProgramParameterBox.Add( parameterSpinCtrl, 0, wx.ALL, 5 )

		parameterSlider = wx.Slider( ProgramParameterBox.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		ProgramParameterBox.Add( parameterSlider, 0, wx.ALL, 5 )

		ProgramParametersBox.Add( ProgramParameterBox, 1, wx.EXPAND, 5 )
		
		guiChannel = GuiParameterApi(
			parameterSpinCtrl,
			parameterSlider
			)
		
		parameterSpinCtrl.Bind( wx.EVT_SPINCTRLDOUBLE, programParameter.onSpin    )
		parameterSpinCtrl.Bind( wx.EVT_TEXT_ENTER    , programParameter.onSpinText)
		parameterSlider  .Bind( wx.EVT_SCROLL        , programParameter.onScroll  )
		
		programParameter.setGui(guiChannel)
	
	def addInputs(self, box, boxSizer, programInfo):
		ProgramInputsBox = wx.StaticBoxSizer( wx.StaticBox( box, wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )
		
		programInputs = programInfo.getInputs()
		inputFound = False
		for programInput in programInputs:
			if programInput.isMapped():
				self.addInput(ProgramInputsBox, programInput)
				inputFound = True
				
		if inputFound:
			boxSizer.Add( ProgramInputsBox, 1, wx.EXPAND, 5 )
	
	def addOutputs(self, box, boxSizer, programInfo):
		ProgramOutputsBox = wx.StaticBoxSizer( wx.StaticBox( box, wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )
		
		programOutputs = programInfo.getOutputs()
		outputFound = False
		for programOutput in programOutputs:
			if programOutput.isMapped():
				self.addOutput(ProgramOutputsBox, programOutput)
				outputFound = True
			
		if outputFound:
			boxSizer.Add( ProgramOutputsBox, 1, wx.EXPAND, 5 )
			
	def addParameters(self, box, boxSizer, programInfo):
		ProgramParametersBox = wx.StaticBoxSizer( wx.StaticBox( box, wx.ID_ANY, _(u"Parameters") ), wx.VERTICAL )
		
		programParameters = programInfo.getParameters()
		parameterFound = False
		for programParameter in programParameters:
			self.addParameter(ProgramParametersBox, programParameters[programParameter])
			parameterFound = True
			
		if parameterFound:
			boxSizer.Add( ProgramParametersBox, 1, wx.EXPAND, 5 )
			
	def programColorToSysColor(self, color):
		sysColor = {
			'default': wx.SystemSettings.GetColour( wx.SYS_COLOUR_MENU ),
			'red'    : wx.Colour( 251, 117, 126 ),
			'blue'   : wx.Colour( 121, 168, 247 ),
			'yellow' : wx.Colour( 243, 235, 124 ),
			'orange' : wx.Colour( 254, 216, 114 ),
			'green'  : wx.Colour( 120, 248, 158 ),
		}
		if color in sysColor:
			return sysColor[color]
		
		return sysColor['default']
	
	def addProgram(self, programInfo):
		wx.CallAfter(self.addProgramNow, programInfo)
	
	def addProgramNow(self, programInfo):
		ProgramPanel = wx.Panel( self.mainScrollableWindow, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		color = self.programColorToSysColor(programInfo.getGuiColor())
		ProgramPanel.SetBackgroundColour( color )

		ProgramBoxSizer = wx.StaticBoxSizer( wx.StaticBox( ProgramPanel, wx.ID_ANY, _(programInfo.getTitle()) ), wx.VERTICAL )
		
		ProgramIOBoxSizer = wx.FlexGridSizer( 0, 1, 10, 0 )
		ProgramIOBoxSizer.SetFlexibleDirection( wx.BOTH )
		ProgramIOBoxSizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.addInputs    (ProgramBoxSizer.GetStaticBox(), ProgramIOBoxSizer, programInfo)
		self.addOutputs   (ProgramBoxSizer.GetStaticBox(), ProgramIOBoxSizer, programInfo)
		self.addParameters(ProgramBoxSizer.GetStaticBox(), ProgramIOBoxSizer, programInfo)

		ProgramBoxSizer.Add( ProgramIOBoxSizer, 1, 0, 5 )
		
		ProgramPanel.SetSizer( ProgramBoxSizer )
		ProgramPanel.Layout()
		ProgramBoxSizer.Fit( ProgramPanel )
		self.programsWrapSizer.Add( ProgramPanel, 1, wx.EXPAND |wx.ALL, 5 )
		self.Layout()
		
	def __del__( self ):
		pass

class ConsoleFrame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 640,480 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		ConsoleSizer = wx.BoxSizer( wx.VERTICAL )

		self.ConsoleTextCtrl = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_READONLY )
		self.ConsoleTextCtrl.SetForegroundColour( wx.Colour( 14, 173, 5 ) )
		self.ConsoleTextCtrl.SetBackgroundColour( wx.Colour( 0, 0, 0 ) )
		
		ConsoleSizer.Add( self.ConsoleTextCtrl, 1, wx.ALL|wx.EXPAND, 5 )


		self.SetSizer( ConsoleSizer )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.doClose )
		
	def __del__( self ):
		pass
	
	# Virtual event handlers, override them in your derived class
	def doClose( self, event ):
		event.Skip()
		guiThread().ClearNow()
		exit(0)
	
	def printText(self, text):
		self.ConsoleTextCtrl.AppendText(text)

	def OnExitButtonPress( self, event ):
		self.doClose(event)

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
		self._ex = MainFrame(self._frame, self)
		self._consoleFrame = ConsoleFrame(self._frame)
		self._ex.Show()
		self._consoleFrame.Show()
		
		self._initDone = True
		
	def Clear(self):
		wx.CallAfter(self.ClearNow)
	
	def ClearNow(self):
		self._ex.programsWrapSizer.Clear(True)
		self._ex.programsWrapSizer.Layout()
		self._ex.Layout()
#		wx.GetApp().OnInit()
	
	def addProgram(self, programInfo):
		wx.CallAfter(self.addProgramNow, programInfo)
		
	def addProgramNow(self, programInfo):
		self._ex.addProgram(programInfo)
		self._ex.mainScrollableWindow.Layout()
		self._ex.Layout()

	def saveProgramPlots(self):
		main.saveProgramPlots()
	
	def printConsoleText(self, text):
		wx.CallAfter(self.printConsoleTextNow, text)
		
	def printConsoleTextNow(self, text):
		self._consoleFrame.printText(text)
		self._consoleFrame.printText('\n')
		
	def run(self):
		self._app.MainLoop()
	


