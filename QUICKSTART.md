# Code Translator - Quick Start Guide

Get up and running in 5 minutes! This guide assumes you have Python installed.

## 🚀 Super Quick Setup

### 1. Download & Install (2 minutes)

Open your terminal and run:

```bash
# Download
git clone https://github.com/yourusername/code-translator.git
cd code-translator

# Install
pip3 install -r requirements.txt
```

### 2. Get an API Key (2 minutes)

Choose ONE provider:

**Option A: OpenAI (Recommended)**
- Go to https://platform.openai.com/api-keys
- Sign in → Create new secret key → Copy it

**Option B: Google (Free tier available)**
- Go to https://makersuite.google.com/app/apikey
- Sign in → Create API key → Copy it

### 3. Run & Configure (1 minute)

```bash
# Start the app
python3 src/main.py
```

1. Click the **⚙ Settings** button
2. Go to **API Keys** tab
3. Paste your key
4. Click **OK**

## 🎯 Your First Translation

1. **Paste** some Python code in the left panel:
   ```python
   def hello(name):
       print(f"Hello, {name}!")
   ```

2. Select **JavaScript** as target language

3. Press **Ctrl+Enter** or click **Translate**

4. See the result on the right:
   ```javascript
   function hello(name) {
       console.log(`Hello, ${name}!`);
   }
   ```

## ⌨️ Essential Shortcuts

- **Ctrl+Enter**: Translate
- **Ctrl+D**: Toggle dark/light theme
- **Ctrl+H**: View history
- **Ctrl+M**: Click-through mode

## 🎉 That's It!

You're ready to translate code! For more features, see the [full documentation](README.md).

### Pro Tips
- Drag & drop code files directly into the window
- Enable real-time translation in settings
- Star your favorite translations with ⭐

### Need Help?
- Run `python3 test_comprehensive.py` to check your setup
- See [INSTALLATION.md](INSTALLATION.md) for troubleshooting
- Check the [FAQ](docs/FAQ.md) for common questions