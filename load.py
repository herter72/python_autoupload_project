import subprocess
import json
import os
import threading
import sys

def check_and_install_packages():
    """Kontrola a instalace vyžadovaných balíčků."""
    required_packages = ["tqdm"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"📦 Installing missing package: {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Package '{package}' installed successfully.")

check_and_install_packages()

from tqdm import tqdm

def save_settings(settings):
    """Uložení konfigurace do JSON."""
    with open("deployment_config.json", "w") as f:
        json.dump(settings, f, indent=4)
    print("✅ Configuration updated and saved.")


def load_settings():
    """Načtení konfigurace."""
    if os.path.exists("deployment_config.json"):
        with open("deployment_config.json", "r") as f:
            return json.load(f)
    return {}

def is_executable(path):
    """Kontrola, zda je cesta spustitelný soubor."""
    return os.path.isfile(path) and os.access(path, os.X_OK)

def prompt_for_settings(settings):
    """Zajištění, že všechny hodnoty v nastavení budou vyplněny prostřednictvím uživatelského vstupu."""
    # Klíče a dotazy podle modulů
    general_keys = {
        "server_host": "Enter the server host (novakon25.mp.spse-net.cz): ",
        "server_port": "Enter the server port (1234): ",
        "server_user": "Enter the server username (novakon25): ",
        "server_pass": "Enter the server password (password): ",
        "server_url": "Enter the server URL (https://novakon25.mp.spse-net.cz/): "
    }

    react_keys = {
        "react_path": "Enter the path to your React project (absolute): ",
        "npm_path": "Enter the path to npm (for npm react build command): ",
        "remote_react_path": "Enter the remote path for React deployment (/web): "
    }

    laravel_keys = {
        "laravel_path": "Enter the path to your Laravel project (absolute): ",
        "php_path": "Enter the path to PHP (for php artisan optimize): ",
        "laravel_env_path": "Enter the path to the Laravel .env file (absolute): ",
        "remote_laravel_path": "Enter the remote path for Laravel deployment (/web): "
    }

    winscp_keys = {
        "winscp_path": "Enter the path to WinSCP (absolute from project folder): "
    }

    # Zeptejte se na obecné otázky
    for key, prompt in general_keys.items():
        if key not in settings or not settings[key]:
            settings[key] = input(prompt).strip()
            if key == "server_port":
                settings[key] = int(settings[key])

    # Zeptejte se, zda nasadit React nebo Laravel
    if "deploy_react" not in settings:
        settings["deploy_react"] = input("Do you want to deploy React? (yes/no): ").strip().lower() == "yes"

    if "deploy_laravel" not in settings:
        settings["deploy_laravel"] = input("Do you want to deploy Laravel? (yes/no): ").strip().lower() == "yes"

    # Pokud je nasazení Reactu povoleno, dotazy na React
    if settings["deploy_react"]:
        for key, prompt in react_keys.items():
            if key == "npm_path":
                # Kontrola existence npm pouze pokud není nastaveno
                if not settings.get(key) or not is_executable(settings[key]):
                    settings[key] = input(prompt).strip()
            elif key not in settings or not settings[key]:
                settings[key] = input(prompt).strip()

    # Pokud je nasazení Laravelu povoleno, dotazy na Laravel
    if settings["deploy_laravel"]:
        for key, prompt in laravel_keys.items():
            if key == "php_path":
                # Kontrola existence php pouze pokud není nastaveno
                if not settings.get(key) or not is_executable(settings[key]):
                    settings[key] = input(prompt).strip()
            elif key not in settings or not settings[key]:
                settings[key] = input(prompt).strip()

    # Dotazy na WinSCP (je potřeba pro obě nasazení)
    for key, prompt in winscp_keys.items():
        if not settings.get(key) or not is_executable(settings[key]):
            settings[key] = input(prompt).strip()

    return settings

def execute_command(command):
    """Spuštění příkazu a zpracování výstupu."""
    try:
        print(f"⏳ Executing: {command}")
        subprocess.run(command, shell=True, check=True)
        print("✅ Command executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Command execution failed: {e}")


def create_winscp_script(script_path, commands):
    """Vytvoření skriptu pro WinSCP."""
    with open(script_path, "w") as f:
        f.write("\n".join(commands))
    print(f"✅ WinSCP script created at {script_path}.")


def run_winscp(winscp_path, script_path):
    """Spuštění WinSCP skriptu."""
    try:
        print(f"⏳ Running WinSCP script: {script_path}")
        subprocess.run([winscp_path, f"/script={script_path}", "/log=winscp.log"], check=True)
        print(f"✅ WinSCP script executed successfully: {script_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ WinSCP script execution failed: {e}")


