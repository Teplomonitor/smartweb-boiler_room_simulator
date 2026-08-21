
import os

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

from presets.preset import get_presetFilesList   as get_presetFilesList

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
		wx.CallAfter(self.loadPreset)

class ScenarioItem(object):
	def __init__(self, scenario, scenarioDir):
		self._scenario = scenario
		self._dir = scenarioDir
	
	def start_scenario(self):
		scenario = self._scenario
		if self._dir:
			scenario = os.path.join(self._dir, self._scenario)
			
		sc.start_scenario(scenario)

	def onScenarioSelect(self, event):
		event.Skip()
		
		if self._scenario == 'Stop':
			self.stop_scenario()
			return
		
		self.start_scenario()
		
	def stop_scenario(self):
		sc.stop_scenario()

class ScenarioSelectionDialog(wx.Dialog):
	def __init__(self, parent, scenario_paths, selected_scenarios):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, _(u"Select scenarios"), wx.DefaultPosition, wx.Size(520, 600))
		self._scenario_paths = list(scenario_paths)
		self.selected_scenarios = []

		scenario_dir = sc.get_scenario_dir()
		labels = [
			os.path.relpath(path, scenario_dir).replace(os.sep, '/')
			for path in self._scenario_paths
		]
		self._scenario_check_list = wx.CheckListBox(
			self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, labels)
		selected_scenarios = set(selected_scenarios)
		for index, path in enumerate(self._scenario_paths):
			self._scenario_check_list.Check(index, path in selected_scenarios)

		button_sizer = wx.BoxSizer(wx.HORIZONTAL)
		select_all_button = wx.Button(self, wx.ID_ANY, _(u"Select all"))
		clear_all_button = wx.Button(self, wx.ID_ANY, _(u"Clear all"))
		run_button = wx.Button(self, wx.ID_OK, _(u"Run selected"))
		cancel_button = wx.Button(self, wx.ID_CANCEL, _(u"Cancel"))
		button_sizer.Add(select_all_button, 0, wx.ALL, 5)
		button_sizer.Add(clear_all_button, 0, wx.ALL, 5)
		button_sizer.AddStretchSpacer(1)
		button_sizer.Add(run_button, 0, wx.ALL, 5)
		button_sizer.Add(cancel_button, 0, wx.ALL, 5)

		main_sizer = wx.BoxSizer(wx.VERTICAL)
		main_sizer.Add(self._scenario_check_list, 1, wx.EXPAND | wx.ALL, 10)
		main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
		self.SetSizer(main_sizer)
		self.SetSizeHints(wx.Size(400, 300), wx.DefaultSize)

		select_all_button.Bind(wx.EVT_BUTTON, self.on_select_all)
		clear_all_button.Bind(wx.EVT_BUTTON, self.on_clear_all)
		run_button.Bind(wx.EVT_BUTTON, self.on_run)
		self.Centre(wx.BOTH)

	def on_select_all(self, event):
		for index in range(self._scenario_check_list.GetCount()):
			self._scenario_check_list.Check(index, True)

	def on_clear_all(self, event):
		for index in range(self._scenario_check_list.GetCount()):
			self._scenario_check_list.Check(index, False)

	def on_run(self, event):
		self.selected_scenarios = [
			path for index, path in enumerate(self._scenario_paths)
			if self._scenario_check_list.IsChecked(index)
		]
		if not self.selected_scenarios:
			wx.MessageBox(
				_(u"Select at least one scenario."),
				_(u"No scenarios selected"),
				wx.OK | wx.ICON_WARNING,
				parent=self)
			return
		self.EndModal(wx.ID_OK)

