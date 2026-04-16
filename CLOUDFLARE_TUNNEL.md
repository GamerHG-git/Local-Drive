# Cloudflare Tunnel Setup Guide

Expose your local Google Drive clone to the internet using Cloudflare Tunnel (no Docker required).

## Step 1: Download cloudflared

### Windows
1. Download the latest `cloudflared-windows-amd64.exe` from:
   https://github.com/cloudflare/cloudflared/releases
2. Rename it to `cloudflared.exe` and place it somewhere convenient (e.g., `C:\cloudflared\cloudflared.exe`).

### Linux
```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/
```

### macOS
```bash
brew install cloudflared
```

## Step 2: Start Your Flask App

```bash
pip install -r requirements.txt
python app.py
```

Your app should now be running on `http://localhost:5000`.

## Step 3: Create a Quick Tunnel (No Account Needed)

### Windows (PowerShell or CMD)
```powershell
.\cloudflared.exe tunnel --url http://localhost:5000
```

### Linux/macOS
```bash
cloudflared tunnel --url http://localhost:5000
```

You will see output like this:
```
+--------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at:                  |
|  https://some-random-words.trycloudflare.com                       |
+--------------------------------------------------------------------+
```

That URL is now publicly accessible and proxies to your local app.

## Step 4 (Optional): Persistent Tunnel with a Custom Domain

If you want a permanent URL with your own domain:

1. **Create a Cloudflare account** and add your domain to Cloudflare DNS.
2. **Authenticate cloudflared:**
   ```bash
   cloudflared tunnel login
   ```
3. **Create a named tunnel:**
   ```bash
   cloudflared tunnel create my-drive
   ```
4. **Configure the tunnel** - create a file `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: my-drive
   credentials-file: /path/to/your/credentials.json

   ingress:
     - hostname: drive.yourdomain.com
       service: http://localhost:5000
     - service: http_status:404
   ```
5. **Route DNS to the tunnel:**
   ```bash
   cloudflared tunnel route dns my-drive drive.yourdomain.com
   ```
6. **Run the tunnel:**
   ```bash
   cloudflared tunnel run my-drive
   ```

## Security Notes

- The quick tunnel URL changes every time you restart `cloudflared`.
- Anyone with the URL can access your app (but they still need the login credentials from `.env`).
- For production use, set up a persistent tunnel with your own domain and consider adding Cloudflare Access for additional authentication.
- Never commit your `.env` file to version control.
