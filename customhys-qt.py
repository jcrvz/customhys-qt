import os
from timeit import default_timer as timer

import numpy as np
from PyQt6.QtCore import Qt, QItemSelectionModel
from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem, QAction, QKeySequence
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog, QListWidget, QListWidgetItem, QTableView
from PyQt6.uic import loadUi
from customhys import benchmark_func as cbf
from customhys import metaheuristic as cmh
from customhys import operators as cso
from customhys.tools import read_json
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.colors import LightSource
from matplotlib.figure import Figure
import copy

# Just for build the app
basedir = os.path.dirname(__file__)

try:
    from ctypes import windll  # Only exists on Windows.

    myappid = 'jcrvz.customhys.app.1'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


# Read all available operators
with open(os.path.join(basedir, 'data', "short_collection.txt"), 'r') as operators_file:
    heuristic_space = [eval(line.rstrip('\n')) for line in operators_file]
selectors = cso.__selectors__
perturbators = sorted(list(set([x[0] for x in heuristic_space])))

categorical_options = read_json(os.path.join(basedir, 'data', "tuning_parameters.json"))


# Format list of perturbators
def pettrify(string_list):
    return [" ".join([x.capitalize() for x in string.split("_")]) for string in string_list]


perturbators_pretty = pettrify(perturbators)
selectors_pretty = pettrify(selectors)

perturbators_icons = read_json(os.path.join(basedir, 'data', "icon_list.json"))
#print(perturbators_icons)