class MainFrame ( wx.Frame ):
	
	def addPresetsMenu(self):
		loadPresetSubmenu = wx.Menu()
		
		presetList = get_presetFilesList()
		
		for preset in presetList:
			presetItem = PresetItem(preset)
			presetMenuItem = wx.MenuItem( loadPresetSubmenu, wx.ID_ANY, _(preset), wx.EmptyString, wx.ITEM_NORMAL )
			loadPresetSubmenu.Append( presetMenuItem )
			self.Bind( wx.EVT_MENU, presetItem.onPresetSelect, id = presetMenuItem.GetId() )

		self.m_menu1.AppendSubMenu( loadPresetSubmenu, _(u"Load preset") )
		
	def addScenarioMenu(self):
		def addScenarioItem(submenu, scenarioTitle, scenarioDir = None):
			scenarioItem = ScenarioItem(scenarioTitle, scenarioDir)
			scenarioMenuItem = wx.MenuItem( submenu, wx.ID_ANY, _(scenarioTitle), wx.EmptyString, wx.ITEM_NORMAL )
			submenu.Append( scenarioMenuItem )
			self.Bind( wx.EVT_MENU, scenarioItem.onScenarioSelect, id = scenarioMenuItem.GetId() )
		
		startScenarioSubmenu = wx.Menu()
		addScenarioItem(startScenarioSubmenu, 'all')
		selectScenarioMenuItem = wx.MenuItem(
			startScenarioSubmenu,
			wx.ID_ANY,
			_(u"Select scenarios..."),
			wx.EmptyString,
			wx.ITEM_NORMAL)
		startScenarioSubmenu.Append(selectScenarioMenuItem)
		self.Bind(wx.EVT_MENU, self.onScenarioSelection, id=selectScenarioMenuItem.GetId())
		startScenarioSubmenu.AppendSeparator()
		
		scenarioDir = sc.get_scenario_dir()
		
		def add_scenario_items(subMenu, scenarioDir):
			def filter_scenario_items():
				if '__pycache__' in dirs : dirs .remove('__pycache__')  # don't visit __pycache__ directories
				if '__init__.py' in files: files.remove('__init__.py')  # don't use __init__.py files
				
			for root, dirs, files in os.walk(scenarioDir):
				filter_scenario_items()
				
				for scenarioFile in sorted(files, key=sc.natural_sort_key):
					addScenarioItem(subMenu, scenarioFile, scenarioDir)
					
				for scenarioSubDir in sorted(dirs, key=sc.natural_sort_key):
					scenarioSubmenu = wx.Menu()
					subMenu.AppendSubMenu(scenarioSubmenu, _(scenarioSubDir))
					
					add_scenario_items(scenarioSubmenu, os.path.join(scenarioDir, scenarioSubDir))
				break
				
		add_scenario_items(startScenarioSubmenu, scenarioDir)
		
		startScenarioSubmenu.AppendSeparator()
		addScenarioItem(startScenarioSubmenu, 'Stop')
		
		self.m_menu1.AppendSubMenu( startScenarioSubmenu, _(u"Scenario") )

	def onScenarioSelection(self, event):
		scenario_paths = sc.get_scenario_files_list()
		dialog = ScenarioSelectionDialog(self, scenario_paths, self._selected_scenarios)
		try:
			if dialog.ShowModal() == wx.ID_OK:
				self._selected_scenarios = dialog.selected_scenarios
				sc.start_scenario(list(self._selected_scenarios))
		finally:
			dialog.Destroy()

	def makeFrame(self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 1020,800 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.Size( 500,400 ), wx.DefaultSize )

		mainBoxSizer = wx.BoxSizer( wx.VERTICAL )

		mainBoxSizer.SetMinSize( wx.Size( 640,-1 ) )

		self.scenarioStatusBanner = wx.StaticText(
			self,
			wx.ID_ANY,
			_(u"No scenario running — sensor controls are available"),
			wx.DefaultPosition,
			wx.DefaultSize,
			wx.ALIGN_CENTER)
		self.scenarioStatusBanner.SetMinSize( wx.Size(-1, 32) )
		bannerFont = self.scenarioStatusBanner.GetFont()
		bannerFont.SetWeight(wx.FONTWEIGHT_BOLD)
		self.scenarioStatusBanner.SetFont(bannerFont)
		self.set_scenario_banner_style('idle')
		mainBoxSizer.Add(self.scenarioStatusBanner, 0, wx.EXPAND | wx.ALL, 5)

		self.mainSplitter = wx.SplitterWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_LIVE_UPDATE )
		self.mainSplitter.SetMinimumPaneSize( 150 )
		self.mainSplitter.SetSashGravity( 0.7 )

		self.mainScrollableWindow = wx.ScrolledWindow( self.mainSplitter, wx.ID_ANY, wx.DefaultPosition, wx.Size( 640,480 ), wx.HSCROLL|wx.VSCROLL )
		self.mainScrollableWindow.SetScrollRate( 5, 5 )
		self.mainScrollableWindow.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_INACTIVECAPTION ) )

		self.programsWrapSizer = wx.WrapSizer( wx.VERTICAL, wx.WRAPSIZER_DEFAULT_FLAGS )

		self.programsWrapSizer.SetMinSize( wx.Size( 640,480 ) )

		self.mainScrollableWindow.SetSizer( self.programsWrapSizer )
		self.mainScrollableWindow.Layout()

		self.ConsoleTextCtrl = wx.TextCtrl( self.mainSplitter, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2 )
		self.ConsoleTextCtrl.SetForegroundColour( wx.Colour( 14, 173, 5 ) )
		self.ConsoleTextCtrl.SetBackgroundColour( wx.Colour( 0, 0, 0 ) )

		self.mainSplitter.SplitHorizontally( self.mainScrollableWindow, self.ConsoleTextCtrl, 560 )
		mainBoxSizer.Add( self.mainSplitter, 1, wx.EXPAND |wx.ALL, 5 )


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
		self.scenarioStatusBar = self.CreateStatusBar(2)
		self.scenarioStatusBar.SetStatusWidths([-1, 220])
		self.set_scenario_status_now('idle')

		self.Centre( wx.BOTH )
		
		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.doClose )
		self.Bind( wx.EVT_MENU, self.OnLogSaveButtonPress, id = self.m_menuItem1.GetId() )
		self.Bind( wx.EVT_MENU, self.OnExitButtonPress   , id = self.m_menuItem2.GetId() )

	# Virtual event handlers, override them in your derived class
	def doClose( self, event ):
		event.Skip()
		main.MainStop()
		guiThread().clear()
		exit(0)
	
	def OnLogSaveButtonPress( self, event ):
		event.Skip()
		self._guithread.saveProgramPlots()

	def OnExitButtonPress( self, event ):
		self.doClose(event)

	def printText(self, text, color='GREEN'):
		colors = {
			'GREEN': wx.Colour(14, 173, 5),
			'RED': wx.Colour(173, 40, 40),
		}
		start_position = self.ConsoleTextCtrl.GetLastPosition()
		self.ConsoleTextCtrl.AppendText(text)
		self.ConsoleTextCtrl.SetStyle(
			start_position,
			start_position + len(text),
			wx.TextAttr(colors.get(color, colors['GREEN']))
		)

	def setTextColor(self, color):
		if color == 'GREEN':
			self.ConsoleTextCtrl.SetForegroundColour( wx.Colour( 14, 173, 5 ) )
		elif color == 'RED':
			self.ConsoleTextCtrl.SetForegroundColour( wx.Colour( 173, 40, 40 ) )

	def set_scenario_banner_style(self, state):
		styles = {
			'idle': (wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE), wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT)),
			'preparing': (wx.Colour(254, 216, 114), wx.Colour(0, 0, 0)),
			'running': (wx.Colour(254, 216, 114), wx.Colour(0, 0, 0)),
			'finished': (wx.Colour(120, 248, 158), wx.Colour(0, 0, 0)),
			'stopped': (wx.Colour(251, 117, 126), wx.Colour(0, 0, 0)),
			'failed': (wx.Colour(251, 117, 126), wx.Colour(0, 0, 0)),
		}
		background, foreground = styles.get(state, styles['idle'])
		self.scenarioStatusBanner.SetBackgroundColour(background)
		self.scenarioStatusBanner.SetForegroundColour(foreground)
		self.scenarioStatusBanner.Refresh()

	def set_scenario_status_now(self, state, scenario_title = ''):
		messages = {
			'idle': u"No scenario running — sensor controls are available",
			'preparing': u"SCENARIO PREPARING — please wait",
			'running': u"SCENARIO RUNNING — sensor controls are locked",
			'finished': u"SCENARIO FINISHED — sensor controls are available",
			'stopped': u"SCENARIO STOPPED — sensor controls are available",
			'failed': u"SCENARIO FAILED — sensor controls are available",
		}
		self.scenarioStatusBanner.SetLabel(_(messages.get(state, messages['idle'])))
		self.set_scenario_banner_style(state)
		self.scenarioStatusBar.SetStatusText(_(messages.get(state, messages['idle'])), 0)
		self.scenarioStatusBar.SetStatusText(scenario_title, 1)
		self.Layout()

	def set_scenario_status(self, state, scenario_title = ''):
		wx.CallAfter(self.set_scenario_status_now, state, scenario_title)

	def __init__( self, parent , guithread):
		self._selected_scenarios = []
		self.makeFrame(parent)
		self._guithread = guithread
		self._collector = None
		self._collector_panel = None
		self._collector_temperature_labels = {}
		self._collector_flow_labels = {}
		self._collector_timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.on_collector_timer, self._collector_timer)
		
	def addInput(self, ProgramInputsBox, programInput):
		inputTitle = programInput.get_title()
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
		outputTitle = programOutput.get_title()
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
		parameterTitle   = programParameter.get_title()
		parameterUnits   = programParameter.getUnits()
		parameterOptions = programParameter.getOptions()
		
		ProgramParameterBox = wx.StaticBoxSizer( wx.StaticBox( ProgramParametersBox.GetStaticBox(), wx.ID_ANY, _(f'{parameterTitle} ({parameterUnits})') ), wx.HORIZONTAL )

		parameterSpinCtrl = wx.SpinCtrlDouble( ProgramParameterBox.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER, 0, 100, 0, 0.1 )
		parameterSpinCtrl.SetDigits( 0 )
		ProgramParameterBox.Add( parameterSpinCtrl, 0, wx.ALL, 5 )

		parameterSlider = wx.Slider( ProgramParameterBox.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		ProgramParameterBox.Add( parameterSlider, 0, wx.ALL, 5 )

		if parameterOptions:
			m_comboBox1Choices = parameterOptions
			parameterComboboxCtr = wx.ComboBox( ProgramParameterBox.GetStaticBox(), wx.ID_ANY, m_comboBox1Choices[0], wx.DefaultPosition, wx.DefaultSize, m_comboBox1Choices, 0 )
			parameterComboboxCtr.SetSelection( 0 )
			parameterComboboxCtr.SetMinSize( wx.Size( 80,-1 ) )
			
			ProgramParameterBox.Add( parameterComboboxCtr, 0, wx.ALL, 5 )
		else:
			parameterComboboxCtr = None
		
		ProgramParametersBox.Add( ProgramParameterBox, 1, wx.EXPAND, 5 )
		
		guiChannel = GuiParameterApi(
			parameterSpinCtrl,
			parameterSlider,
			parameterComboboxCtr
			)
		
		parameterSpinCtrl.Bind( wx.EVT_SPINCTRLDOUBLE, programParameter.onSpin    )
		parameterSpinCtrl.Bind( wx.EVT_TEXT_ENTER    , programParameter.onSpinText)
		parameterSlider  .Bind( wx.EVT_SCROLL        , programParameter.onScroll  )
		
		programParameter.setGui(guiChannel)
	
	def addInputs(self, box, boxSizer, programInfo):
		ProgramInputsBox = wx.StaticBoxSizer( wx.StaticBox( box, wx.ID_ANY, _(u"Inputs") ), wx.VERTICAL )
		
		programInputs = programInfo.get_inputs()
		inputFound = False
		for programInput in programInputs.values():
			if programInput.is_mapped():
				self.addInput(ProgramInputsBox, programInput)
				inputFound = True
				
		if inputFound:
			boxSizer.Add( ProgramInputsBox, 1, wx.EXPAND, 5 )
	
	def addOutputs(self, box, boxSizer, programInfo):
		ProgramOutputsBox = wx.StaticBoxSizer( wx.StaticBox( box, wx.ID_ANY, _(u"Outputs") ), wx.VERTICAL )
		
		programOutputs = programInfo.get_outputs()
		outputFound = False
		for programOutput in programOutputs.values():
			if programOutput.is_mapped():
				self.addOutput(ProgramOutputsBox, programOutput)
				outputFound = True
			
		if outputFound:
			boxSizer.Add( ProgramOutputsBox, 1, wx.EXPAND, 5 )
			
	def addParameters(self, box, boxSizer, programInfo):
		ProgramParametersBox = wx.StaticBoxSizer( wx.StaticBox( box, wx.ID_ANY, _(u"Parameters") ), wx.VERTICAL )
		
		programParameters = programInfo.get_parameters()
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
		color = self.programColorToSysColor(programInfo.get_gui_color())
		ProgramPanel.SetBackgroundColour( color )

		ProgramBoxSizer = wx.StaticBoxSizer( wx.StaticBox( ProgramPanel, wx.ID_ANY, _(programInfo.get_title()) ), wx.VERTICAL )
		
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
		self.mainScrollableWindow.FitInside()
		self.Layout()

	def add_collector(self, collector):
		self.remove_collector()

		self._collector = collector
		self._collector_panel = wx.Panel(
			self.mainScrollableWindow,
			wx.ID_ANY,
			wx.DefaultPosition,
			wx.DefaultSize,
			wx.TAB_TRAVERSAL)
		self._collector_panel.SetBackgroundColour(self.programColorToSysColor('orange'))

		collector_box = wx.StaticBoxSizer(
			wx.StaticBox(self._collector_panel, wx.ID_ANY, _(u"Collector")),
			wx.VERTICAL)
		status_box = wx.FlexGridSizer(6, 2, 5, 10)
		status_box.AddGrowableCol(1, 1)

		for name, title in (
			('supply_direct', _(u"Supply from boilers")),
			('supply_backward', _(u"Return to boilers")),
			('direct', _(u"Supply to consumers")),
			('backward', _(u"Return from consumers")),
			):
			status_box.Add(wx.StaticText(
				collector_box.GetStaticBox(), wx.ID_ANY, title),
				0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 3)
			value_label = wx.StaticText(
				collector_box.GetStaticBox(), wx.ID_ANY, u"—")
			value_label.SetMinSize(wx.Size(90, -1))
			status_box.Add(value_label, 0, wx.ALIGN_RIGHT | wx.ALL, 3)
			self._collector_temperature_labels[name] = value_label

		for name, title in (
			('boiler_flow', _(u"Boiler flow")),
			('consumer_flow', _(u"Consumer flow")),
			):
			status_box.Add(wx.StaticText(
				collector_box.GetStaticBox(), wx.ID_ANY, title),
				0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 3)
			value_label = wx.StaticText(
				collector_box.GetStaticBox(), wx.ID_ANY, u"—")
			value_label.SetMinSize(wx.Size(90, -1))
			status_box.Add(value_label, 0, wx.ALIGN_RIGHT | wx.ALL, 3)
			self._collector_flow_labels[name] = value_label
			
		collector_box.Add(status_box, 1, wx.EXPAND | wx.ALL, 5)
		self._collector_panel.SetSizer(collector_box)
		self._collector_panel.Layout()
		collector_box.Fit(self._collector_panel)
		self.programsWrapSizer.Add(self._collector_panel, 1, wx.EXPAND | wx.ALL, 5)
		self.update_collector_temperatures()
		self._collector_timer.Start(500)
		self.mainScrollableWindow.FitInside()
		self.mainScrollableWindow.Layout()
		self.Layout()

	def remove_collector(self):
		if self._collector_timer.IsRunning():
			self._collector_timer.Stop()

		if self._collector_panel:
			self.programsWrapSizer.Detach(self._collector_panel)
			self._collector_panel.Destroy()

		self._collector = None
		self._collector_panel = None
		self._collector_temperature_labels = {}
		self._collector_flow_labels = {}

	def on_collector_timer(self, event):
		self.update_collector_temperatures()

	def update_collector_temperatures(self):
		if not self._collector:
			return

		temperatures = {
			'supply_direct': self._collector.get_supply_direct_temperature(),
			'supply_backward': self._collector.get_supply_backward_temperature(),
			'direct': self._collector.get_direct_temperature(),
			'backward': self._collector.get_backward_temperature(),
		}
		
		flows = {
			'boiler_flow'  : self._collector.get_generator_flow(),
			'consumer_flow': self._collector.get_consumer_flow(),
			}

		for name, temperature in temperatures.items():
			self._collector_temperature_labels[name].SetLabel(f'{temperature:.1f} °C')
		
		for name, flow in flows.items():
			self._collector_flow_labels[name].SetLabel(f'{flow:.1f} t/h')
		
	def __del__( self ):
		pass

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
		self._ex.Show()
		
		self._initDone = True
		
	def clear(self):
		wx.CallAfter(self.ClearNow)
	
	def stopNow(self):
		self.ClearNow()
		exit(0)
		
	def stop(self):
		wx.CallAfter(self.stopNow)
		
	def ClearNow(self):
		self._ex.remove_collector()
		self._ex.programsWrapSizer.Clear(True)
		self._ex.programsWrapSizer.Layout()
		self._ex.set_scenario_status_now('idle')
		self._ex.Layout()
#		wx.GetApp().OnInit()
	
	def addProgram(self, programInfo):
		wx.CallAfter(self.addProgramNow, programInfo)
		
	def addProgramNow(self, programInfo):
		self._ex.addProgram(programInfo)
		self._ex.mainScrollableWindow.Layout()
		self._ex.Layout()

	def add_collector(self, collector):
		wx.CallAfter(self.add_collector_now, collector)

	def add_collector_now(self, collector):
		self._ex.add_collector(collector)

	def saveProgramPlots(self):
		main.saveProgramPlots()
	
	def printConsoleText(self, text, color='GREEN'):
		wx.CallAfter(self.printConsoleTextNow, text, color)
		
	def printConsoleTextNow(self, text, color='GREEN'):
		self._ex.printText(f'{text}\n', color)
		
	def setTextColor(self, color):
		self._ex.setTextColor(color)

	def set_scenario_status(self, state, scenario_title = ''):
		self._ex.set_scenario_status(state, scenario_title)
		
	def run(self):
		self._app.MainLoop()
	


