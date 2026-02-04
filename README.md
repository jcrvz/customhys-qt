# CUSTOMHyS-Qt

This is the official repository for the CUSTOMHyS-Qt software. CUSTOMHyS-Qt is a GUI for the CUSTOMHyS framework, which is an interactive tool for customising heuristic-based algorithms. The CUSTOMHyS-Qt is written in Python and uses the PyQt6 library for the GUI. Further references about the backend can be found in the [CUSTOMHyS repository](https://github.com/jcrvz/CUSTOMHyS). The CUSTOMHyS-Qt is distributed under the terms of the GNU General Public License v3.0.

## Features

- Interactive GUI for configuring and running metaheuristic algorithms
- 3D visualization of benchmark functions
- Real-time plotting of fitness evolution
- Support for multiple search operators and tuning parameters
- Batch run capabilities
- Export results to tables

## Screenshot(s)

![Screenshot](data/Screenshot.png)

## Installation

### Prerequisites

- Python 3.8 or higher
- uv (fast Python package manager)
- make

### Quick Setup with uv and Make

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository and setup:
```bash
git clone https://github.com/jcrvz/customhys-qt.git
cd customhys-qt
make setup
```

This will create a virtual environment and install all dependencies.

3. Activate the virtual environment:
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

4. Run the application:
```bash
make run
```

### Manual Installation

If you prefer manual setup:

1. Clone the repository
```bash
git clone https://github.com/jcrvz/customhys-qt.git
cd customhys-qt
```

2. Create virtual environment:
```bash
uv venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
uv sync
```

4. Run the application:
```bash
python customhys-qt.py
```

### Creating a Standalone Executable

To create a standalone executable using PyInstaller:

```bash
make build
```

The executable will be located in the `dist/` directory.

## Available Make Targets

- `make help` - Show available targets
- `make install-uv` - Install uv
- `make venv` - Create virtual environment
- `make install` - Install dependencies
- `make run` - Run the application
- `make build` - Build executable
- `make clean` - Clean build artifacts
- `make test` - Run tests (placeholder)
- `make lint` - Run linting with ruff
- `make format` - Format code with ruff
- `make setup` - Full setup (venv + install)

## Usage

1. Select a benchmark function from the dropdown.
2. Adjust problem dimensions, population size, and iterations.
3. Add search operators by clicking "Add" and configuring parameters.
4. Click "Run" to execute the algorithm.
5. View results in the table and plots.

## Dependencies

- PyQt6: GUI framework
- matplotlib: Plotting library
- numpy: Numerical computations
- customhys: Backend library for metaheuristics
- scipy, pandas, etc.: Additional scientific libraries

## License

GNU General Public License v3.0
