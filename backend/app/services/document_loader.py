"""文档加载与预处理"""
from pathlib import Path
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings


class DocumentLoader():

    def __init__(self):
        self.settings = get_settings()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.rag_chunk_size,
            chunk_overlap=self.settings.rag_chunk_overlap,
            separators=["\n\n", "\n", "。", ". ", " ", ""]
        )

    def load_directory(self, dir_path: str = None) -> list[Document]:
        """
        扫描目录下所有的文档，加载并分块

        Args:
            dir_path: 文档目录路径

        Returns:
            分块后的Document列表
        """
        if dir_path is None:
            dir_path = self.settings.knowledge_dir
        dir_path = Path(dir_path)
        if not dir_path.exists():
            raise FileNotFoundError(f"知识库目录不存在: {dir_path}")

        all_docs = []
        for file_path in dir_path.glob("*"):
            if file_path.is_dir():
                continue
            docs = self._load_file(file_path)
            all_docs.extend(docs)

        # 分块
        chunks = self.splitter.split_documents(all_docs)
        return chunks

    def _load_file(self, file_path: Path) -> list[Document]:
        """根据文件扩展名选择加载方式"""
        suffix = file_path.suffix.lower()

        if suffix == ".md":
            return self._load_markdown(file_path)
        elif suffix == ".txt":
            return self._load_text(file_path)
        elif suffix == ".pdf":
            return self._load_pdf(file_path)
        else:
            print(f" 跳过不支持的文件类型: {file_path.name}")
            return []

    def _load_markdown(self, file_path: Path) -> list[Document]:
        text = file_path.read_text(encoding="utf-8")
        return [Document(
            page_content=text,
            metadata={"sourse": file_path.name, "type": "markdown"}
        )]

    def _load_text(self, file_path: Path) -> list[Document]:
        text = file_path.read_text(encoding="utf-8")
        return [Document(
            page_content=text,
            metadata={"sourse": file_path.name, "type": "text"}
        )]

    def _load_pdf(self, file_path: Path) -> list[Document]:
        reader = PdfReader(str(file_path))  #解析pdf
        docs = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()   #提取文字，得到字符串
            if text.strip():
                docs.append(Document(
                    page_content=text,
                    metadata={"sourse": file_path.name, "type": "pdf", "page": i + 1}
                ))
        return docs

#全局唯一实例
document_loader = DocumentLoader()