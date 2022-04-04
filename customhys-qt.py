import sys

import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog, QListWidget
from PyQt6.QtCore import QPropertyAnimation
from PyQt6 import QtCore, QtWidgets
from PyQt6.uic import loadUi

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from customhys import benchmark_func as cbf
from customhys import operators as cso
from customhys import metaheuristic as cmh
from matplotlib import pyplot as plt
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d import Axes3D

# Read all available operators
with open('data/short_collection.txt', 'r') as operators_file:
    heuristic_space = [eval(line.rstrip('\n')) for line in operators_file]
selectors = cso.all_selectors
perturbators = sorted(list(set([x[0] for x in heuristic_space])))

# Format list of perturbators
def pretty_fy(string_list):
    return [" ".join([x.capitalize() for x in string.split("_")]) for string in string_list]

perturbatos_pretty = pretty_fy(perturbators)
selectors_pretty = pretty_fy(selectors)

# print(heuristic_space, selectors, perturbators, sep='\n')


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('test1.ui', self)

        # Read all problems
        self.problem_names = list(cbf.list_functions().keys())
        inf_vals, sup_vals = cbf.for_all('min_search_range'), cbf.for_all('max_search_range')
        self.problem_ranges = {prob: [inf_vals[prob][0], sup_vals[prob][0]] for prob in self.problem_names}


        self.figure = Figure()
        self.figure.set_facecolor("none")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color:transparent;")
        # self.toolbar = NavigationToolbar(self.canvas, self)

        # self.verticalLayout.addWidget(self.toolbar)
        self.verticalLayout.addWidget(self.canvas)

        # Set problem information
        self.qProblemName.addItems(self.problem_names)
        self.update_problem_info(self.qProblemName.currentText())

        # Call the update function
        self.qProblemName.currentTextChanged.connect(self.update_problem_info)
        self.qLowBound.textChanged.connect(self.update_problem_view)
        self.qUppBound.textChanged.connect(self.update_problem_view)

        self.qAdd.clicked.connect(self.add_button)

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
        dlg = self.SearchOperatorsDialog()
        dlg.setWindowTitle("Add Search Operator")
        dlg.exec()

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

    class SearchOperatorsDialog(QDialog):
        def __init__(self):
            super().__init__()

            QBtn = QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel

            self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
            self.buttonBox.accepted.connect(self.accept)
            self.buttonBox.rejected.connect(self.reject)

            # Load list of perturbators
            search_operators = QListWidget()
            search_operators.addItems(perturbatos_pretty)
            search_operators.currentRowChanged.connect(self.update_tuning)

            # Create the table with the parameters to edit for each search operator
            self.table_tuning = QtWidgets.QTableWidget()

            # Prepare GUI
            self.layout = QtWidgets.QVBoxLayout()
            message = QtWidgets.QLabel("List of available search operators:")
            self.layout.addWidget(message)
            self.layout.addWidget(search_operators)
            self.layout.addWidget(self.table_tuning)
            self.layout.addWidget(self.buttonBox)
            self.setLayout(self.layout)

        def update_tuning(self, pert_pretty_index):
            for pert_info in heuristic_space:
                if pert_info[0] == perturbators[pert_pretty_index]:
                    tuning_params, selector = pert_info[1], pert_info[2]

            num_rows = len(tuning_params.items()) + 1

            self.table_tuning.clear()
            self.table_tuning.setColumnCount(2)
            self.table_tuning.setRowCount(num_rows)
            self.table_tuning.setHorizontalHeaderLabels(['Parameter', 'Value'])

            for id, item in enumerate(tuning_params.items()):
                self.table_tuning.setItem(id, 0, QtWidgets.QTableWidgetItem(item[0]))
                self.table_tuning.setItem(id, 1, QtWidgets.QTableWidgetItem(str(item[1])))

            self.table_tuning.setItem(num_rows - 1, 0, QtWidgets.QTableWidgetItem('Selector'))
            self.table_tuning.setItem(num_rows - 1, 1, QtWidgets.QTableWidgetItem(selector))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    q_main_window = MainWindow()
    q_main_window.show()
    sys.exit(app.exec())

