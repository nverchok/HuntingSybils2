import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.patches import Rectangle
from matplotlib.patches import Circle
from matplotlib.widgets import Slider
from matplotlib.widgets import RadioButtons
from matplotlib.widgets import CheckButtons
from Utils import *
from CurveAnalysis import *
import pprint
pp = pprint.PrettyPrinter(indent=4)

class GUI:
	""" Encompasses the entire graphical interface, as well as managing its
	interactive elements such as buttons, sliders, and stdout output. """
	cfg_figsize = (10.0, 5.0)
	cfg_fade_time = 1.5
	cfg_time_step = 0.05
	col_menu_axes = "lightgoldenrodyellow"
	col_terrain_normal = "#DDDDDD"
	col_terrain_blocked = "#AAAAAA"
	col_terrain_edge = "#888888"
	col_loc_val_radius = "#A6BC95"
	col_node_fill = {
		"hon": "green",
		"mal": "yellow",
		"syb": "red"
	}
	col_node_edge = {
		"non-sybil": "darkgreen",
		"sybil": "darkred",
		"unknown": "darkgrey"
	}
	dim_node_rad = 0.38
	dim_node_rad_h = 0.55
	dim_node_lw = 1.5
	dim_node_lw_h = 2.25
	



	def __init__(self, terrain, id_to_node):
		""" Stores the relevant data, and initialized a set of gfx lookup tables
		to store the references to the drawn graphical objects. """
		self.terrain = terrain
		self.id_to_node = id_to_node
		self.loc_val_data = {}
		self.max_time = Node.max_time

		self.gfx = {}
		self.gfx["val_circle"] = None
		self.gfx["sl_curr_time"] = None
		self.gfx["rb_detectors"] = None
		self.gfx["ax_rb_detectors"] = None
		self.gfx["node_gfx"] = {}
		self.gfx["highlighted_node"] = None
		self.gfx["highlighted_text"] = None
		self.gfx["id_to_arrows_gfx"] = {}
		self.gfx["id_to_arrows_shown"] = {node_id:False for node_id in self.id_to_node.keys()}
		self.gfx["actions_toggle_cdf"] = False
		self.gfx["actions_toggle_pval"] = False
		self.gfx["actions_toggle_arrows"] = False
		self.gfx["options_use_rep_loc"] = False
		self.gfx["options_snap_time"] = False

		self.curr_val_label = None
		self.curr_val_data = None
		self.curr_det_label = None
		self.curr_det_results = None
		self.curr_time = 0
	

	def __printGreeting__(self):
		print("\n  ______________________\n  | SIMULATOR LAUNCHED |\n  "+"\u203E"*22+"\n")
		return
	

	def __getNodeFillColor__(self, node_id):
		""" Returns the fill color of a node (true node type). """
		true_type = self.id_to_node[node_id].type
		return GUI.col_node_fill.get(true_type, "black")
	

	def __getNodeEdgeColor__(self, node_id):
		""" Returns the edge color of a node (predicted node type). """
		if self.curr_det_results != None:
			pred_type = self.curr_det_results["id_to_type"].get(node_id, "unknown")
			return GUI.col_node_edge[pred_type]
		else:
			return self.__getNodeFillColor__(node_id)

	
	def __getArrowColor__(self, edge):
		""" Returns the color of an arrow (i.e. edge; connection success). """
		return "green" if edge.successful else "red"
	

	def __getNodePval__(self, node_id):
		""" Returns the pval of a node if available. """
		if self.curr_det_results != None and "id_to_pval" in self.curr_det_results:
			return str(self.curr_det_results["id_to_pval"][node_id])
		else:
			return "N/A"


	def addLocVal(self, val_label, graph_gen, id_to_edges, results):
		""" Stores the data associated with a location validation procedure. Thus
		multiple location validation procedures may be plotted at once, viewed one
		at a time (but swapped-between dynamically). """
		self.loc_val_data[val_label] = {
			"detectors": list(results.keys()),
			"graph": graph_gen,
			"id_to_edges": id_to_edges,
			"results": results
		}
		self.curr_val_label = val_label
		detectors = self.loc_val_data[val_label]["detectors"]
		initial_det_label = detectors[0]
		self.curr_det_label = initial_det_label
		self.curr_det_results = results[initial_det_label]
		return


	def draw(self):
		""" Executes the drawing. """
		self.__printGreeting__()
		self.fig = plt.figure(figsize=GUI.cfg_figsize)
		self.ax = self.fig.add_axes(
			(0.17, 0.10, 0.80, 0.85),
			aspect="equal", 
			frameon=False,
			xlim=(-0.05, self.terrain.width + 0.05),
			ylim=(-0.05, self.terrain.height + 0.05))
		self.ax.add_patch(Rectangle(
			(0,0),
			self.terrain.width,
			self.terrain.height,
			ec=GUI.col_terrain_edge,
			fc=GUI.col_terrain_normal))

		ax_sl_curr_time = plt.axes([0.22, 0.04, 0.70, 0.03], facecolor=GUI.col_menu_axes, frameon=True)
		axfig_sl_curr_time = self.fig.add_axes(
			ax_sl_curr_time, 
			frameon=False,
			xlim=(-0.05, self.terrain.width + 0.05), 
			ylim=(-0.02,-0.01))
		ax_sl_curr_time.xaxis.set_visible(True)
		ax_sl_curr_time.set_xticks(list(range(Node.max_time)), minor=False)
		sl_curr_time = Slider(ax_sl_curr_time, "Time", 0, self.max_time, valinit=0, closedmin=True, closedmax=True)
		sl_curr_time.valstep = GUI.cfg_time_step
		self.gfx["sl_curr_time"] = sl_curr_time

		ax_rb_val_label = plt.axes([0.01, 0.70, 0.12, 0.22], facecolor=GUI.col_menu_axes, frameon=True)
		rb_val_label = RadioButtons(ax_rb_val_label, tuple(self.loc_val_data.keys()))
		
		ax_rb_detectors = plt.axes([0.01, 0.40, 0.12, 0.25], facecolor=GUI.col_menu_axes, frameon=True)
		rb_detectors = RadioButtons(ax_rb_detectors, tuple())
		self.gfx["rb_detectors"] = rb_detectors
		self.gfx["ax_rb_detectors"] = ax_rb_detectors

		ax_cb_actions = plt.axes([0.01, 0.15, 0.12, 0.20], facecolor=GUI.col_menu_axes, frameon=True)
		cb_actions = CheckButtons(ax_cb_actions, ("cdf", "pval", "arrows"), (False, False, False))

		ax_cb_options = plt.axes([0.01, 0.00, 0.12, 0.15], facecolor=GUI.col_menu_axes, frameon=False)
		cb_options = CheckButtons(ax_cb_options, ("use rep. loc.", "snap time"), (False, False))

		for rstr in self.terrain.restrictions:
			data = rstr[0]
			color = rstr[1]
			self.ax.add_patch(Rectangle( (data[0],data[1]), data[2], data[3], ec=GUI.col_terrain_edge, fc=color))


		def __drawNodes__():
			""" Creates graphical objects for all nodes. """
			for node in self.id_to_node.values():
				node_gfx = Circle(
					node.getPos(0), 
					radius=GUI.dim_node_rad, 
					linewidth=GUI.dim_node_lw,
					ec=self.__getNodeEdgeColor__(node.id), 
					fc=self.__getNodeFillColor__(node.id), 
					zorder=3)
				node_gfx.set_picker(True)
				node_gfx.set_url(node.id)
				self.ax.add_patch(node_gfx)
				self.gfx["node_gfx"][node.id] = node_gfx
			return
		

		def __drawNodeCDF__(node_id):
			id_to_edges = self.curr_val_data["id_to_edges"]
			edges = id_to_edges[node_id]
			xvals, cdf = CurveAnalysis.calcNodeConnCDF(edges)
			CurveAnalysis.plotCDF(self.id_to_node[node_id], xvals, cdf)
			return

		
		def __toggleNodewiseArrows__(node_id):
			""" Creates the set of arrow objects for a given broadcasting node. """
			display_arrows = self.gfx["id_to_arrows_shown"][node_id]
			if node_id not in self.gfx["id_to_arrows_gfx"]:
				edges = self.curr_val_data["id_to_edges"].get(node_id, [])
				temp_arrow_list = []
				for edge in edges:
					pos1 = edge.node_src.getPos(edge.time, reported_pos=self.gfx["options_use_rep_loc"])
					pos2 = edge.node_dst.getPos(edge.time, reported_pos=self.gfx["options_use_rep_loc"])
					x, y, dx, dy = (pos2[0], pos2[1], pos1[0]-pos2[0], pos1[1]-pos2[1])
					col = self.__getArrowColor__(edge)
					arrow_gfx = self.ax.arrow(
						x, y, dx, dy, 
						color=col, 
						visible=False, 
						zorder=2, 
						linewidth=0.2, 
						head_width=0, 
						length_includes_head=True)
					arrow_gfx.set_url(edge.time)
					temp_arrow_list += [arrow_gfx]
				self.gfx["id_to_arrows_gfx"][node_id] = np.array(temp_arrow_list)
			for arrow_gfx in self.gfx["id_to_arrows_gfx"][node_id]:
				__updateArrowAlpha__(arrow_gfx, arrow_visible=display_arrows)
			return
		

		def __updateValCircleAlpha__():
			""" Updates the visual representation of the location validation are
			(i.e. a large circle), showing it only while the procedure is in progress
			and hiding it before and after the procedure. """
			rad_gfx = self.gfx["val_circle"]
			graph = self.curr_val_data["graph"]
			time_start = graph.time_start
			time_end = graph.time_end
			if self.curr_time < time_start:
				rad_gfx.set_alpha(0.1)
			elif self.curr_time < time_end:
				rad_gfx.set_alpha(1)
			elif self.curr_time < time_end + GUI.cfg_fade_time:
				new_alpha = max(1-((self.curr_time - time_end)/GUI.cfg_fade_time)**0.5,0.1)
				rad_gfx.set_alpha(new_alpha)
			else:
				rad_gfx.set_alpha(0.1)
			return
		

		def __updateArrowAlpha__(arrow_gfx, arrow_visible=True):
			""" Updates the visual representation of a single arrow (edge) depending
			on the current time selected and the broadcasting node's click status (i.e.
			whether arrows for this node should be shown at all). """
			arrow_time = float(arrow_gfx.get_url())
			if not arrow_visible:
				arrow_gfx.set_visible(False)
			elif arrow_time > self.curr_time:
				arrow_gfx.set_visible(False)
			elif arrow_time + GUI.cfg_fade_time < self.curr_time:
				arrow_gfx.set_visible(False)
			else:
				new_alpha = 1-((self.curr_time - arrow_time)/GUI.cfg_fade_time)**0.5
				arrow_gfx.set_visible(True)
				arrow_gfx.set_alpha(new_alpha)
			return
		

		def __updateNodes__():
			for node in self.id_to_node.values():
				node_gfx = self.gfx["node_gfx"][node.id]
				node_gfx.center = node.getPos(self.curr_time, reported_pos=self.gfx["options_use_rep_loc"])
			return

		
		def __updateCurrTime__(val):
			""" Updates the current time to the one selected on the time slider. Then
			triggers further updates of the location validation radius and all existing
			arrow objects. """
			self.curr_time = float(val)
			__updateValCircleAlpha__()
			__updateNodes__()
			for arrow_gfx_list in self.gfx["id_to_arrows_gfx"].values():
				for arrow_gfx in arrow_gfx_list:
					__updateArrowAlpha__(arrow_gfx)
			return
		

		def __updateDetector__(det_label):
			""" Updates the current detector chosen from the list of current detectors.
			Recolors relevant node edges according to the predictions made by the new 
			detector. Additionally, prints the precision and recall figures for the new 
			detector to stdout. """
			self.curr_det_label = det_label
			self.curr_det_results = self.curr_val_data["results"][det_label]
			for node in self.id_to_node.values():
				node_gfx = self.gfx["node_gfx"][node.id]
				node_gfx.set_ec(self.__getNodeEdgeColor__(node.id))
			print("Detector: {}\n{}".format(det_label, self.curr_det_results["matrix"]))
			self.fig.canvas.draw()
			return


		def __updateDetectorList__(det_list):
			""" Updates the current detector list according to the current location
			validation procedure, correspondingly updating the RadioButtons UI element. 
			Triggers a UI update indirectly through __updateDetector__()."""
			self.gfx["rb_detectors"].disconnect(0)
			self.gfx["ax_rb_detectors"].cla()
			self.gfx["rb_detectors"] = RadioButtons(self.gfx["ax_rb_detectors"], det_list)
			self.gfx["rb_detectors"].on_clicked(__updateDetector__)
			__updateDetector__(det_list[0])
			return


		def __updateValLabel__(val_label):
			""" Updates the current location validation procedure. Erases all arrow
			objects, updates the old radius object, and updates the detector list.
			Triggers a UI update indirectly through __updateDetectorList__(). """
			self.curr_val_label = val_label
			self.curr_val_data = self.loc_val_data[val_label]
			if self.gfx["val_circle"] != None:
				self.gfx["val_circle"].remove()
			graph = self.loc_val_data[val_label]["graph"]
			new_val_rad = Circle(
				graph.val_pos, 
				radius=graph.val_rad, 
				linewidth=2, 
				ec=GUI.col_loc_val_radius, 
				zorder=4, 
				visible=True, 
				fill=False)
			self.gfx["val_circle"] = new_val_rad
			self.ax.add_patch(new_val_rad)
			__updateValCircleAlpha__()
			for arrow_gfx_list in self.gfx["id_to_arrows_gfx"].values():
				for arrow_gfx in arrow_gfx_list:
					arrow_gfx.remove()
			self.gfx["id_to_arrows_gfx"] = {}
			new_det_list = self.curr_val_data["detectors"]
			__updateDetectorList__(new_det_list)
			return

		
		def __updateActions__(action_label):
			action_str = "actions_toggle_" + action_label
			self.gfx[action_str] = not self.gfx[action_str]
			return
		

		def __toggleOptions__(option_label):
			""" Toggles between using the true location of nodes and node edges, or
			the reported one seen by the server and used by the detection algorithms."""
			if option_label == "use rep. loc.":
				self.gfx["options_use_rep_loc"] = not self.gfx["options_use_rep_loc"]
				__updateNodes__()
				for node_id in self.gfx["id_to_arrows_gfx"].keys():
					for arrow_gfx in self.gfx["id_to_arrows_gfx"][node_id]:
						arrow_gfx.remove()
					self.gfx["id_to_arrows_gfx"].pop(node_id)
					__drawNodewiseArrows__(node_id)
				self.fig.canvas.draw()
			elif option_label == "snap time":
				self.gfx["options_snap_time"] = not self.gfx["options_snap_time"]
				if self.gfx["options_snap_time"]:
					self.gfx["sl_curr_time"].set_val(int(self.gfx["sl_curr_time"].val))
					self.gfx["sl_curr_time"].valstep = 1.00
				else:
					self.gfx["sl_curr_time"].valstep = GUI.cfg_time_step
			return
		
		
		def __onClickNode__(event):
			""" Creates a click-listener for the nodes to allow showing/hiding the
			set of a node's arrows. """
			if self.curr_val_label == None:
				return
			node_id = int(str(event.artist.get_url()))
			if self.gfx["actions_toggle_cdf"]:
				__drawNodeCDF__(node_id)
			if self.gfx["actions_toggle_pval"]:
				print("Node: {}, pval={}".format(node_id, self.__getNodePval__(node_id)))
			if self.gfx["actions_toggle_arrows"]:
				self.gfx["id_to_arrows_shown"][node_id] = not self.gfx["id_to_arrows_shown"][node_id]
				__toggleNodewiseArrows__(node_id)
			self.fig.canvas.draw()
			return
		

		def __onHoverNode__(event):
			if event.inaxes == self.ax:
				new_id = None
				for node_gfx in self.gfx["node_gfx"].values():
					cont, ind = node_gfx.contains(event)
					if cont:
						new_id = int(str((node_gfx.get_url())))
						break
				curr_id = self.gfx["highlighted_node"]
				if curr_id == new_id:
					return
				if curr_id != None:
					curr_gfx = self.gfx["node_gfx"][curr_id]
					curr_gfx.radius = GUI.dim_node_rad
					curr_gfx.linewidth = GUI.dim_node_lw
					self.gfx["highlighted_text"].remove()
				if new_id != None:
					new_gfx = self.gfx["node_gfx"][new_id]
					new_gfx.radius = GUI.dim_node_rad_h
					new_gfx.linewidth = GUI.dim_node_lw_h
					self.gfx["highlighted_text"] = self.ax.text(
						new_gfx._center[0], 
						new_gfx._center[1] + 1, 
						str(new_id), 
						weight="bold",
						horizontalalignment="center")
				self.gfx["highlighted_node"] = new_id
				self.fig.canvas.draw()
			return

		
		__drawNodes__()
		sl_curr_time.on_changed(__updateCurrTime__)
		rb_detectors.on_clicked(__updateDetector__)
		rb_val_label.on_clicked(__updateValLabel__)
		cb_actions.on_clicked(__updateActions__)
		cb_options.on_clicked(__toggleOptions__)
		if self.loc_val_data != {}:
			__updateValLabel__(list(self.loc_val_data.keys())[0])
		self.fig.canvas.mpl_connect("pick_event", __onClickNode__)
		self.fig.canvas.mpl_connect("motion_notify_event", __onHoverNode__)
		plt.show()