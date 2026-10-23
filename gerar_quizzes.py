#!/usr/bin/env python3
import os
import glob
import argparse
import subprocess
from pathlib import Path
from google import genai

# Substituição de segurança para evitar barras invertidas soltas a quebrar o LaTeX
        # (Converte \n isolado em `\n` se não estiver já protegido por crases)
import re

# Initialize the Gemini API client (uses GEMINI_API_KEY environment variable)
client = genai.Client()

SYSTEM_PROMPT = """
És um professor universitário da disciplina de Programação em C.
O teu objetivo é gerar um mini-quiz de avaliação/triagem curta com 5 perguntas de escolha múltipla para verificar a compreensão e apropriação dos conceitos do código C submetido pelos alunos.

Regras de Formatação e Conteúdo:
1. Título do documento: "Mini-Quiz de Programação em C". NUNCA uses termos como "Verificação de Autoria" ou "Fraude".
2. Língua: Português Europeu.
3. Formato das Opções: OBRIGATÓRIO usar caixas de seleção no seguinte formato exato para TODAS as opções:
   - [ ] A) Texto da opção
   - [ ] B) Texto da opção
   - [ ] C) Texto da opção
   - [ ] D) Texto da opção

4. Estrutura das Perguntas:
   - 5 questões de escolha múltipla com apenas 1 opção correta.
   - Foco na compreensão das opções de implementação (ex: funcionamento de fórmulas, tratamento de erros, limites de variáveis, controlo de fluxo).
   - Respostas rápidas e diretas para quem trabalhou ou estudou o código.

5. Formato de Saída (MUITO IMPORTANTE):
   Deverás dividir a tua resposta exatamente em DUAS secções separadas pela marca "=== CHAVE DE CORRECAO ===":

[INÍCIO DA PRIMEIRA SECÇÃO - QUIZ DO ALUNO]
# Mini-Quiz de Programação em C

**Nome do Aluno:** ____________________________________  **Data:** ______________
**Grupo / Projeto:** {nome_identificador}

---

1. [Texto da Pergunta 1]
   - [ ] A) [Opção A]
   - [ ] B) [Opção B]
   - [ ] C) [Opção C]
   - [ ] D) [Opção D]

... (para as 5 perguntas)

=== CHAVE DE CORRECAO ===

[INÍCIO DA SEGUNDA SECÇÃO - CHAVE DO DOCENTE]
# Chave de Correção (Uso Exclusivo do Docente)
**Grupo / Projeto:** {nome_identificador}

1. Opção Correta: [Ex: B] - [Breve explicação de 1 frase do conceito]
2. Opção Correta: [Ex: A] - [Breve explicação de 1 frase do conceito]
...
"""

def converter_md_para_pdf(ficheiro_md, ficheiro_pdf):
    """Converts a Markdown file to PDF locally using pandoc on Linux."""
    try:
        resultado = subprocess.run(
            ["pandoc", ficheiro_md, "-o", ficheiro_pdf],
            capture_output=True,
            text=True
        )
        if resultado.returncode == 0:
            print(f"📄 PDF do Quiz (Aluno) gerado localmente: {ficheiro_pdf}")
        else:
            print(f"⚠️ Aviso ao converter PDF via pandoc: {resultado.stderr.strip()}")
    except FileNotFoundError:
        print("⚠️ A ferramenta 'pandoc' não foi encontrada no sistema.")
        print("   Para gerar PDFs automaticamente, instale no terminal: sudo apt install pandoc texlive-latex-base")
    except Exception as e:
        print(f"⚠️ Erro ao executar conversão para PDF: {e}")

def ler_codigo_c_pasta(caminho_pasta):
    """Finds and concatenates all .c and .h code files in a folder."""
    conteudo_total = ""
    ficheiros = glob.glob(os.path.join(caminho_pasta, "**", "*.[ch]"), recursive=True)
    
    for f in ficheiros:
        rel_path = os.path.relpath(f, caminho_pasta)
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                conteudo_total += f"\n\n--- FICHEIRO: {rel_path} ---\n"
                conteudo_total += file.read()
        except Exception as e:
            print(f"❌ Erro ao ler {f}: {e}")
            
    return conteudo_total

