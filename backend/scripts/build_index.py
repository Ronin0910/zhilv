"""构建向量索引 — 运行一次即可"""

import sys
import time
from pathlib import Path

# 把 backend/ 加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.document_loader import document_loader
from app.services.vector_store import vector_store_service


def main():
    print("=" * 50)
    print("开始构建向量索引")
    print("=" * 50)

    start = time.time()

    # 1. 初始化 VectorStore
    vector_store_service.get_store()

    # 2. 加载并分块文档
    root_dir = Path(__file__).parent.parent
    knowledge_dir = root_dir / "knowledge"
    chunks = document_loader.load_directory(str(knowledge_dir))

    if not chunks:
        print("⚠️ 没有找到任何文档，请检查 knowledge/ 目录")
        return

    # 3. 批量上传到 Pinecone（每批 100 个）
    batch_size = 100
    total = len(chunks)
    for i in range(0, total, batch_size):
        batch = chunks[i:i + batch_size]
        vector_store_service.add_documents(batch)
        print(f"  进度: {min(i + batch_size, total)}/{total}")

    elapsed = time.time() - start

    # 4. 输出统计
    stats = vector_store_service.get_index_stats()
    print(f"\n{'=' * 50}")
    print(f"索引构建完成!")
    print(f"  文档片段数: {total}")
    print(f"  Pinecone 向量总数: {stats['total_vectors']}")
    print(f"  耗时: {elapsed:.1f} 秒")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()