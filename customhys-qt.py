import sys, os

from timeit import default_timer as timer

import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog, QListWidget
from PyQt6.QtCore import QPropertyAnimation
from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.uic import loadUi

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from customhys import benchmark_func as cbf
from customhys import operators as cso
from customhys import metaheuristic as cmh
from customhys.tools import read_json
from matplotlib import pyplot as plt
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d import Axes3D

# Just for build the app
basedir = os.path.dirname(__file__)

try:
    from ctypes import windll  # Only exists on Windows.

    myappid = 'mycompany.myproduct.subproduct.version'
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

# with open("data/tuning_parameters.txt", 'r') as default_tuning_file:
#     categorical_options = [eval(line.rstrip('\n')) for line in default_tuning_file]
categorical_options = read_json(os.path.join(basedir, 'data', "tuning_parameters.json"))


# Format list of perturbators
def pettrify(string_list):
    return [" ".join([x.capitalize() for x in string.split("_")]) for string in string_list]


perturbatos_pretty = pettrify(perturbators)
selectors_pretty = pettrify(selectors)


# print(heuristic_space, selectors, perturbators, sep='\n')
# %%
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
        self.search_operators.addItems(perturbatos_pretty)
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
                tuning_list.append("'{}':{}".format(widget_key, widget_value))
            tuning_parameters = '{' + ', '.join(tuning_list) + '}, '
        else:
            tuning_parameters = '{}, '

        only_selector = self.table_tuning.cellWidget(row_count - 1, 1).currentText()
        return tuning_parameters + "'{}'".format(only_selector)

    def accept(self) -> None:
        search_operator_pretty_name = self.search_operators.currentItem().text()
        search_operator_name = perturbators[self.search_operators.currentRow()]
        search_operator_tuning = self.read_table_tuning()
        search_operator = f"{search_operator_pretty_name} -> " + "('{}', {})".format(
            search_operator_name, search_operator_tuning)
        # print(self.read_table_tuning)
        if self.edit_mode:
            self.parent().qMetaheuristic.currentItem().setText(search_operator)
        else:
            self.parent().qMetaheuristic.addItem(search_operator)
        QDialog.accept(self)

    def update_tuning(self, pert_pretty_index, custom_tuning=None):
        chosen_perturbator = perturbators[pert_pretty_index]
        for pert_info in heuristic_space:
            if pert_info[0] == perturbators[pert_pretty_index]:
                tuning_params, selector = pert_info[1], pert_info[2]

        # Bypass default tuning_params if edit_mode is on
        if self.edit_mode:
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


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.path.join(basedir, 'data', "customhys-qt.ui"), self)
        self.setWindowTitle("cUIstomhys")

        # Read all problems
        self.problem_names = list(cbf.__all__)
        inf_vals, sup_vals = cbf.for_all('min_search_range'), cbf.for_all('max_search_range')
        self.problem_ranges = {prob: [inf_vals[prob][0], sup_vals[prob][0]] for prob in self.problem_names}

        # For visualising the problem in 2D
        self.figure = Figure()
        self.figure.set_facecolor("none")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color:transparent;")
        self.verticalLayout.addWidget(self.canvas)

        # For visualising the fitness evolution
        self.figure_hist = Figure()
        self.figure_hist.set_facecolor("none")
        self.canvas_hist = FigureCanvas(self.figure_hist)
        self.canvas_hist.setStyleSheet("background-color:transparent;")
        self.runLayout.addWidget(self.canvas_hist)
        # self.toolbar = NavigationToolbar(self.canvas, self)

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

        self.show()

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

        # print(dir(self.qProblemPreview))

        # new_qProblemPreview = Problem_Preview(problem_object, low_boundary, upp_boundary)
        # self.verticalLayout.replaceWidget(self.qProblemPreview, new_qProblemPreview, 3)

        # self.verticalLayout.removeWidget(self.qProblemPreview)
        # self.qProblemPreview.close()
        # self.qProblemPreview = Problem_Preview(problem_object, low_boundary, upp_boundary)
        # self.verticalLayout.addWidget(self.qProblemPreview, 2)
        # self.verticalLayout.update()

        # self.verticalLayout.removeWidget(self.qProblemPreview)
        # self.qProblemPreview = self.verticalLayout.addWidget(Problem_Preview(problem_object, low_boundary, upp_boundary))
        # self.verticalLayout.update()
        # self.qProblemPreview = Problem_Preview(problem_object, low_boundary, upp_boundary)

    def add_button(self):
        dlg = SearchOperatorsDialog(self)
        dlg.setWindowTitle("Add Search Operator")
        dlg.exec()
        self.enable_run_button()

    def rem_button(self):
        # try:
        self.qMetaheuristic.takeItem(self.qMetaheuristic.currentRow())
        self.enable_run_button()
        # except:
        #     print("Nothing to remove!")

    def enable_run_button(self):
        self.qRunButton.setEnabled(self.qMetaheuristic.count() > 0)

    def edit_button(self):
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

        # Show results
        solution = mh.get_solution()
        self.qInfo_Fitness.setText("{:.6g}".format(solution[1]))
        self.qInfo_Position.setText(str(solution[0]))
        self.qInfo_Centroid.setText(str(mh.historical['centroid'][-1]))
        self.qInfo_Time.setText("{:.4f}".format(elapsed_time))
        # print("x_best = {}, f_best = {}".format(*mh.get_solution())

        # Plot history
        fitness_values = mh.historical['fitness']
        self.figure_hist.clear()
        self.ax_hist = self.figure_hist.subplots(1, 1)
        self.ax_hist.set_facecolor("none")
        self.ax_hist.plot(range(len(fitness_values)), fitness_values)
        self.ax_hist.set_xlabel('Iteration')
        self.ax_hist.set_ylabel('Fitness')

        self.canvas_hist.draw()

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
    app.setWindowIcon(QtGui.QIcon(os.path.join(basedir, 'data', "chm_logo.png")))
    q_main_window = MainWindow()
    app.exec()
    # app.exec()
