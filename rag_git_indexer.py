#!/usr/bin/env python3
import os
import json
import tempfile
import argparse
from pathlib import Path
import subprocess
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clone_repository(repo_url, temp_dir):
    """Clone a git repository to a temporary directory."""
    logger.info(f"Cloning repository {repo_url} to {temp_dir}")
    try:
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository: {e}")
        return False

def is_binary_file(file_path):
    """Check if a file is binary."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # Try to read as text
        return False
    except UnicodeDecodeError:
        return True

def should_ignore_file(file_path):
    """Check if a file should be ignored based on common patterns."""
    ignore_patterns = [
        '.git/', 'node_modules/', '__pycache__/', 'venv/', '.env/',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.mp3', '.mp4', '.avi', '.mov', '.flv', '.wmv',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.pyc', '.so', '.dll', '.exe', '.bin',
        '.lock', '.cache', '.token', '.env', '.gitignore', 'Jenkinsfile'
    ]
    
    return any(pattern in str(file_path) for pattern in ignore_patterns)

def extract_java_methods(content):
    """Extract methods from Java file content."""
    # This regex pattern tries to match Java method signatures and their bodies
    # It's a simplified approach and might not catch all edge cases
    method_pattern = r'(?:public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^)]*\) *(\{?|[^;])'
    
    methods = []
    # Find all potential method starts
    for match in re.finditer(method_pattern, content):
        start_pos = match.start()
        # Find the method body by counting braces
        if '{' in match.group():
            # Method with body
            open_braces = 1
            end_pos = match.end()
            
            while open_braces > 0 and end_pos < len(content):
                if content[end_pos] == '{':
                    open_braces += 1
                elif content[end_pos] == '}':
                    open_braces -= 1
                end_pos += 1
            
            method_content = content[start_pos:end_pos]
            method_signature = match.group().strip()
            if method_signature.endswith('{'):
                method_signature = method_signature[:-1].strip()
            
            methods.append({
                "method_signature": method_signature,
                "content": method_content
            })
    
    return methods

def process_repository(repo_dir, output_file):
    """Process all files in the repository and write to JSONL file."""
    logger.info(f"Processing repository files and writing to {output_file}")
    count = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for root, _, files in os.walk(repo_dir):
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(repo_dir)
                
                if should_ignore_file(file_path):
                    continue
                
                if is_binary_file(file_path):
                    logger.debug(f"Skipping binary file: {rel_path}")
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as code_file:
                        content = code_file.read()
                    
                    # Create a document for RAG
                    chunk = {
                        "path": str(rel_path),
                        "file_name": file,
                        "file_extension": file_path.suffix,
                        "file_size": file_path.stat().st_size,
                        "content": content,
                    }
                    
                    # Write to JSONL file
                    f.write(json.dumps(chunk) + '\n')
                    count += 1
                    
                    # Special handling for Java files
                    if file_path.suffix.lower() == '.java':
                        # Extract methods from Java file
                        methods = extract_java_methods(content)
                        
                        # Create a chunk for each method
                        for i, method in enumerate(methods):
                            method_chunk = {
                                "path": str(rel_path),
                                "file_name": file,
                                "file_extension": file_path.suffix,
                                "file_size": len(method["content"]),
                                "content": method["content"],
                                "method_signature": method["method_signature"],
                                "chunk_type": "method",
                                "method_index": i
                            }
                            
                            # Write method chunk to JSONL file
                            f.write(json.dumps(method_chunk) + '\n')
                            count += 1
                    
                    if count % 100 == 0:
                        logger.info(f"Processed {count} chunks...")
                        
                except Exception as e:
                    logger.error(f"Error processing file {rel_path}: {e}")
    
    logger.info(f"Completed processing {count} files")
    return count

def main():
    parser = argparse.ArgumentParser(description="Generate RAG dataset from Git repository")
    parser.add_argument("repo_url", help="URL of the Git repository to clone")
    parser.add_argument("--output", "-o", default="rag_dataset.jsonl", 
                        help="Output JSONL file path (default: rag_dataset.jsonl)")
    args = parser.parse_args()
    
    # Create a temporary directory for the repository
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Created temporary directory: {temp_dir}")
        
        # Clone the repository
        if not clone_repository(args.repo_url, temp_dir):
            logger.error("Failed to clone repository. Exiting.")
            return 1
        
        # Process the repository and create the JSONL file
        file_count = process_repository(temp_dir, args.output)
        
        logger.info(f"Successfully created RAG dataset with {file_count} files at {args.output}")
    
    logger.info("Temporary directory cleaned up")
    return 0


if __name__ == "__main__":
    exit(main())
