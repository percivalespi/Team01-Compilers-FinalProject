import os
import subprocess
import platform
import shutil

class ExecutableGenerator:


    @staticmethod
    def is_local_env_ready():

        return shutil.which("nasm") is not None and shutil.which("gcc") is not None

    @staticmethod
    def _wsl_path(win_path: str) -> str:

        win_path = os.path.abspath(win_path)
        drive, tail = os.path.splitdrive(win_path)
        drive = drive.replace(":", "").lower()
        tail = tail.replace("\\", "/")
        return f"/mnt/{drive}{tail}"

    @staticmethod
    def compile_and_run(asm_code: str, user_input: str = "") -> dict:

        current_host = platform.system().lower()
        if current_host == "windows":
            if shutil.which("wsl"):
                return ExecutableGenerator._run_local_wsl(asm_code, user_input)
            else:
                return {"success": False, "output": "Error: WSL no está instalado o configurado en este equipo Windows.", "binary": b""}
        else:
            if ExecutableGenerator.is_local_env_ready():
                return ExecutableGenerator._run_local_native(asm_code, user_input)
            else:
                return {"success": False, "output": "Error: Faltan instalar 'nasm' o 'gcc' en el servidor de Linux.", "binary": b""}

    @staticmethod
    def _run_local_wsl(asm_code: str, user_input: str = "") -> dict:
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs", "out"))
        os.makedirs(out_dir, exist_ok=True)
        
        base_filename = "a.out"
        asm_path = os.path.join(out_dir, "source.asm")
        obj_path = os.path.join(out_dir, "source.o")
        exe_path = os.path.join(out_dir, base_filename)

        with open(asm_path, "w", encoding="utf-8") as f:
            f.write(asm_code.replace('\x00', ''))

        wsl_asm, wsl_obj, wsl_exe = map(ExecutableGenerator._wsl_path, [asm_path, obj_path, exe_path])

        try:
            res_nasm = subprocess.run(["wsl", "nasm", "-f", "elf64", wsl_asm, "-o", wsl_obj], capture_output=True, text=True)
            if res_nasm.returncode != 0:
                return {"success": False, "output": f"NASM Error:\n{res_nasm.stderr}", "binary": b""}
            res_gcc = subprocess.run(["wsl", "gcc", wsl_obj, "-o", wsl_exe, "-no-pie"], capture_output=True, text=True)
            if res_gcc.returncode != 0:
                return {"success": False, "output": f"GCC Error:\n{res_gcc.stderr}", "binary": b""}
            with open(exe_path, "rb") as b_file:
                binary = b_file.read()

            try:
                res_run = subprocess.run(["wsl", wsl_exe], input=user_input, capture_output=True, text=True, timeout=3)
                output = res_run.stdout
                if res_run.returncode != 0 and res_run.stderr:
                    output += "\n" + res_run.stderr
                return {"success": True, "output": output.strip(), "binary": binary}
            except subprocess.TimeoutExpired as e:
                out_msg = "El programa tardó demasiado (posible bucle infinito o esperando entrada como scanf sin datos).\n¡Descarga el archivo a.out y córrelo en tu terminal real de WSL para interactuar con él!"
                if e.stdout:
                    out_msg += "\n\nSalida parcial:\n" + e.stdout
                return {"success": True, "output": out_msg, "binary": binary}
            
        except Exception as e:
            return {"success": False, "output": f"Error del sistema en WSL:\n{str(e)}", "binary": b""}

    @staticmethod
    def _run_local_native(asm_code: str, user_input: str = "") -> dict:
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs", "out"))
        os.makedirs(out_dir, exist_ok=True)
        
        asm_path = os.path.join(out_dir, "source.asm")
        obj_path = os.path.join(out_dir, "source.o")
        exe_path = os.path.join(out_dir, "a.out")

        with open(asm_path, "w", encoding="utf-8") as f:
            f.write(asm_code.replace('\x00', ''))

        try:
            res_nasm = subprocess.run(["nasm", "-f", "elf64", asm_path, "-o", obj_path], capture_output=True, text=True)
            if res_nasm.returncode != 0:
                return {"success": False, "output": f"NASM Error:\n{res_nasm.stderr}", "binary": b""}
            
            res_gcc = subprocess.run(["gcc", obj_path, "-o", exe_path, "-no-pie"], capture_output=True, text=True)
            if res_gcc.returncode != 0:
                return {"success": False, "output": f"GCC Error:\n{res_gcc.stderr}", "binary": b""}
            with open(exe_path, "rb") as b_file:
                binary = b_file.read()

            try:
                res_run = subprocess.run([exe_path], input=user_input, capture_output=True, text=True, timeout=3)
                output = res_run.stdout
                if res_run.returncode != 0 and res_run.stderr:
                    output += "\n" + res_run.stderr
                return {"success": True, "output": output.strip(), "binary": binary}
            except subprocess.TimeoutExpired as e:
                out_msg = "El programa tardó demasiado (posible bucle infinito o esperando entrada como scanf sin datos).\n¡Descarga el archivo a.out y córrelo en tu terminal real para interactuar con él!"
                if e.stdout:
                    out_msg += "\n\nSalida parcial:\n" + e.stdout
                return {"success": True, "output": out_msg, "binary": binary}
            
        except Exception as e:
            return {"success": False, "output": f"Error del sistema nativo:\n{str(e)}", "binary": b""}