class SearchOperatorsDialog(QDialog):
    def __init__(self, parent=None, edit_mode=False):
        super().__init__(parent)
        self.edit_mode = edit_mode

        # Create the table with the parameters to edit for each search operator
        self.table_tuning = QtWidgets.QTableWidget()

        QBtn = QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Load list of perturbators
        self.search_operators = QListWidget()
        self.search_operators.addItems(perturbators_pretty)
        if self.edit_mode:
            so2edit = self.parent().qMetaheuristic.currentItem().text().split("->")
            so2edit_name = so2edit[0].strip()
            so2edit_tuning = eval(so2edit[1].strip())
            so2edit_item = self.search_operators.findItems(so2edit_name, QtCore.Qt.MatchFlag.MatchExactly)[0]
            self.search_operators.setCurrentItem(so2edit_item)
            self.update_tuning(self.search_operators.currentRow(), custom_tuning=so2edit_tuning)
        else:
            self.search_operators.setCurrentRow(0)
            self.update_tuning(0)

        self.search_operators.currentRowChanged.connect(self.update_tuning)

        # Prepare GUI
        self.layout = QtWidgets.QVBoxLayout()
        message = QtWidgets.QLabel("List of available search operators:")
        self.layout.addWidget(message)
        self.layout.addWidget(self.search_operators)
        self.layout.addWidget(self.table_tuning)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    @staticmethod
    def reformat_search_operator():
        pass

    def read_table_tuning(self):
        row_count = self.table_tuning.rowCount()
        tuning_list = []
        if row_count > 1:
            for row in range(row_count - 1):
                widget_key = self.table_tuning.item(row, 0).text()
                if self.table_tuning.item(row, 1):
                    widget_value = self.table_tuning.item(row, 1).text()
                elif self.table_tuning.cellWidget(row, 1):
                    widget_value = self.table_tuning.cellWidget(row, 1).currentText()
                else:
                    widget_value = 'NULL'
                try:
                    float(widget_value)
                except:
                    widget_value = f"'{widget_value}'"
                tuning_list.append("'{}': {}".format(widget_key, widget_value))
            tuning_parameters = '{' + ','.join(tuning_list) + '},'
        else:
            tuning_parameters = '{},'

        only_selector = self.table_tuning.cellWidget(row_count - 1, 1).currentText()
        return tuning_parameters + "'{}'".format(only_selector)

    def accept(self) -> None:
        search_operator_pretty_name = self.search_operators.currentItem().text()
        search_operator_name = perturbators[self.search_operators.currentRow()]
        search_operator_tuning = self.read_table_tuning()
        search_operator = f"{search_operator_pretty_name}->" + "('{}', {})".format(
            search_operator_name, search_operator_tuning)
        # print(self.read_table_tuning)
        op_icon = QIcon(os.path.join(basedir, 'data', 'icons', perturbators_icons[search_operator_pretty_name]))
        if self.edit_mode:
            self.parent().qMetaheuristic.currentItem().setText(search_operator)
            self.parent().qMetaheuristic.currentItem().setIcon(op_icon)
        else:  # Add new item
            item_to_add = QListWidgetItem(op_icon, search_operator)
            #item_to_add.setSizeHint(QtCore.QSize(30, 30))
            self.parent().qMetaheuristic.addItem(item_to_add)
            self.parent().qMetaheuristic.setCurrentItem(item_to_add)
        QDialog.accept(self)

    def update_tuning(self, pert_pretty_index, custom_tuning=None):
        chosen_perturbator = perturbators[pert_pretty_index]
        for pert_info in heuristic_space:
            if pert_info[0] == perturbators[pert_pretty_index]:
                tuning_params, selector = pert_info[1], pert_info[2]

        # Bypass default tuning_params if edit_mode is on
        if self.edit_mode and custom_tuning:
            for key, value in custom_tuning[1].items():
                tuning_params[key] = value
            selector = custom_tuning[2]

        # Combo box for selectors
        qcombo_selector = QtWidgets.QComboBox()
        qcombo_selector.addItems(selectors)

        num_rows = len(tuning_params.items()) + 1

        self.table_tuning.clear()
        self.table_tuning.setColumnCount(2)
        self.table_tuning.setRowCount(num_rows)
        self.table_tuning.setHorizontalHeaderLabels(['Parameter', 'Value'])

        for id, item in enumerate(tuning_params.items()):
            # Combo box for special cases
            is_special = True
            if chosen_perturbator in ["firefly_dynamic", "genetic_mutation", "local_random_walk", "random_search",
                                      "swarm_dynamic"] and item[0] == 'distribution':
                item_to_add = QtWidgets.QComboBox()
                item_to_add.addItems(categorical_options['distribution'])
            elif chosen_perturbator == "differential_mutation" and item[0] == 'expression':
                item_to_add = QtWidgets.QComboBox()
                item_to_add.addItems(categorical_options['expression'])
            elif chosen_perturbator == "differential_crossover" and item[0] == 'version':
                item_to_add = QtWidgets.QComboBox()
                item_to_add.addItems(categorical_options['version_dc'])
            elif chosen_perturbator == "genetic_crossover" and item[0] == 'pairing':
                item_to_add = QtWidgets.QComboBox()
                item_to_add.addItems(categorical_options['pairing'])
            elif chosen_perturbator == "genetic_crossover" and item[0] == 'crossover':
                item_to_add = QtWidgets.QComboBox()
                item_to_add.addItems(categorical_options['crossover'])
            elif chosen_perturbator == "swarm_dynamic" and item[0] == 'version':
                item_to_add = QtWidgets.QComboBox()
                item_to_add.addItems(categorical_options['version_ps'])
            else:
                item_to_add = QtWidgets.QTableWidgetItem(str(item[1]))
                is_special = False

            # Fill items for the two columns
            self.table_tuning.setItem(id, 0, QtWidgets.QTableWidgetItem(item[0]))
            if is_special:
                item_to_add.setCurrentText(item[1])
                self.table_tuning.setCellWidget(id, 1, item_to_add)
            else:
                self.table_tuning.setItem(id, 1, item_to_add)

        qcombo_selector.setCurrentText(selector)
        self.table_tuning.setItem(num_rows - 1, 0, QtWidgets.QTableWidgetItem('selector'))
        self.table_tuning.setCellWidget(num_rows - 1, 1, qcombo_selector)
        # self.table_tuning.setItem(num_rows - 1, 1, QtWidgets.QTableWidgetItem(selector))


