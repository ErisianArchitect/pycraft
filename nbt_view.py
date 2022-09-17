from PySide6 import QtCore, QtGui
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import os, sys
import pathlib
from functools import partial

from world import region
from world import nbt

def pause():
	input('[Press Enter To Continue...]')

region_dir = 'C:\\Users\\admin\\Documents\\Software\\MultiMC\\instances\\1.16.5\\.minecraft\\saves\\Pythonian\\region'
region_file = os.path.join(region_dir, 'r.0.0.mca')
region_file_backup = os.path.join(region_dir, 'r.0.0.backup.mca')

assert os.path.isfile(region_file), "Region file not found. Can not proceed."
assert os.path.isfile(region_file_backup), "Region file backup not found. Will not proceed."

reg = region.RegionFile(region_file)
tag, tag_name = reg.read_chunk_tag(0, 0)
raw_chunk = reg.read_chunk_raw(0, 0)

assert tag is not None, "Chunk was not found."

# This is some code to grab data for the chunk at (0, 0).
# This is in case I need to isolate the binary data of the NBT of a chunk for testing.
# if not os.path.isfile('raw_chunk.nbt'):
# 	with open('raw_chunk.nbt', 'wb') as f:
# 		f.write(raw_chunk)
# 	print('File created for raw chunk.')
# 	input('[Press Enter To Exit]')
# 	sys.exit()

print('Tag Type:', type(tag))

app = QApplication(sys.argv)

class nbt_tree:
	__slots__ = {'root', 'widget', 'children'}

	def __init__(self, root_tag : nbt.nbt_tag) -> None:
		self.root = root_tag

class MainWindow(QWidget):
	def __init__(self):
		super(MainWindow, self).__init__()

		self.menu = QMenuBar(self)

		self.act = QAction('Test Action')

		self.menu.addAction(self.act)

		fg = QRect(0,0, 600, 600)
		center = QtGui.QScreen.availableGeometry(QApplication.primaryScreen()).center()
		fg.moveCenter(center)
		self.setGeometry(fg)

		vbox = QVBoxLayout(self)

		tree = QTreeWidget()
		tree.setGeometry(0,0, fg.width(), fg.height())
		self.tree = tree

		vbox.addWidget(self.menu)

		vbox.addWidget(tree)

		btn = QPushButton('Hello')

		vbox.addWidget(btn)

		self.setLayout(vbox)

		# self.tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

		# self.tree.setGeometry(0,0, 500, 400)
		self.header = QTreeWidgetItem(['NBT Viewer'])
		self.tree.setHeaderItem(self.header)
		self.root = QTreeWidgetItem(self.tree, ['Test'])
		# self.tree.itemClicked.connect(partial(print, 'itemClicked'))
		for x in range(4):
			x_tree = QTreeWidgetItem(self.tree, [f'({x}, 0, 0)'])
			x_tree.setData(0, Qt.EditRole, 'Test')
			for y in range(4):
				y_tree = QTreeWidgetItem(x_tree, [f'({x}, {y}, 0)'])
				for z in range(4):
					z_tree = QTreeWidgetItem(y_tree, [f'({x}, {y}, {z})'])
		

main = MainWindow()
main.show()
sys.exit(app.exec())

tree = QTreeWidget()

header = QTreeWidgetItem(['Virtual folder tree'])

tree.setHeaderItem(header)

root = QTreeWidgetItem(tree, ['Untagged files'])
root.setData(2, QtCore.Qt.EditRole, foo(420, 69))

folder2 = QTreeWidgetItem(root, ['Exteriors'])
folder2.setData(2, QtCore.Qt.EditRole, 'Some hidden data')

print(root.data(2, QtCore.Qt.EditRole))

tree.show()
sys.exit(app.exec())
