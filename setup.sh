#!/usr/bin/env bash
# Tech Career Fit Engine - Project setup (see README.md)
# Requires: network, Python 3.11+, Node 18+, npm
# Ubuntu/Debian: sudo apt install python3.10-venv  (if venv fails)
set -e
cd "$(dirname "$0")"

echo "==> Backend setup"
cd backend

# Create .env from template if missing
if [[ ! -f .env ]]; then
  cp env.template .env
  echo "    Created .env from env.template — edit .env and set GEMINI_API_KEY"
fi

# Ensure data dirs exist
mkdir -p data data/sessions

# Virtual environment (ensure valid: has activate and pip)
create_venv() {
  if python3 -m venv venv 2>/dev/null && [[ -f venv/bin/activate ]]; then
    echo "    Created venv with python3 -m venv"
    return 0
  fi
  rm -rf venv
  if command -v virtualenv &>/dev/null; then
    python3 -m virtualenv venv && [[ -f venv/bin/activate ]] && { echo "    Created venv with virtualenv"; return 0; }
    rm -rf venv
  fi
  return 1
}
if [[ ! -f venv/bin/activate ]]; then
  if ! create_venv; then
    echo "    python3 -m venv failed (install: sudo apt install python3.10-venv)"
    echo "    Or: pip3 install --user virtualenv, then re-run setup.sh"
    exit 1
  fi
fi
source venv/bin/activate
pip install -r requirements.txt
echo "    Backend deps installed"

echo ""
echo "==> Frontend setup"
cd ../frontend
npm install
echo "    Frontend deps installed"

echo ""
echo "==> Done. Next steps:"
echo "    1. Edit backend/.env and set GEMINI_API_KEY=your-key"
echo "    2. Terminal 1: cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo "    3. Terminal 2: cd frontend && npm run dev"
echo "    4. Open http://localhost:3000"
