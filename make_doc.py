import os
import re
import time
from pathlib import Path
from llm import LLM
from concurrent.futures import ThreadPoolExecutor, as_completed

class DocProcessor:
    def __init__(self, max_workers: int = 10, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the DocProcessor class
        
        Args:
            max_workers (int): Maximum number of concurrent workers
            max_retries (int): Maximum number of retry attempts for failed blocks
            retry_delay (float): Delay in seconds between retry attempts
        """
        # Regular expressions for matching C/C++ constructs
        self.function_pattern = re.compile(
            # Capture any preceding comments
            r'(?P<comments>(?:[ \t]*//[^\n]*\n|[ \t]*/\*(?:[^*]|\*(?!/))*\*/[ \t]*\n)*)'
            # Function signature and body
            r'(?P<return_type>[\w\*\s]+?)\s+'  # Return type
            r'(?P<name>\w+)\s*'                # Function name
            r'\((?P<params>[^)]*)\)\s*'        # Parameters
            r'(?P<body>{[^{}]*({[^{}]*}[^{}]*)*}|;)'  # Function body or declaration
        )
        
        self.struct_pattern = re.compile(
            # Capture any preceding comments
            r'(?P<comments>(?:[ \t]*//[^\n]*\n|[ \t]*/\*(?:[^*]|\*(?!/))*\*/[ \t]*\n)*)'
            # Struct definition
            r'struct\s+'                     # struct keyword
            r'(?P<name>\w+)\s*'             # struct name
            r'(?P<body>{[^{}]*({[^{}]*}[^{}]*)*})\s*;'  # struct body
        )

        self.llm = LLM()
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _extract_code_blocks(self, content: str) -> list:
        """
        Extract function and struct definitions from the content.
        
        Args:
            content (str): The file content to parse
            
        Returns:
            list: List of tuples (block_type, name, lines)
        """
        blocks = []
        
        # Extract functions
        for match in self.function_pattern.finditer(content):
            block_text = match.group('comments') + match.group(0)[len(match.group('comments')):]
            # Split into lines and remove empty lines at start/end while preserving comments
            lines = [line for line in block_text.split('\n')]
            # Remove empty lines at start and end but keep comments
            while lines and not lines[0].strip():
                lines.pop(0)
            while lines and not lines[-1].strip():
                lines.pop()
            blocks.append(('function', match.group('name'), lines))
        
        # Extract structs
        for match in self.struct_pattern.finditer(content):
            block_text = match.group('comments') + match.group(0)[len(match.group('comments')):]
            # Split into lines and remove empty lines at start/end while preserving comments
            lines = [line for line in block_text.split('\n')]
            # Remove empty lines at start and end but keep comments
            while lines and not lines[0].strip():
                lines.pop(0)
            while lines and not lines[-1].strip():
                lines.pop()
            blocks.append(('struct', match.group('name'), lines))
        
        return blocks

    def _process_block(self, block_info: tuple, block_index: int) -> tuple:
        """
        Process a single block using LLM with retry mechanism.
        
        Args:
            block_info: Tuple of (block_type, name, lines)
            block_index: Index to maintain order
            
        Returns:
            Tuple of (block_index, generated_doc)
            
        Raises:
            Exception: If all retry attempts fail
        """
        block_type, name, lines = block_info
        code_block = '\n'.join(lines)
        
        for attempt in range(self.max_retries):
            try:
                doc = self.llm.make_doc(code_block)
                return block_index, doc
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"Error processing block {block_index + 1} (attempt {attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(self.retry_delay)
                else:
                    print(f"All retry attempts failed for block {block_index + 1}: {e}")
                    raise  # Re-raise the last exception after all retries fail

    def process_file(self, input_file: Path, output_file: Path):
        """
        Process a C/C++ header file and extract code blocks.
        
        Args:
            input_file (Path): Path to the input file
            output_file (Path): Path where the processed file should be saved
        """
        # Only process .h, .hpp files
        if input_file.suffix not in ['.h', '.hpp']:
            return False
            
        print(f"Processing file: {input_file}")
        
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract code blocks
        blocks = self._extract_code_blocks(content)
        
        # Process blocks concurrently
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks and store futures with their indices
            future_to_index = {
                executor.submit(self._process_block, block, i): i 
                for i, block in enumerate(blocks)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                block_index = future_to_index[future]
                try:
                    block_index, doc = future.result()
                    results.append((block_index, doc))
                    print(f"Processing file: {input_file}, block {block_index + 1} of {len(blocks)} completed")
                except Exception as e:
                    print(f"Failed to process block {block_index + 1} after all retries: {e}")
                    return False
        
        # Sort results by block index to maintain order
        results.sort(key=lambda x: x[0])
        
        # Write results to file
        with open(output_file, 'w', encoding='utf-8') as md_file:
            for _, doc in results:
                md_file.write(doc)
                md_file.write('\n\n')
                md_file.flush()
                
        print(f"Saved documentation to: {output_file}")
        return True

    def make_doc(self, input_dir: str, output_dir: str):
        """
        Process documents from input directory and generate output in the specified output directory.
        
        Args:
            input_dir (str): Path to the input directory containing source documents
            output_dir (str): Path to the output directory where processed documents will be saved
        """
        # Convert to Path objects for easier handling
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create or open the index.md file in the output_dir
        index_file_path = output_path / 'index.md'
        with open(index_file_path, 'w', encoding='utf-8') as index_file:
            # Loop through all files in the input directory
            for file_path in input_path.rglob('*'):
                if file_path.is_file():
                    # Calculate the relative path of the file with respect to input_dir
                    relative_path = file_path.relative_to(input_path)
                    # Define the output path by combining output_dir/files with the relative path
                    output_file_path = output_path / 'files' / relative_path.with_suffix('.md')
                    
                    # Skip if the file already exists
                    if output_file_path.exists() and output_file_path.stat().st_size > 0:
                        print(f"Skipping existing file: {output_file_path}")
                        continue

                    # Create necessary directories in the output path
                    output_file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Process the file and generate documentation
                    if self.process_file(file_path, output_file_path):
                        print(f"Processed and saved: {output_file_path}")

                        # Write the filename as a header in the index.md file
                        index_file.write(f"## {file_path.stem}\n")
                        index_file.flush()
                        # List functions as links in the index.md file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        blocks = self._extract_code_blocks(content)
                        for block_type, name, _ in blocks:
                            if block_type == 'function':
                                link_path = (Path('files') / relative_path.with_suffix('.html')).as_posix()
                                index_file.write(f"- [{name}]({link_path}#{name})\n")
                        index_file.write('\n')
                        index_file.flush()
        print(f"Index file created at: {index_file_path}")
