# TEAM 01 - Final Project - Compiler

This repository contains the compiler for the Compilers course, developed by Team 1

**Members**
- Espinoza Matamoros Percival Ulises
- Flores Colín Victor Jaziel
- García Cortés Adolfo de Jesus
- Lara Hernandez Angel Husiel
- Lugo Manzano Rodrigo
  
## Running the Program

### Web Version

A web version of the Compiler has been deployed using Streamlit. You can access it through the following link:

[Compiler Web App](https://fi-compilers-team1-p3-km77fcpu9ugztdjxzspbhki.streamlit.app/)

### Local Version

To run the compiler, you can execute the `app.py` or `main.py` file. Make sure you have the required dependencies installed, which are listed in the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

>[!NOTE]
> To run the application locally, you must have `WSL` installed along with the `gcc` and `nasm` packages. If you are running it from Linux, make sure you have the `gcc` and `nasm` packages installed.

#### UI Version

You can run the UI version of the program by executing the `app.py` file. This will launch a Streamlit interface where you can input your code and see the results.

```bash
python -m streamlit run unam.fi.compilers.g5.01/ui/app.py
```

#### Terminal Version

If run the program in the terminal, the file must be located in the `inputs/` directory. For example, if you have an input file named `ok_optimized.c`, you can run the program like:

```bash
python unam.fi.compilers.g5.01/src/main.py ok_functions.c
```
If you don't want to run the program with an input file, you can execute it without arguments and the program will read the input from the console:

```bash
python unam.fi.compilers.g5.01/src/main.py
```