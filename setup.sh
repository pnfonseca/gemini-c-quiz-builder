#!/usr/bin/env bash
set -e

echo "🚀 Setting up c-quiz-generator workspace..."

# 1. Create required directories
mkdir -p submissoes quizzes_gerados
echo "✅ Created directories: submissoes/ and quizzes_gerados/"

# 2. Make the main script executable
if [ -f "gerar_quizzes.py" ]; then
    chmod +x gerar_quizzes.py
    echo "✅ Set execution permissions on gerar_quizzes.py"
fi

# 3. Create .gitignore if missing
if [ ! -f ".gitignore" ]; then
    cat << 'EOF' > .gitignore
__pycache__/
*.py[cod]
*$py.class
.venv/
env/
venv/
ENV/
.env
.env.local
quizzes_gerados/
quizzes_finais/
*.pdf
repos_temp/
submissoes/
.vscode/
.idea/
.DS_Store
EOF
    echo "✅ Created .gitignore"
fi

# 4. Initialize Git repository if not already initialized
if [ ! -d ".git" ]; then
    git init
    echo "✅ Initialized Git repository"
fi

echo ""
echo "🎉 Setup complete! Next steps:"
echo "  1. Export your key: export GEMINI_API_KEY='your_key_here'"
echo "  2. Test the script: ./gerar_quizzes.py --help"
