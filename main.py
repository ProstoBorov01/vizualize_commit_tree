import argparse
import subprocess
import os
import sys
import logging
from typing import Dict, List

def parse_args():

    parser = argparse.ArgumentParser(description='Git Dependency Graph Visualizer')
    parser.add_argument('--vizualize', required=True, help='Path to mermaid-cli')
    parser.add_argument('--repo', required=True, help='Path to the git repository to analyze')
    parser.add_argument('--output', required=True, help='Path to the output PNG file')
    parser.add_argument('--branch', required=True, help='Name of the branch to analyze')

    return parser.parse_args()


def get_commit_graph(repo_path: str, branch: str) -> Dict[str, List[str]]:

    logging.info(f"Начало анализа репозитория: {repo_path}, ветка: {branch}")

    try:
        if not os.path.isdir(repo_path):
            logging.error(f"Указанный путь не существует или это не директория: {repo_path}")
            raise ValueError(f"Repository path '{repo_path}' does not exist or is not a directory.")

        cmd = ['git', '-C', repo_path, 'log', branch, '--pretty=%H %P']
        logging.debug(f"Выполнение команды: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        commit_graph = {}
        for line in result.stdout.strip().split('\n'):
            parts = line.strip().split()
            if len(parts) == 0:
                continue
            commit = parts[0]
            parents = parts[1:] if len(parts) > 1 else []
            commit_graph[commit] = parents
            
        logging.info(f"Граф коммитов успешно получен. Количество узлов: {len(commit_graph)}")
        return commit_graph
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка выполнения команды Git: {e.stderr.strip()}")
        raise RuntimeError(f"Git command failed: {e.stderr.strip()}") from e


def generate_mermaid(commit_graph: Dict[str, List[str]]) -> str:

    logging.info("Генерация Mermaid-графа...")
    mermaid_lines = ["graph TD"]
    for commit, parents in commit_graph.items():
        if not parents:
            mermaid_lines.append(f'    {commit}')
        for parent in parents:
            mermaid_lines.append(f'    {commit} --> {parent}')
    
    logging.debug(f"Mermaid-граф успешно сгенерирован:\n{mermaid_lines}")

    return "\n".join(mermaid_lines)


def save_mermaid(mermaid_str: str, file_path: str):

    logging.info(f"Сохранение Mermaid-графа во временный файл: {file_path}")
    try:
        with open(file_path, 'w') as f:
            f.write(mermaid_str)
        logging.debug("Mermaid-граф успешно сохранен.")
    except IOError as e:
        logging.error(f"Ошибка записи файла: {e}")
        raise RuntimeError(f"Failed to write Mermaid file: {e}") from e
    

def visualize_graph(visualizer_path: str, mermaid_file: str, output_file: str):

    logging.info(f"Визуализация графа с помощью Node.js и Mermaid CLI, входной файл: {mermaid_file}, выходной файл: {output_file}")
    try:
        cmd = [
            visualizer_path,
            "-i", mermaid_file,
            "-o", output_file
        ]
        logging.debug(f"Выполнение команды: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        logging.info("Граф успешно визуализирован и сохранен.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка визуализации графа: {e.stderr.strip()}")
        raise RuntimeError(f"Visualization tool failed: {e.stderr.strip()}") from e


def main():

    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(levelname)s - %(message)s', 
        handlers=[
            logging.StreamHandler(sys.stdout) 
        ]
    )
    
    logging.info("Запуск программы Git Dependency Graph Visualizer.")
    args = parse_args()

    try:
        logging.info("Получение графа коммитов...")
        commit_graph = get_commit_graph(args.repo, args.branch)
        
        logging.info("Генерация описания Mermaid-графа...")
        mermaid_str = generate_mermaid(commit_graph)
        
        temp_mermaid = 'temp_graph.mmd'
        save_mermaid(mermaid_str, temp_mermaid)

        logging.info("Запуск визуализации...")
        visualize_graph(args.vizualize, temp_mermaid, args.output)

        logging.info("Очистка временных файлов...")
        os.remove(temp_mermaid)

        logging.info("Граф зависимостей успешно построен и сохранен.")
        
    except Exception as e:
        logging.critical(f"Ошибка выполнения: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

