#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os
import file_explorer

""" A sort of TreeView container that serves for showing file listings """
class TreeViewFile:
	def __init__(self, pixbufDir, pixbufFile):
		
		self.pixbufDirectory = pixbufDir
		self.pixbufFile = pixbufFile
		# GOTCHA: Number of columns in the store *MUST* match the number of values
		# added in loadData
		self.tree_store = gtk.TreeStore(gobject.TYPE_BOOLEAN, str, int)
		self.tree_view = gtk.TreeView(self.tree_store)
		self.tree_view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
		self.scrolled_window = gtk.ScrolledWindow()
		self.scrolled_window.add_with_viewport(self.tree_view)
		
		# TYPE
		type_col = gtk.TreeViewColumn('')
		self.tree_view.append_column(type_col)
		
		type_col_renderer_pixbuf = gtk.CellRendererPixbuf()
		type_col.pack_start(type_col_renderer_pixbuf, expand=True)
		# GOTCHA Func must be set AFTER the renderer is packed into the column
		type_col.set_cell_data_func(type_col_renderer_pixbuf, self.renderDirOrFile)

		# NAME
		name_col = gtk.TreeViewColumn('File name')
		self.tree_view.append_column(name_col)
		
		name_col_renderer_text = gtk.CellRendererText()
		name_col.pack_start(name_col_renderer_text, expand=True)
		name_col.add_attribute(name_col_renderer_text, 'text', 1)
		name_col.set_sort_column_id(1)
		self.tree_view.set_search_column(1)
		
		# SIZE
		size_col = gtk.TreeViewColumn('Size')
		self.tree_view.append_column(size_col)
		
		size_col_renderer = gtk.CellRendererText()
		size_col.pack_start(size_col_renderer, expand=True)
		size_col.add_attribute(size_col_renderer, 'text', 2)
		size_col.set_sort_column_id(2)


	def renderDirOrFile(self, tree_view_column, cell, model, iter):
		isDir = model.get_value(iter, 0)
		if isDir:
			pixbuf = self.pixbufDirectory
		else:
			pixbuf = self.pixbufFile

		cell.set_property('pixbuf', pixbuf)


	def getView(self):
		return self.scrolled_window

	def getTree(self):
		return self.tree_view


	def loadData(self, data):
		self.tree_store.clear()

		for row in data:
			rowIter = self.tree_store.append(None, [ row['directory'], row['name'], row['size'] ])



class GFileExplorer:
	def __init__(self):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_border_width(10)
		self.window.set_size_request(640, 480)

		self.window.connect('destroy', self.destroy)

		self.v_box = gtk.VBox(False, 0)
		self.window.add(self.v_box)

		imageDir = gtk.Image()
		imageDir.set_from_file('./icons/folder.png')
		imageFile = gtk.Image()
		imageFile.set_from_file('./icons/file.png')

		# Host and device panels, and copy buttons
		# They're inside an HBox (which is inside the topmost VBox)
		self.h_box = gtk.HBox(False, 0)
		self.v_box.pack_start(self.h_box, True, True, 0)
		
		# host
		hostVBox = gtk.VBox(False, 0)
		
		hostLabel = gtk.Label('Host')
		hostVBox.pack_start(hostLabel, expand=False, fill=False)
		
		self.host_tree_view_file = TreeViewFile(imageDir.get_pixbuf(), imageFile.get_pixbuf())
		hostVBox.pack_start(self.host_tree_view_file.getView())
		
		self.h_box.pack_start(hostVBox)

		# Copy buttons
		buttonsVBox = gtk.VBox(False, 0)
		self.h_box.pack_start(buttonsVBox, expand=False, fill=False)

		self.btnCopyToDevice = gtk.Button("->")
		self.btnCopyFromDevice = gtk.Button("<-")

		buttonsVBox.pack_start(self.btnCopyToDevice, expand=False, fill=False)
		buttonsVBox.pack_start(self.btnCopyFromDevice, expand=False, fill=False)

		self.btnCopyToDevice.connect('clicked', self.copy_to_device_callback, None)
		self.btnCopyFromDevice.connect('clicked', self.copy_from_device_callback, None)

		# device
		deviceVBox = gtk.VBox(False, 0)

		deviceLabel = gtk.Label('Device')
		deviceVBox.pack_start(deviceLabel, expand=False, fill=False)

		self.device_tree_view_file = TreeViewFile(imageDir.get_pixbuf(), imageFile.get_pixbuf())
		deviceVBox.pack_start(self.device_tree_view_file.getView())

		self.h_box.pack_start(deviceVBox)

		# Status
		self.status_frame = gtk.Frame("Status")
		
		self.status_text = gtk.TextView()
		self.status_text.set_editable(False)
		self.status_frame.add(self.status_text)
		
		self.v_box.pack_start(self.status_frame, True, True, 0)

		self.window.show_all()

		self.output("Ready")

		self.adb = 'adb'

		self.host_cwd = os.getcwd()
		self.device_cwd = '/mnt/sdcard/'

		self.refreshHostFiles()
		self.refreshDeviceFiles()


	def refreshHostFiles(self):
		self.host_tree_view_file.loadData(self.dirScanHost(self.host_cwd))

	def refreshDeviceFiles(self):
		self.device_tree_view_file.loadData(self.dirScanDevice(self.device_cwd))

	""" Walks through a directory and return the data in a tree-style list 
		that can be used by the TreeViewFile """
	def dirScanHost(self, directory):
		output = []

		root, dirs, files = next(os.walk(directory))

		dirs.sort()
		files.sort()

		output.append({'directory': True, 'name': '..', 'size': 0})

		for d in dirs:
			output.append({'directory': True, 'name': d, 'size': 0})

		for f in files:
			size = os.path.getsize(os.path.join(directory, f))
			output.append({'directory': False, 'name': f, 'size': size})

		return output

	""" Like dirScanHost, but in the connected Android device """
	def dirScanDevice(self, directory):
		output = []
		
		entries = file_explorer.parse_device_list(file_explorer.device_list(self.adb, directory))

		dirs = []
		files = []

		for filename, entry in entries.iteritems():
			if entry['is_directory']:
				dirs.append(filename)
			else:
				files.append(filename)

		dirs.sort()
		files.sort()

		output.append({'directory': True, 'name': '..', 'size': 0})

		for d in dirs:
			output.append({'directory': True, 'name': d, 'size': 0})

		for f in files:
			size = entries[f]['size']
			output.append({'directory': False, 'name': f, 'size': size})

		return output

	def copy_to_device_callback(self, widget, data=None):
		print 'copy to device'
	
	def copy_from_device_callback(self, widget, data=None):
		model, rows = self.device_tree_view_file.getTree().get_selection().get_selected_rows()

		for row in rows:
			iter = model.get_iter(row)
			filename = model.get_value(iter, 1)
			full_device_path = os.path.join(self.device_cwd, filename)
			full_host_path = os.path.join(self.host_cwd, filename)

			file_explorer.action_copy_from_device(self.adb, full_device_path, full_host_path)
			self.refreshHostFiles()
		


	def output(self, text):
		buffer = self.status_text.get_buffer()
		buffer.set_text(text)
		self.status_text.set_buffer(buffer)

	def die_callback(self, widget, data=None):
		self.destroy(widget, data)

	def destroy(self, widget, data=None):
		gtk.main_quit()

	def main(self):
		gtk.main()


if __name__ == '__main__':
	explorer = GFileExplorer()
	explorer.main()