def processar_repositorio_git(repo_url, pasta_destino="./repos_temp"):
    """Clones or pulls a Git repository."""
    nome_repo = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
    caminho_local = os.path.join(pasta_destino, nome_repo)
    
    if os.path.exists(caminho_local):
        print(f"🔄 Repositório {nome_repo} já existe localmente. A efetuar git pull...")
        subprocess.run(["git", "-C", caminho_local, "pull"], check=False)
    else:
        print(f"📥 A clonar {nome_repo}...")
        subprocess.run(["git", "clone", repo_url, caminho_local], check=True)
        
    return caminho_local, nome_repo

def gerar_quiz_grupo(nome_identificador, codigo_c, modelo="gemini-3.8-flash", pasta_saida="./quizzes_gerados", forcar=False, gerar_pdf=True):
    """Sends C code to Gemini, splits output into Student Quiz and Teacher Key, and compiles Student PDF."""
    os.makedirs(pasta_saida, exist_ok=True)
    ficheiro_quiz_md = os.path.join(pasta_saida, f"quiz_{nome_identificador}.md")
    ficheiro_chave_md = os.path.join(pasta_saida, f"chave_{nome_identificador}.md")
    ficheiro_quiz_pdf = os.path.join(pasta_saida, f"quiz_{nome_identificador}.pdf")
    
    # Resume check
    if os.path.exists(ficheiro_quiz_md) and os.path.getsize(ficheiro_quiz_md) > 0 and not forcar:
        print(f"⏩ [Ignorado] Quiz para '{nome_identificador}' já existe em: {ficheiro_quiz_md}")
        if gerar_pdf and not os.path.exists(ficheiro_quiz_pdf):
            converter_md_para_pdf(ficheiro_quiz_md, ficheiro_quiz_pdf)
        return

    if not codigo_c.strip():
        print(f"⚠️ Sem ficheiros .c ou .h encontrados em: {nome_identificador}")
        return

    prompt = f"Gera um mini-quiz de programação para o grupo/trabalho '{nome_identificador}' com base neste código C:\n\n{codigo_c}"
    
    print(f"🚀 A gerar quiz para '{nome_identificador}' usando o modelo '{modelo}'...")
    
    try:
        response = client.models.generate_content(
            model=modelo,
            contents=prompt,
            config={'system_instruction': SYSTEM_PROMPT}
        )
        
        texto_completo = response.text
        
        # Split into Student Quiz and Teacher Solution Key
        if "=== CHAVE DE CORRECAO ===" in texto_completo:
            partes = texto_completo.split("=== CHAVE DE CORRECAO ===")
            conteudo_quiz = partes[0].strip()
            conteudo_chave = partes[1].strip()
        else:
            conteudo_quiz = texto_completo.strip()
            conteudo_chave = "Chave de correção não gerada separadamente."

        conteudo_quiz = re.sub(r'(?<!`)\\(n|t|r|0)(?!`)', r'`\\\1`', conteudo_quiz)

        # 1. Save Student Quiz Markdown
        with open(ficheiro_quiz_md, 'w', encoding='utf-8') as f:
            f.write(conteudo_quiz)
        print(f"✅ Quiz do Aluno guardado em: {ficheiro_quiz_md}")

        # 2. Save Teacher Key Markdown
        with open(ficheiro_chave_md, 'w', encoding='utf-8') as f:
            f.write(conteudo_chave)
        print(f"🔑 Chave do Docente guardada em: {ficheiro_chave_md}")
        
        # 3. Generate PDF for Student Quiz ONLY (0 token consumption)
        if gerar_pdf:
            converter_md_para_pdf(ficheiro_quiz_md, ficheiro_quiz_pdf)
            
    except Exception as e:
        print(f"❌ Erro ao gerar quiz para '{nome_identificador}': {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Gera mini-quizzes de avaliação de Programação em C (em Markdown e PDF) a partir de pastas locais ou repositórios GitHub.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de Utilização:
  1. Executar na pasta atual (gerando MD e PDF em ./quizzes_gerados com gemini-3.8-flash por defeito):
     python3 gerar_quizzes.py

  2. Processar uma pasta específica de submissões:
     python3 gerar_quizzes.py -p ./turma_A

  3. Definir a pasta de saída dos quizzes e forçar a regeração de ficheiros existentes:
     python3 gerar_quizzes.py -p ./submissoes -o ./quizzes_finais -f

  4. Desativar a conversão para PDF (gerar apenas Markdown):
     python3 gerar_quizzes.py --sem-pdf
"""
    )
    
    parser.add_argument("-p", "--pasta", default="./", help="Caminho para a pasta local com as submissões dos alunos (padrão: './')")
    parser.add_argument("-o", "--saida", default="./quizzes_gerados", help="Pasta onde serão guardados os ficheiros .md e .pdf (padrão: './quizzes_gerados')")
    parser.add_argument("-m", "--modo", choices=["local", "github", "ambos"], default="local", help="Modo de carregamento do código: 'local', 'github' ou 'ambos' (padrão: 'local')")
    parser.add_argument("--modelo", default="gemini-3.8-flash", help="Identificador do modelo Gemini da API (padrão: 'gemini-3.8-flash')")
    parser.add_argument("-f", "--forcar", action="store_true", help="Forçar a regeração de todos os quizzes mesmo que já existam na pasta de destino")
    parser.add_argument("--sem-pdf", action="store_true", help="Desativar a conversão automática para PDF (gera apenas ficheiros .md)")
    
    args = parser.parse_args()
    gerar_pdf = not args.sem_pdf
    
    # -------------------------------------------------------------------------
    # MODO LOCAL
    # -------------------------------------------------------------------------
    if args.modo in ["local", "ambos"]:
        pasta_base = os.path.abspath(args.pasta)
        print(f"\n📂 A processar pastas em: {pasta_base}")
        
        if os.path.exists(pasta_base):
            subpastas = [f for f in os.listdir(pasta_base) if os.path.isdir(os.path.join(pasta_base, f)) and f != os.path.basename(args.saida)]
            
            ficheiros_diretos = glob.glob(os.path.join(pasta_base, "*.[ch]"))
            if not subpastas and ficheiros_diretos:
                nome_grupo = os.path.basename(pasta_base) or "projeto_local"
                codigo = ler_codigo_c_pasta(pasta_base)
                gerar_quiz_grupo(nome_grupo, codigo, modelo=args.modelo, pasta_saida=args.saida, forcar=args.forcar, gerar_pdf=gerar_pdf)
            else:
                for subpasta in subpastas:
                    caminho_subpasta = os.path.join(pasta_base, subpasta)
                    codigo = ler_codigo_c_pasta(caminho_subpasta)
                    gerar_quiz_grupo(subpasta, codigo, modelo=args.modelo, pasta_saida=args.saida, forcar=args.forcar, gerar_pdf=gerar_pdf)
        else:
            print(f"❌ A pasta especificada '{pasta_base}' não existe.")

    # -------------------------------------------------------------------------
    # MODO GITHUB
    # -------------------------------------------------------------------------
    if args.modo in ["github", "ambos"]:
        REPOS_GITHUB = [
            # Add GitHub repository URLs here if needed
        ]
        
        if REPOS_GITHUB:
            print("\n🌐 A processar repositórios GitHub...")
            for repo_url in REPOS_GITHUB:
                try:
                    caminho_local, nome_grupo = processar_repositorio_git(repo_url)
                    codigo = ler_codigo_c_pasta(caminho_local)
                    gerar_quiz_grupo(nome_grupo, codigo, modelo=args.modelo, pasta_saida=args.saida, forcar=args.forcar, gerar_pdf=gerar_pdf)
                except Exception as e:
                    print(f"❌ Erro ao processar o repositório {repo_url}: {e}")

if __name__ == "__main__":
    main()
