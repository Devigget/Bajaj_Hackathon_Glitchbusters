from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_text(text: str, chunk_size=800, chunk_overlap=100):
    """Split text with better parameters for insurance documents"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", ".", " ", ""],
        keep_separator=True
    )
    return splitter.split_text(text)
