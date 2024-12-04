import argparse
from make_doc import DocProcessor
import os


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Document processing tool')
    parser.add_argument('--input-dir', help='Input directory containing source documents')
    parser.add_argument('--output-dir', help='Output directory for processed documents')
    
    # Parse arguments
    args = parser.parse_args()
   
    if not args.input_dir or not args.output_dir:
        parser.error("--input-dir and --output-dir are required")
    # Create processor instance and process documents
    processor = DocProcessor()
    processor.make_doc(args.input_dir, args.output_dir)

if __name__ == '__main__':
    main()