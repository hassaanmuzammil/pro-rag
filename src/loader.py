from typing import Literal
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader

class FileLoader:
    page_delimiter = "\n<<<END_OF_PAGE>>>\n\f"
    page_annotation_template = "<<<START_OF_PAGE: {page_num}>>>\n{content}"

    def __init__(self):
        pass

    def load(self, file_path: str, mode: Literal["single", "page"]) -> list[Document]:
        if file_path.endswith(".pdf"):
            return self._load_pdf(file_path, mode)
        elif file_path.endswith(".txt"):
            return self._load_txt(file_path)
        elif file_path.endswith(".docx"):
            return self._load_docx(file_path)
        else:
            raise ValueError("Unsupported file extension.")

    def _load_pdf(
        self,
        file_path: str,
        mode: Literal["single", "page"]
    ):
        if mode == "page":
            return PyPDFLoader(file_path, mode="page", extract_images=True).load()
        
        if mode == "single":
            documents =  PyPDFLoader(
                file_path, 
                mode="single", 
                extract_images=True,
                pages_delimiter=self.page_delimiter
            ).load()

            raw_text = documents[0].page_content
            pages = raw_text.split(self.page_delimiter)

            annotated_pages = [
                self.page_annotation_template.format(page_num=i+1, content=page.strip())
                for i, page in enumerate(pages)
            ]
            documents[0].page_content = self.page_delimiter.join(annotated_pages)
            return documents
        
    def _load_txt(self, file_path: str) -> list[Document]:
        return TextLoader(file_path).load()
    
    def _load_docx(self, file_path: str) -> list[Document]:
        return Docx2txtLoader(file_path).load()
