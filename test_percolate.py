import unittest
import tempfile
import os
import json
from percolate import find_latest_files, extract_tasks_with_worklog

class TestPercolate(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = self.tempdir.name

    def tearDown(self):
        self.tempdir.cleanup()

    def create_file(self, relpath, content, mtime=None):
        fpath = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(content, f)
        if mtime:
            os.utime(fpath, (mtime, mtime))
        return fpath

    def test_find_latest_files(self):
        # Create two files with same name, different mtime
        f1 = self.create_file('a/file.json', {}, mtime=100)
        f2 = self.create_file('b/file.json', {}, mtime=200)
        files = find_latest_files(self.root)
        self.assertIn('file.json', files)
        self.assertEqual(files['file.json'], f2)

    def test_extract_tasks_with_worklog(self):
        # File with matching worklog
        data = {
            "key": "TASK-1",
            "summary": "Test summary",
            "description": "Test desc",
            "worklog": [{"email": "a@b.com"}]
        }
        f1 = self.create_file('f1.json', data)
        files = {'f1.json': f1}
        result = extract_tasks_with_worklog(files, 'a@b.com')
        self.assertIn('TASK-1', result)
        self.assertEqual(result['TASK-1']['summary'], "Test summary")

    def test_extract_tasks_with_worklog_no_match(self):
        data = {
            "key": "TASK-2",
            "summary": "No match",
            "description": "No match desc",
            "worklog": [{"email": "other@b.com"}]
        }
        f1 = self.create_file('f2.json', data)
        files = {'f2.json': f1}
        result = extract_tasks_with_worklog(files, 'a@b.com')
        self.assertNotIn('TASK-2', result)

    def test_extract_tasks_with_worklog_invalid_json(self):
        # Create a file with invalid JSON
        fpath = os.path.join(self.root, 'bad.json')
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write('{bad json}')
        files = {'bad.json': fpath}
        # Should not raise
        result = extract_tasks_with_worklog(files, 'a@b.com')
        self.assertEqual(result, {})

    def test_extract_tasks_with_worklog_missing_fields(self):
        # Missing worklog
        data = {"key": "TASK-3", "summary": "s", "description": "d"}
        f1 = self.create_file('f3.json', data)
        files = {'f3.json': f1}
        result = extract_tasks_with_worklog(files, 'a@b.com')
        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()
