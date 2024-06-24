import math
from textwrap import dedent
from typing import Annotated, List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field

# class DocumentEditBase(BaseModel):
#     pass

class DocumentLinesDelete(BaseModel):
    """Delete a range of lines from the file"""
    edit_type: Literal['delete']

    line_numbers: Tuple[int, int] = Field(..., description="A range of numbers to delete, inclusive. To delete a single line, put the same number twice. [0,0] will delete the first line of the file.")

class DocumentLineAdd(BaseModel):
    """
    Add a new line below the specified line number.
    This is how to add a line in the middle of the file, or to add a line to the end of the file.
    """
    edit_type: Literal['add']

    line_number: Optional[int] = Field(..., description="A new line will be added below this line number in the file. None means to add the line to the end of the file")
    new_line: str = Field(..., description="The line you want to add at the given line number")

class DocumentLineEdit(BaseModel):
    """Editing a single line from the file"""
    edit_type: Literal['edit']

    line_number: int = Field(..., description="The line number in the text file you want to replace.")
    new_line: str = Field(..., description="The line you want to replace the existing line in the file")

LineEdit = Annotated[Union[DocumentLineEdit , DocumentLineAdd , DocumentLinesDelete], Field(discriminator="edit_type")]

class DocumentEdits(BaseModel):
    """A collection of edits to be made to the file"""

    edits: List[LineEdit]

document_edits_example = dedent("""\
                                Your response should take the form of a DocumentEdits JSON object. Here is an example:   
                                {{
                                    edits: [
                                        {{
                                            edit_type: "delete",
                                            line_numbers: [5, 7]
                                        }},
                                        {{
                                            edit_type: "add",
                                            line_number: 5,
                                            new_line: "Line 6 is here, baby!"
                                        }},
                                        {{
                                            edit_type: "add",
                                            line_number: null,
                                            new_line: "This line will go at the end of the file!"
                                        }},
                                        {{
                                            edit_type: "edit",
                                            line_number: 9,
                                            new_line: "This is the new line_number. I have replaced it!"
                                        }}
                                    ]
                                }}
                                """)

def sort_document_edits(edit: LineEdit):
    if isinstance(edit, DocumentLinesDelete):
        return min(edit.line_numbers)
    if isinstance(edit, DocumentLineEdit):
        return edit.line_number
    if isinstance(edit, DocumentLineAdd):
        return edit.line_number if edit.line_number is not None else float('inf')

def edit_document(file_path: str, document_edit: DocumentEdits):
    # Read the content of the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    for edit in sorted(document_edit.edits, key=sort_document_edits, reverse=True):
        if isinstance(edit, DocumentLinesDelete):
            start, end = edit.line_numbers
            if start < 1 or end > len(lines):
                raise IndexError("Line number out of range for delete operation")
            if start == end:
                del lines[start - 1]
            else:
                del lines[start - 1:end]
        
        elif isinstance(edit, DocumentLineAdd):
            line_number = edit.line_number
            if line_number is not None and (line_number <= 0 or line_number > len(lines)):
                raise IndexError("Line number out of range for add operation")
            if line_number is None:
                lines.append(edit.new_line + "\n")
            else:
                lines.insert(line_number, edit.new_line + "\n")

        elif isinstance(edit, DocumentLineEdit):
            line_number = edit.line_number
            if line_number <= 0 or line_number > len(lines):
                raise IndexError("Line number out of range for edit operation")
            lines[line_number-1] = edit.new_line + "\n"
    
    # Write the modified content back to the file
    with open(file_path, 'w') as file:
        file.writelines(lines)


def fetch_doc_with_line_numbers(doc_path: str):
    with open(doc_path, 'r', encoding='utf-8') as fh:
        ret_str = ""
        count = 1
        for line in fh:
            ret_str += f"\n{count}: {line}"
            count = count + 1
        return ret_str