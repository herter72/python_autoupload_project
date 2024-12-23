# Deployment Script

## Funkce
- **Nasazení Laravelu pomocí vláken**: Paralelní nahrávání složek a souborů.
- **Práce s `.env` soubory**: Nahraje `.env.production` jako `.env` a ignoruje ostatní `.env` soubory.
- **Optimalizace projektu**: Spustí příkaz `artisan optimize` před nasazením.
- **Nasazení Reactu**: Automaticky vytvoří build React projektu a nahraje ho na server.
- **Progress bar**: Zobrazuje průběh nasazení.

## Požadavky
- **Python**: Pro spuštění skriptu.
- **WinSCP**: Instalovaný a dostupný.
- **PHP**: Cesta k PHP exekutábli.
- **Node.js a npm**: Pro vytvoření React buildu.
- **Nastavení serveru**: Hostitel, port, uživatel a heslo.

## Použití
1. Nastavte potřebné hodnoty v `settings` (např. cesty k souborům, serverové údaje).
2. Spusťte funkce `deploy_laravel(settings)` nebo `deploy_react(settings)` podle potřeby.

### Příklad nastavení
```python
settings = {
    "deploy_laravel": True,
    "laravel_path": "C:\\cesta\\k\\laravel",
    "remote_laravel_path": "/var/www/laravel",
    "php_path": "C:\\cesta\\k\\php.exe",
    "winscp_path": "C:\\cesta\\k\\WinSCP.exe",
    "server_host": "example.com",
    "server_port": 22,
    "server_user": "uzivatel",
    "server_pass": "heslo",
    "deploy_react": True,
    "react_path": "C:\\cesta\\k\\react",
    "npm_path": "C:\\Program Files\\nodejs\\npm.cmd",
    "remote_react_path": "/var/www/react"
}
```

## Poznámky
- Nasazení Laravelu zpracovává pouze soubory a složky na první úrovni.
- `.env.production` je přejmenován na `.env` a ostatní `.env` soubory jsou ignorovány.
- React build je vytvořen pomocí `npm run build` a následně nahrán na vzdálený server.

