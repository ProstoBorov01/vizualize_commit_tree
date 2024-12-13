import unittest
from unittest.mock import patch, mock_open, MagicMock
import main
import subprocess
import sys

class TestGitDependencyGraphVisualizer(unittest.TestCase):

    def setUp(self):

        self.repo_path = 'C:/Users/SavvinPC/Documents/TAIGA/Betton_Admin_Endpoint'
        self.branch = 'main'
        self.visualizer_path = 'C://Users//SavvinPC//AppData//Roaming//npm//mmdc.cmd'
        self.output_file = 'graph.png'
        self.temp_mermaid_file = 'temp_graph.mmd'
        self.commit_graph = {
            'commit1': [],
            'commit2': ['commit1'],
            'commit3': ['commit2'],
            'commit4': ['commit2', 'commit3'],
        }
        self.mermaid_str = """graph TD
    commit1
    commit2 --> commit1
    commit3 --> commit2
    commit4 --> commit2
    commit4 --> commit3"""

    @patch('main.os.path.isdir', return_value=True)
    @patch('main.subprocess.run')
    def test_get_commit_graph_success(self, mock_run, mock_isdir):

        mock_run.return_value = subprocess.CompletedProcess(
            args=['git', '-C', self.repo_path, 'log', self.branch, '--pretty=%H %P'],
            returncode=0,
            stdout='commit1\ncommit2 commit1\ncommit3 commit2\ncommit4 commit2 commit3\n',
            stderr=''
        )

        result = main.get_commit_graph(self.repo_path, self.branch)
        self.assertEqual(result, self.commit_graph)
        mock_run.assert_called_once_with(
            ['git', '-C', self.repo_path, 'log', self.branch, '--pretty=%H %P'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

    def test_generate_mermaid(self):
        mermaid = main.generate_mermaid(self.commit_graph)
        self.assertEqual(mermaid.strip(), self.mermaid_str.strip())

    @patch('builtins.open', new_callable=mock_open)
    def test_save_mermaid_success(self, mock_file):
        try:
            main.save_mermaid(self.mermaid_str, self.temp_mermaid_file)
        except Exception as e:
            self.fail(f"save_mermaid raised an exception {e}")
        mock_file.assert_called_once_with(self.temp_mermaid_file, 'w')
        mock_file().write.assert_called_once_with(self.mermaid_str)

    @patch('main.subprocess.run')
    def test_visualize_graph_success(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[self.visualizer_path, '-i', self.temp_mermaid_file, '-o', self.output_file],
            returncode=0,
            stdout='',
            stderr=''
        )
        try:
            main.visualize_graph(self.visualizer_path, self.temp_mermaid_file, self.output_file)
        except Exception as e:
            self.fail(f"visualize_graph raised an exception {e}")
        mock_run.assert_called_once_with(
            [self.visualizer_path, '-i', self.temp_mermaid_file, '-o', self.output_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

    @patch('main.os.remove')
    @patch('main.visualize_graph')
    @patch('main.save_mermaid')
    @patch('main.generate_mermaid')
    @patch('main.get_commit_graph')
    @patch('main.parse_args')
    @patch('main.logging')
    def test_main_success(self, mock_logging, mock_parse_args, mock_get_commit_graph,
                          mock_generate_mermaid, mock_save_mermaid, mock_visualize_graph,
                          mock_remove):

        mock_parse_args.return_value = main.argparse.Namespace(
            vizualize=self.visualizer_path,
            repo=self.repo_path,
            output=self.output_file,
            branch=self.branch
        )
 
        mock_get_commit_graph.return_value = self.commit_graph
        mock_generate_mermaid.return_value = self.mermaid_str

        with patch.object(sys, 'argv', ['main.py', '--vizualize', self.visualizer_path,
                                        '--repo', self.repo_path, '--output', self.output_file,
                                        '--branch', self.branch]):
            try:
                main.main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)

        mock_get_commit_graph.assert_called_once_with(self.repo_path, self.branch)
        mock_generate_mermaid.assert_called_once_with(self.commit_graph)
        mock_save_mermaid.assert_called_once_with(self.mermaid_str, self.temp_mermaid_file)
        mock_visualize_graph.assert_called_once_with(self.visualizer_path, self.temp_mermaid_file, self.output_file)
        mock_remove.assert_called_once_with(self.temp_mermaid_file)
        mock_logging.info.assert_any_call("Граф зависимостей успешно построен и сохранен.")

    @patch('main.logging')
    @patch('main.get_commit_graph', side_effect=Exception("Some error"))
    @patch('main.parse_args')
    def test_main_failure(self, mock_parse_args, mock_get_commit_graph, mock_logging):

        mock_parse_args.return_value = main.argparse.Namespace(
            vizualize=self.visualizer_path,
            repo=self.repo_path,
            output=self.output_file,
            branch=self.branch
        )

        with patch.object(sys, 'argv', ['main.py', '--vizualize', self.visualizer_path,
                                        '--repo', self.repo_path, '--output', self.output_file,
                                        '--branch', self.branch]):
            with self.assertRaises(SystemExit) as cm:
                main.main()
            self.assertEqual(cm.exception.code, 1)

        mock_logging.critical.assert_called_once()
        mock_logging.critical.assert_called_with('Ошибка выполнения: Some error', exc_info=True)

if __name__ == '__main__':
    unittest.main()
