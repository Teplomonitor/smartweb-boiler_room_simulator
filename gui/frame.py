
import threading

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
		
		self.mainScrollableWindow.SetSizer( programsWrapSizer )
		self.mainScrollableWindow.Layout()
		mainBoxSizer.Add( self.mainScrollableWindow, 1, wx.EXPAND |wx.ALL, 5 )


		self.SetSizer( mainBoxSizer )
		self.Layout()

		self.Centre( wx.BOTH )
		
	def __del__( self ):
		pass


class guiThread(threading.Thread):
	def __init__(self, thread_name, thread_ID):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		
		self._app = wx.App()
		self._frame = wx.Frame(None, title='Simple application')
		self._ex = MainFrame(self._frame)
		self._ex.Show()
		

	def run(self):
		self._app.MainLoop()
			