def deploy_react(settings):
    """Nasazení React projektu."""
    if not settings.get("deploy_react", False):
        print("React deployment is disabled.")
        return
    
    print("\n🚀 Starting React deployment...")
    react_path = settings["react_path"]
    remote_react_path = settings["remote_react_path"]
    winscp_path = settings["winscp_path"]

    # Build React project
    print("⏳ Building React project...")
    execute_command(f'cd "{react_path}" && "{settings["npm_path"]}" run build')

    # Create and run WinSCP script
    react_script = "react_sync_script.txt"
    create_winscp_script(react_script, [
        "option batch abort",
        "option confirm off",
        f'open sftp://{settings["server_user"]}:{settings["server_pass"]}@{settings["server_host"]}:{settings["server_port"]} -hostkey=*',
        f'lcd "{os.path.join(react_path, "build")}"',
        f'cd {remote_react_path}',
        "synchronize remote .",
        "exit",
    ])
    run_winscp(winscp_path, react_script)
    print("✅ React deployment completed.")


def deploy_laravel(settings):
    """Nasazení Laravel projektu pomocí více vláken."""
    if not settings.get("deploy_laravel", False):
        print("Laravel deployment is disabled.")
        return

    print("\n🚀 Starting Laravel deployment...")
    laravel_path = settings["laravel_path"]
    remote_laravel_path = settings["remote_laravel_path"]
    winscp_path = settings["winscp_path"]

    # Optimalizace Laravel projektu
    print("⏳ Optimizing Laravel project...")
    execute_command(f'"{settings["php_path"]}" -d memory_limit=-1 -d max_execution_time=300 -f "{os.path.join(laravel_path, "artisan")}" optimize')

    # Rozdělení Laravel projektu na složky a samostatné soubory
    folders = []
    standalone_files = []

    for root, dirs, files in os.walk(laravel_path):
        # Přidáme složky
        for folder in dirs:
            folders.append(os.path.join(root, folder))
        # Přidáme samostatné soubory z root Laravel projektu
        if root == laravel_path:
            standalone_files.extend([
                os.path.join(root, file) for file in files if not file.startswith(".env")
            ])
        break  # Zpracujeme pouze první úroveň

    # Přidání .env.production jako .env
    env_production_path = os.path.join(laravel_path, ".env.production")
    if os.path.exists(env_production_path):
        standalone_files.append(env_production_path)

    threads = []
    progress_bar = tqdm(total=len(folders) + (1 if standalone_files else 0), desc="Laravel Deployment", unit="task")

    # Funkce pro spuštění skriptů s progress barem
    def run_winscp_with_progress(script_name):
        try:
            run_winscp(winscp_path, script_name)
        finally:
            progress_bar.update(1)

    # Vlákna pro každou složku
    for folder in folders:
        folder_name = os.path.relpath(folder, laravel_path).replace("\\", "/")
        script_name = f"laravel_sync_{folder_name.replace('/', '_')}.txt"
        create_winscp_script(
            script_name,
            [
                "option batch abort",
                "option confirm off",
                f'open sftp://{settings["server_user"]}:{settings["server_pass"]}@{settings["server_host"]}:{settings["server_port"]} -hostkey=*',
                f'lcd "{folder}"',
                f'cd {remote_laravel_path}/{folder_name}',
                "synchronize remote .",
                "exit",
            ]
        )
        thread = threading.Thread(target=run_winscp_with_progress, args=(script_name,))
        threads.append(thread)

    # Vlákno pro samostatné soubory
    if standalone_files:
        script_name = "laravel_sync_standalone_files.txt"
        create_winscp_script(
            script_name,
            [
                "option batch abort",
                "option confirm off",
                f'open sftp://{settings["server_user"]}:{settings["server_pass"]}@{settings["server_host"]}:{settings["server_port"]} -hostkey=*',
                f'lcd "{laravel_path}"',
                f'cd {remote_laravel_path}',
                "synchronize remote .",
                f'put "{env_production_path}" {remote_laravel_path}/.env',
                "exit",
            ]
        )
        thread = threading.Thread(target=run_winscp_with_progress, args=(script_name,))
        threads.append(thread)

    # Spuštění všech vláken
    for thread in threads:
        thread.start()

    # Čekání na dokončení všech vláken
    for thread in threads:
        thread.join()

    progress_bar.close()
    print("✅ Laravel deployment completed with threads.")



def main():
    settings = load_settings()

    # Zajistěte, že všechna nastavení budou vyplněna
    settings = prompt_for_settings(settings)
    
    # Uložení aktualizovaných nastavení
    save_settings(settings)

    # Následné nasazení
    if settings["deploy_react"]:
        deploy_react(settings)
    if settings["deploy_laravel"]:
        deploy_laravel(settings)

if __name__ == "__main__":
    main()
