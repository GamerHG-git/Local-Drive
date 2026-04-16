LOCAL DRIVE - Self-Hosted File Management System
==============================================

A lightweight, production-ready Google Drive clone built with Python (Flask) and HTML/CSS/JS.

FEATURES
--------
- Dark/Light Mode - Toggle between themes, preference saved
- File Management - Upload, download, delete files and folders
- Folder Download - Server-side ZIP compression
- Favorites - Star files for quick access
- Sharing - Generate public share links
- Media Preview - Built-in lightbox for images, videos, and audio
- Cloud Dashboard - Server stats (CPU, RAM, uptime)
- Storage Statistics - Disk usage display
- Mobile Responsive - Works on phones and desktops
- 100% Offline - All icons are inline SVGs

REQUIREMENTS
------------
- Python 3.8+
- Flask
- Pillow (for image dimensions)

INSTALLATION
------------
1. Install dependencies:
apt install python3.11
pip install -r requirements.txt

3. Configure .env file:

   USERNAME=admin

   PASSWORD=password123

   SECRET_KEY=your-secret-key

5. Run the app:

   python app.py

7. Open browser:

    http://localhost:5000

DEFAULT CREDENTIALS
------------------

Username: admin

Password: password123

MEDIA SUPPORT
-------------
Images: jpg, jpeg, png, gif, webp, svg
Videos: mp4, webm, mov, avi, 3gp
Audio: mp3, wav, ogg, m4a, aac

KEYBOARD SHORTCUTS
------------------
Lightbox:
- Arrow Left/Right: Navigate media
- Escape: Close lightbox

FILE STORAGE
------------
All files are stored in the "drive-files" directory.

SECURITY NOTES
--------------
- Change default password in .env
- Use HTTPS in production
- Session cookies are signed with SECRET_KEY

TECHNICAL STACK
---------------
Backend: Python Flask
Frontend: HTML5, CSS3, Vanilla JS
Database: JSON files (favorites.json, shares.json)
