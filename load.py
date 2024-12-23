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
            standalone_files.extend([os.path.join(root, file) for file in files])
        break  # Zpracujeme pouze první úroveň

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

    if "deploy_react" not in settings or "deploy_laravel" not in settings:
        settings["deploy_react"] = input("Do you want to deploy React? (yes/no): ").strip().lower() == "yes"
        settings["deploy_laravel"] = input("Do you want to deploy Laravel? (yes/no): ").strip().lower() == "yes"
        save_settings(settings)

    # Deploy React
    deploy_react(settings)

    # Deploy Laravel
    deploy_laravel(settings)


if __name__ == "__main__":
    main()