class CopyableTableView(QTableView):
    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copy_selection()
        else:
            super().keyPressEvent(event)

    def copy_selection(self):
        selection = self.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]

            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                table[row][column] = index.data()

            stream = []
            for row in table:
                stream.append('\t'.join(row))
            clipboard_text = '\n'.join(stream)

            clipboard = QApplication.clipboard()
            clipboard.setText(clipboard_text)

class PlotWindow(QMainWindow):
    def __init__(self, figure, parent=None):
        super().__init__(parent)
        self.figure = copy.deepcopy(figure)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.addToolBar(self.toolbar)
        self.setCentralWidget(self.canvas)


class MyCanvas(FigureCanvas):
    def __init__(self, parent=None, is_3d=False, figsize=(3, 2)):
        self.figure = Figure(figsize, tight_layout=True)
        self.figure.set_facecolor("none")
        if is_3d:
            self.ax = self.figure.subplots(1, 1, subplot_kw=dict(projection='3d', proj_type='ortho'))
            self.ax.set_facecolor("none")
        else:
            self.ax = self.figure.subplots(1, 2, sharey='row', gridspec_kw={'width_ratios': [0.8, 0.2]})
            self.ax[0].set_facecolor("none")
            self.ax[1].set_facecolor("none")
        super().__init__(self.figure)
        self.setStyleSheet("background-color:transparent;")

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.new_window = PlotWindow(self.figure)
            self.new_window.show()


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.worst_fitness = None
        self.worst_position = None
        self.worst_centroid = None
        self.worst_time = None
        self.best_time = None
        self.best_fitness = None
        self.best_position = None
        self.best_centroid = None
        self.historical_time = []
        self.historical_fitness_values = []
        loadUi(os.path.join(basedir, 'data', "customhys-qt.ui"), self)
        self.setWindowTitle("CUSTOMHyS-Qt")
        #self.setOrganizationName("jcrvz")
        # lock change size of the window
        #self.setFixedSize(self.size())

        # Read all problems
        self.problem_names = list(cbf.__all__)
        if "CEC2005" in self.problem_names:
            self.problem_names.remove("CEC2005")

        inf_vals = dict()
        sup_vals = dict()
        # Read all functions and request their optimum data
        for ii, function_name in enumerate(self.problem_names):
            dummy_function = eval('cbf.{}({})'.format(function_name, 2))
            inf_vals[function_name] = dummy_function.min_search_range
            sup_vals[function_name] = dummy_function.max_search_range

        self.problem_ranges = {prob: [inf_vals[prob][0], sup_vals[prob][0]] for prob in self.problem_names}

        # For visualising the problem in 2D
        #self.figure = Figure()
        #self.figure.set_facecolor("none")
        #self.canvas = FigureCanvas(self.figure)
        self.canvas = MyCanvas(is_3d=True)
        self.figure = self.canvas.figure
        self.canvas.setStyleSheet("background-color:transparent;")
        self.verticalLayout.addWidget(self.canvas)

        # For visualising the fitness evolution
        #self.figure_hist = Figure()
        #self.figure_hist.set_facecolor("none")
        #self.canvas_hist = FigureCanvas(self.figure_hist)
        self.canvas_hist = MyCanvas(figsize=(7, 2.2))
        self.figure_hist = self.canvas_hist.figure
        self.axs_hist = self.canvas_hist.ax
        self.axs_hist[0].set_xlabel('Iteration')
        self.axs_hist[1].set_xlabel('Iteration')
        self.axs_hist[0].set_ylabel('Fitness')
        # self.axs_hist[1].set_ylabel('Fitness')
        self.canvas_hist.setStyleSheet("background-color:transparent;")
        self.runLayout.addWidget(self.canvas_hist)


        # self.verticalLayout.addWidget(self.toolbar)

        # Set problem information
        self.qProblemName.addItems(self.problem_names)
        self.update_problem_info(self.qProblemName.currentText())

        # Call the update function
        self.qProblemName.currentTextChanged.connect(self.update_problem_info)
        self.qLowBound.textChanged.connect(self.update_problem_view)
        self.qUppBound.textChanged.connect(self.update_problem_view)

        self.qAdd.clicked.connect(self.add_button)
        self.qRem.clicked.connect(self.rem_button)
        self.qEdit.clicked.connect(self.edit_button)
        self.qRunButton.clicked.connect(self.run_button)

        self.qMetaheuristic.setIconSize(QtCore.QSize(30, 30))
        #self.qMetaheuristic.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.qMetaheuristic.doubleClicked.connect(self.edit_button)
        self.qMetaheuristic.itemEntered.connect(self.on_item_entered)

        self.canvas_hist.setVisible(False)
        self.qInfo_Table.setVisible(False)

        self.show()



    @staticmethod
    def on_item_entered(item):
        # Set the tooltip to the item's text
        item.setToolTip(item.text())

    def update_problem_info(self, problem_name):
        # Set lower and upper boundaries
        self.qLowBound.setText(f"{self.problem_ranges[problem_name][0]}")
        self.qUppBound.setText(f"{self.problem_ranges[problem_name][1]}")
        # self.qBoundaries.setText("{}, {}".format(*self.problem_ranges[problem_name]))

        self.update_problem_view()

    def update_problem_view(self):
        # Load the problem to plot
        problem_object = eval(f"cbf.{self.qProblemName.currentText()}(2)")

        # Read the lower and upper boundaries
        low_boundary = float(self.qLowBound.text())
        upp_boundary = float(self.qUppBound.text())

        self.plot(problem_object, low_boundary, upp_boundary)

    def add_button(self):
        dlg = SearchOperatorsDialog(self)
        dlg.setWindowTitle("Add Search Operator")
        dlg.exec()
        self.enable_run_button()

    def rem_button(self):
        self.qMetaheuristic.takeItem(self.qMetaheuristic.currentRow())
        self.enable_run_button()

    def enable_run_button(self):
        self.qRunButton.setEnabled(self.qMetaheuristic.count() > 0)

    #def enable_edit_button(self):
    #    self.qEditButton.setEnabled(self.qMetaheuristic.currentRow is not None)

    def edit_button(self):
        if self.qMetaheuristic.currentItem():
            dlg = SearchOperatorsDialog(self, edit_mode=True)
            dlg.setWindowTitle("Edit Search Operator")
            dlg.exec()

    def run_button(self):
        # Get information for run the metaheuristic
        # try:
        #     float(self.qDimensionality.text())
        # except:
        #     QtWidgets.QErrorMessage(self).showMessage("Invalid dimensionality!")
        # try:
        #     float(self.qPopulation.text())
        # except:
        #     QtWidgets.QErrorMessage(self).showMessage("Invalid population!")
        # try:
        #     float(self.qIterations.text())
        # except:
        #     QtWidgets.QErrorMessage(self).showMessage("Invalid iterations!")
        dim = int(self.qDimensionality.text())
        pop = int(self.qPopulation.text())
        ite = int(self.qIterations.text())

        # Prepare the problem
        fun = eval(f"cbf.{self.qProblemName.currentText()}({dim})")
        fun.set_search_range(float(self.qLowBound.text()), float(self.qUppBound.text()))

        # Build the metaheuristic
        heuristics = [
            eval(self.qMetaheuristic.item(x).text().split("->")[1].strip()) for x in range(self.qMetaheuristic.count())]
        mh = cmh.Metaheuristic(fun.get_formatted_problem(), heuristics, num_agents=pop, num_iterations=ite)

        # Run simulation
        start_time = timer()
        mh.run()
        end_time = timer()
        elapsed_time = end_time - start_time

        # Plot history
        fitness_values = mh.historical['fitness']
        if self.qClearHist.isChecked():
            self.historical_fitness_values = []
            self.best_fitness = None
            self.best_position = None
            self.best_centroid = None
            self.best_time = None
            self.worst_fitness = None
            self.worst_position = None
            self.worst_centroid = None
            self.worst_time = None
            self.historical_time = []

            self.qClearHist.setChecked(False)
            self.axs_hist[0].clear()

        # Save history
        self.historical_fitness_values.append(fitness_values[-1])
        self.historical_time.append(elapsed_time)

        # Save best history
        if self.best_fitness is None or fitness_values[-1] < self.best_fitness:
            self.best_fitness = fitness_values[-1]
            self.best_position = mh.historical['position'][-1]
            self.best_centroid = mh.historical['centroid'][-1]
            self.best_time = elapsed_time

        # Save worst history
        if self.worst_fitness is None or fitness_values[-1] > self.worst_fitness:
            self.worst_fitness = fitness_values[-1]
            self.worst_position = mh.historical['position'][-1]
            self.worst_centroid = mh.historical['centroid'][-1]
            self.worst_time = elapsed_time

        self.axs_hist[0].plot(range(len(fitness_values)), fitness_values)
        self.axs_hist[0].set_xlabel('Iteration')
        self.axs_hist[0].set_ylabel('Fitness')

        self.axs_hist[1].clear()
        self.axs_hist[1].violinplot(self.historical_fitness_values, showmeans=True, showmedians=True)
        #self.axs_hist[1].boxplot(self.historical_fitness_values, showfliers=False)
        self.axs_hist[1].set_xlabel('Final Iteration')

        self.canvas_hist.setVisible(True)
        self.canvas_hist.draw()

        # Show results
        solution = mh.get_solution()
        # self.qInfo_Fitness.setText("{:.2f}".format(solution[1]))
        # self.qInfo_Position.setText(", ".join(["{:#7.2g}"]*len(solution[0])).format(*solution[0]))
        # self.qInfo_Centroid.setText(", ".join(["{:#7.2g}"]*len(solution[0])).format(*mh.historical['centroid'][-1]))
        # self.qInfo_Time.setText("{:.2f}".format(elapsed_time))
        # print("x_best = {}, f_best = {}".format(*mh.get_solution())

        # Update table
        model = QStandardItemModel()
        model.setRowCount(4)
        model.setColumnCount(6)
        model.setVerticalHeaderLabels(["Fitness", "Position", "Centroid", "Time (s)"])
        model.setHorizontalHeaderLabels(["Last", "Best", "Worst", "Mean", "Std. Dev.", "Median"])

        # Show the last iteration
        model.setItem(0, 0, QStandardItem("{:.2f}".format(solution[1])))
        model.setItem(1, 0, QStandardItem(
            ", ".join(["{:#7.2g}"] * len(solution[0])).format(*solution[0])))
        model.setItem(2, 0, QStandardItem(
            ", ".join(["{:#7.2g}"] * len(solution[0])).format(*mh.historical['centroid'][-1])))
        model.setItem(3, 0, QStandardItem("{:.2f}".format(elapsed_time)))

        # Show the best iteration
        model.setItem(0, 1, QStandardItem("{:.2f}".format(self.best_fitness)))
        model.setItem(1, 1, QStandardItem(
            ", ".join(["{:#7.2g}"] * len(self.best_position)).format(*self.best_position)))
        model.setItem(2, 1, QStandardItem(
            ", ".join(["{:#7.2g}"] * len(self.best_centroid)).format(*self.best_centroid)))
        model.setItem(3, 1, QStandardItem("{:.2f}".format(self.best_time)))

        # Show the worst iteration
        model.setItem(0, 2, QStandardItem("{:.2f}".format(self.worst_fitness)))
        model.setItem(1, 2, QStandardItem(
            ", ".join(["{:#7.2g}"] * len(self.worst_position)).format(*self.worst_position)))
        model.setItem(2, 2, QStandardItem(
            ", ".join(["{:#7.2g}"] * len(self.worst_centroid)).format(*self.worst_centroid)))
        model.setItem(3, 2, QStandardItem("{:.2f}".format(self.worst_time)))

        # Show the mean iteration
        model.setItem(0, 3, QStandardItem("{:.2f}".format(np.mean(self.historical_fitness_values))))
        model.setItem(1, 3, QStandardItem("--"))
        model.setItem(2, 3, QStandardItem("--"))
        model.setItem(3, 3, QStandardItem("{:.2f}".format(np.mean(self.historical_time))))

        # Show the std. dev. iteration
        model.setItem(0, 4, QStandardItem("{:.2f}".format(np.std(self.historical_fitness_values))))
        model.setItem(1, 4, QStandardItem("--"))
        model.setItem(2, 4, QStandardItem("--"))
        model.setItem(3, 4, QStandardItem("{:.2f}".format(np.std(self.historical_time))))

        # Show the median iteration
        model.setItem(0, 5, QStandardItem("{:.2f}".format(np.median(self.historical_fitness_values))))
        model.setItem(1, 5, QStandardItem("--"))
        model.setItem(2, 5, QStandardItem("--"))
        model.setItem(3, 5, QStandardItem("{:.2f}".format(np.median(self.historical_time))))

        self.qInfo_Table.setModel(model)
        self.qInfo_Table.setVisible(True)

        row_height = 24
        header = self.qInfo_Table.horizontalHeader()
        self.qInfo_Table.verticalHeader().setDefaultSectionSize(row_height)
        self.qInfo_Table.setFixedHeight(4 * row_height + 2 * header.height())
        #print(4 * row_height + 2 * header.height())

    # class Problem_Preview(FigureCanvas):
    def plot(self, problem_object, low_boundary, upp_boundary):
        samples = 50
        x = np.linspace(low_boundary, upp_boundary, samples)
        y = np.linspace(low_boundary, upp_boundary, samples)

        # Create the grid matrices
        matrix_x, matrix_y = np.meshgrid(x, y)

        # Evaluate each node of the grid into the problem function
        matrix_z = []
        for xy_list in zip(matrix_x, matrix_y):
            z = []
            for xy_input in zip(xy_list[0], xy_list[1]):
                tmp = list(xy_input)
                tmp.extend(list(problem_object.optimal_solution[2:problem_object.variable_num]))
                z.append(problem_object.get_function_value(np.array(tmp)))
            matrix_z.append(z)
        matrix_z = np.array(matrix_z)

        # Initialise the figure
        # self.fig = plt.figure(figsize=[4, 3], facecolor='w')
        # self.ax = self.fig.gca(projection='3d', proj_type='ortho')
        self.figure.clear()
        self.ax = self.figure.subplots(1, 1, subplot_kw=dict(projection='3d', proj_type='ortho'))
        self.ax.set_facecolor("none")

        # super().__init__(self.fig)

        ls = LightSource(azdeg=90, altdeg=45)
        rgb = ls.shade(matrix_z, plt.cm.jet)

        # Plot data
        self.ax.plot_surface(matrix_x, matrix_y, matrix_z, rstride=1, cstride=1, linewidth=0.5,
                             antialiased=False, facecolors=rgb)  #

        # Adjust the labels
        self.ax.set_xlabel('$x_1$')
        self.ax.set_ylabel('$x_2$')
        self.ax.set_zlabel('$f(x, y)$')
        # self.ax.set_title(problem_object.func_name)

        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False

        # self.figure.patch.set_facecolor("None")
        # self.ax.patch.set_alpha(1)

        # plt.close()
        self.canvas.draw()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    #app.setStyle("Fusion")
    app.setWindowIcon(QtGui.QIcon(os.path.join(basedir, 'data', "chm_logo.png")))
    q_main_window = MainWindow()
    app.exec()
    # app.exec()
