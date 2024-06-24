import unittest
import tempfile
import os
from typing import List, Optional, Tuple
from crews.document_edits import DocumentEdits, DocumentLineEdit, DocumentLinesAdd, DocumentLinesDelete, edit_document
from pydantic import BaseModel, Field

# Assuming the classes and edit_document function are in a module named document_editor

class TestEditDocument(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary file to test with
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(b"Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        self.test_file.close()

    def tearDown(self):
        # Clean up the temporary file
        os.remove(self.test_file.name)

    def test_delete_single_line(self):
        edits = DocumentEdits(edits=[DocumentLinesDelete(line_numbers=(1, 1))])
        edit_document(self.test_file.name, edits)
        with open(self.test_file.name, 'r') as file:
            content = file.readlines()
        self.assertEqual(content, ["Line 2\n", "Line 3\n", "Line 4\n", "Line 5\n"])

    def test_delete_range_of_lines(self):
        edits = DocumentEdits(edits=[DocumentLinesDelete(line_numbers=(1, 3))])
        edit_document(self.test_file.name, edits)
        with open(self.test_file.name, 'r') as file:
            content = file.readlines()
        self.assertEqual(content, ["Line 4\n", "Line 5\n"])

    def test_add_line_in_middle(self):
        edits = DocumentEdits(edits=[DocumentLinesAdd(line_number=2, new_line="New Line")])
        edit_document(self.test_file.name, edits)
        with open(self.test_file.name, 'r') as file:
            content = file.readlines()
        self.assertEqual(content, ["Line 1\n", "Line 2\n", "New Line\n", "Line 3\n", "Line 4\n", "Line 5\n"])

    def test_add_line_at_end(self):
        edits = DocumentEdits(edits=[DocumentLinesAdd(line_number=None, new_line="New Line at End")])
        edit_document(self.test_file.name, edits)
        with open(self.test_file.name, 'r') as file:
            content = file.readlines()
        self.assertEqual(content, ["Line 1\n", "Line 2\n", "Line 3\n", "Line 4\n", "Line 5\n", "New Line at End\n"])

    def test_edit_single_line(self):
        edits = DocumentEdits(edits=[DocumentLineEdit(line_number=2, new_line="Edited Line 2")])
        edit_document(self.test_file.name, edits)
        with open(self.test_file.name, 'r') as file:
            content = file.readlines()
        self.assertEqual(content, ["Line 1\n", "Edited Line 2\n", "Line 3\n", "Line 4\n", "Line 5\n"])

    def test_combined_edits(self):
        edits = DocumentEdits(edits=[
            DocumentLinesDelete(line_numbers=(1, 1)),
            DocumentLinesAdd(line_number=2, new_line="Inserted Line"),
            DocumentLineEdit(line_number=3, new_line="Edited Line 3")
        ])
        edit_document(self.test_file.name, edits)
        with open(self.test_file.name, 'r') as file:
            content = file.readlines()
        self.assertEqual(content, ["Line 2\n", "Inserted Line\n", "Edited Line 3\n", "Line 4\n", "Line 5\n"])

    def test_invalid_line_number_for_delete(self):
        edits = DocumentEdits(edits=[DocumentLinesDelete(line_numbers=(10, 10))])
        with self.assertRaises(IndexError):
            edit_document(self.test_file.name, edits)

    def test_invalid_line_number_for_add(self):
        edits = DocumentEdits(edits=[DocumentLinesAdd(line_number=10, new_line="Invalid Line\n")])
        with self.assertRaises(IndexError):
            edit_document(self.test_file.name, edits)

    def test_invalid_line_number_for_edit(self):
        edits = DocumentEdits(edits=[DocumentLineEdit(line_number=10, new_line="Invalid Edit\n")])
        with self.assertRaises(IndexError):
            edit_document(self.test_file.name, edits)

if __name__ == '__main__':
    unittest.main()
