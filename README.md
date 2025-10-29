# Library Management System

A comprehensive library management system built with Frappe Framework.

## Features

- **Article Management**: Create, edit, and manage library articles
- **User Management**: Member registration and authentication
- **Library Transactions**: Issue and return tracking
- **Modern Web Interface**: Responsive design with Bootstrap
- **Role-based Permissions**: Administrator, Librarian, and Member roles
- **API Integration**: RESTful API for all operations

## Tech Stack

- **Backend**: Frappe Framework (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: MariaDB/MySQL
- **Web Server**: Nginx

## Quick Start

### Prerequisites

- Ubuntu 20.04+ or WSL2 (Windows)
- Python 3.8+
- Node.js 16+
- MariaDB/MySQL
- Redis

### Installation

#### Method 1: Using Bench Commands (Recommended)

```bash
# Create a new bench
bench init frappe-bench --frappe-branch version-14
cd frappe-bench

# Create a site
bench new-site library.localhost

# Install the app
bench get-app library_management https://github.com/yasserbousrih/library_management.git
bench --site library.localhost install-app library_management

# Enable Developer Mode (recommended for development)
bench --site library.localhost set-config developer_mode 1
bench --site library.localhost migrate

# Start the server
bench start
```

#### Method 2: Manual Installation

```bash
# Clone the app manually
cd apps
git clone https://github.com/yasserbousrih/library_management.git
cd ..

# Add to apps.txt
echo -e "frappe\nlibrary_management" > apps.txt

# Install the app
bench --site library.localhost install-app library_management

# Enable Developer Mode (recommended for development)
bench --site library.localhost set-config developer_mode 1
bench --site library.localhost migrate
```

### Access the Application

- **Web Interface**: http://library.localhost:8000
- **Admin Panel**: http://library.localhost:8000/app
- **Default Login**: 
  - Username: `Administrator`
  - Email: `admin@example.com`
  - Password: `12345678` (or your site creation password)

### Developer Mode

Developer Mode provides enhanced debugging capabilities:
- **Detailed error messages** in the browser
- **Source code visibility** for debugging
- **Enhanced logging** for development
- **Hot reloading** for faster development cycles

To enable/disable Developer Mode:
```bash
# Enable Developer Mode
bench --site library.localhost set-config developer_mode 1
bench --site library.localhost migrate

# Disable Developer Mode (for production)
bench --site library.localhost set-config developer_mode 0
bench --site library.localhost migrate
```

## Project Structure

```
apps/library_management/
├── hooks.py                    # App configuration
├── library_management/         # Main Python package
│   ├── __init__.py            # Version info
│   ├── build.json             # Asset configuration
│   ├── api.py                 # API endpoints
│   ├── doctype/               # DocType definitions
│   │   ├── article/
│   │   ├── library_member/
│   │   └── library_transaction/
│   └── public/                # Static assets
├── www/                       # Web pages
│   ├── home/
│   ├── signup/
│   ├── articles-page/
│   └── my-articles/
└── templates/                 # Jinja templates
    └── includes/
```

### App Structure Notes for Contributors

**Important**: `hooks.py`, `patches.txt`, `modules.txt` must stay at `apps/library_management/`.
The Python package (modules, DocTypes) live in `apps/library_management/library_management/`.
**Do NOT put `hooks.py` inside the package folder.**

## DocTypes

- **Article**: Library articles with metadata
- **Library Member**: User management
- **Library Transaction**: Issue/return tracking
- **Library Membership**: Member status management
- **Library Settings**: System configuration

## API Endpoints

- `POST /api/method/library_management.api.signup` - User registration
- `GET /api/method/library_management.api.get_articles` - List articles
- `POST /api/method/library_management.api.issue_article` - Issue article
- `POST /api/method/library_management.api.return_article` - Return article

## Troubleshooting

### Common Issues

1. **"No module named 'library_management'" Error**:
   ```bash
   # Test Python import
   cd apps
   python3 -c "import library_management.hooks; print('Import successful')"
   ```

2. **Build Error & App Not in apps.txt**:
   ```bash
   # Bulletproof fix
   echo -e "frappe\nlibrary_management" > apps.txt
   echo -e "frappe\nlibrary_management" > sites/apps.txt
   bench build --app library_management
   bench --site your-site.localhost install-app library_management
   ```

3. **Permission Errors**:
   ```bash
   sudo chown -R $USER:$USER ~/frappe-bench
   ```

### 🔍 Frappe Installation Debug: apps.txt Issue

**Problem:**
If you see errors like:
```
App library_management not in apps.txt
```
but your app is present and listed in your bench root `apps.txt`, it's likely that Frappe is using the `sites/apps.txt` file (not the root one) for actual site installations!

**Solution:**
Check both files:
```bash
cat apps.txt
cat sites/apps.txt
```

Edit `sites/apps.txt`:
Make sure it contains one app name per line, no extra whitespace or blank lines:
```
frappe
library_management
```

Save and retry the app install:
```bash
bench --site your-site-name install-app library_management
```

If you still face the issue, restart bench:
```bash
bench restart
bench setup requirements --python
bench --site your-site-name install-app library_management
```

**Why It Matters:**
Frappe uses the `sites/apps.txt` file as the registry for site installations, even if your app and root `apps.txt` are correct. Missing entries here will block every install, migration, and app build until fixed.

### 🚨 Asset Build Debug: esbuild Error

**Problem:**
If you see errors like:
```
TypeError [ERR_INVALID_ARG_TYPE]: The "paths[0]" argument must be of type string. Received undefined
```

**Root Cause:**
Frappe's `get_public_path(app)` returns undefined because it can't find the `public` folder in the correct location.

**Solution:**
1. **Check directory structure** - Ensure `public` folder is directly inside your app root:
   ```
   apps/library_management/
   ├── public/                    ← CORRECT location
   │   ├── css/
   │   └── js/
   ├── library_management/
   └── ...
   ```

2. **Remove duplicate public folders** - Don't have `public` inside `library_management/library_management/`

3. **Temporarily remove assets** if needed:
   ```bash
   # Comment out asset references in hooks.py
   # app_include_css = "/assets/library_management/css/library_management.css"
   # app_include_js = "/assets/library_management/js/library_management.js"
   
   # Remove public folder temporarily
   rm -rf apps/library_management/public
   
   # Test with --skip-assets
   bench get-app library_management https://github.com/yasserbousrih/library_management.git --skip-assets
   ```

### App Maintenance

```bash
# Update the app
bench update --patch

# Remove the app
bench --site your-site.localhost uninstall-app library_management
bench remove-app library_management

# View current apps
cat apps.txt
```

## Development

### Adding New Features

1. Create DocTypes in `library_management/doctype/`
2. Add API endpoints in `api.py`
3. Create web pages in `www/`
4. Update permissions in DocType JSON files

### Testing

```bash
# Run tests
bench --site your-site.localhost run-tests library_management

# Check app status
bench --site your-site.localhost list-apps
```

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/yasserbousrih/library_management/issues)
- Email: yasser040503@gmail.com

---

**Ready for Production**: This app meets all Frappe installation requirements and is ready for deployment.