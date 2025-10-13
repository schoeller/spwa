# Sheet Pile Wall Analysis Tool (SPWA)

This application is a desktop tool for the geotechnical analysis and design of sheet pile retaining walls. It allows civil and geotechnical engineers to model and analyze both cantilever and multi-anchored sheet pile walls based on the free-earth support method.

![Application Screenshot](https://i.imgur.com/your-screenshot.png) *(Note: Add a real screenshot link here)*

## Features

- **Analysis Methods**: Performs analysis for both cantilever and multi-anchored walls.
- **Static & Seismic Conditions**: Implements Coulomb's theory for static conditions and the Mononobe-Okabe method for seismic conditions.
- **Complex Profiles**: Supports multi-layered soil profiles with varying properties.
- **Water Levels**: Considers different water levels on both the active and passive sides.
- **Structural Checks**: Performs stress and deflection checks based on selected section properties and design codes.
- **Graphical Output**: Generates diagrams for net pressure, earth pressure, shear force, bending moment, rotation, and deflection.
- **User-Friendly Interface**: A modern, themeable (dark/light) GUI built with PyQt6.
- **Multi-language Support**: Available in English and Turkish.
- **Project Files**: Save and load your analysis inputs to a `.spwa` file.

## Installation

To run this application, you need Python 3.8+ and the required packages.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/spwa.git
    cd spwa
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    The project's dependencies are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Once the dependencies are installed, you can run the application from the root directory:

```bash
python main.py
```

## Running Tests

The project includes a suite of unit tests to ensure the accuracy of the analysis engine. To run the tests, execute the following command from the root directory:

```bash
python -m unittest discover tests
```

## Contributing

Contributions are welcome! If you would like to contribute, please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature-name`).
3. Make your changes and commit them (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature-name`).
5. Open a pull request.

Please make sure to update tests as appropriate.