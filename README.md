# C Quiz Generator (`c-quiz-generator`)

An automated Python CLI tool that analyzes student C programming project submissions (from local directories or GitHub repositories) and uses the **Google Gemini API** to generate tailored 5-question multiple-choice quizzes and separate teacher answer keys in Markdown and PDF formats.

Designed for university programming courses to assess student comprehension and concept appropriation.

## Features

- Automated Code Parsing: Recursively reads `.c` and `.h` source files across student project folders.
- Flexible Inputs: Works with local submission subfolders (`./submissoes/`) or GitHub repository URLs.
- Separate Student & Teacher Outputs:
  - **Student Worksheet (`quiz_<group>.pdf` & `quiz_<group>.md`)**: Printable quiz with standard `[ ]` checkboxes and student/date headers.
  - **Teacher Key (`chave_<group>.md`)**: Solution key with answer letters and 1-sentence concept explanations.
- Resume Support: Automatically skips previously generated quizzes to prevent unnecessary API calls and allow resuming interrupted runs.
- Zero-Token Local PDF Generation: Converts Markdown worksheets to PDF locally via `pandoc`.

## Prerequisites

- Linux (Ubuntu/Debian recommended)
- Python 3.10+
- Pandoc and LaTeX (for local PDF compilation)

## Quick Start

1. Clone or download this repository.
2. Install the required dependencies: `google-genai`
3. Export your API Key: `export GEMINI_API_KEY="your_key"`
4. Run the script: `python3 gerar_quizzes.py`

## CLI Options

- `-p`, `--pasta`: Path to local submissions directory (default: `./`)
- `-o`, `--saida`: Output folder for quizzes and keys (default: `./quizzes_gerados`)
- `-m`, `--modo`: Input mode (`local`, `github`, or `ambos`)
- `--modelo`: Gemini model identifier (default: `gemini-3.8-flash`)
- `-f`, `--forcar`: Force regeneration of existing quizzes
- `--sem-pdf`: Disable local PDF generation

## Repository Structure

- `gerar_quizzes.py`: Main Python script
- `setup.sh`: Environment and repo setup helper script
- `README.md`: Project documentation
- `.gitignore`: Git ignore rules
- `submissoes/`: Default local folder for student subdirectories
- `quizzes_gerados/`: Generated output folder (`.md` and `.pdf` files)

## License

MIT License
