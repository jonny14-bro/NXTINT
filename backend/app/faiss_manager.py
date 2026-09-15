import json
import threading
import uuid
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np

class FaceIDManager:
    def __init__(self, similarity_threshold=0.75):
        self.face_id_counter = 0
        self.known_faces = {}  # face_id → embedding
        self.threshold = similarity_threshold

    def assign_face_id(self, embedding):
        import numpy as np

        best_id = None
        best_sim = 0.0

        for fid, emb in self.known_faces.items():
            sim = np.dot(embedding, emb)
            if sim > best_sim:
                best_sim = sim
                best_id = fid

        if best_sim >= self.threshold:
            return best_id, best_sim

        # New face
        self.face_id_counter += 1
        fid = f"FACE_{self.face_id_counter:03d}"
        self.known_faces[fid] = embedding
        return fid, 1.0


class FaissManager:
    def __init__(self, dim: int, use_hnsw: bool = True):
        self.dim = dim
        self.lock = threading.Lock()

        if use_hnsw and hasattr(faiss, "IndexHNSWFlat"):
            base = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_INNER_PRODUCT)
        else:
            base = faiss.IndexFlatL2(dim)

        self.index = faiss.IndexIDMap(base)
        self._next_idx = 1

        self.idx_to_uid = {}
        self.uid_to_idx = {}
        self.metadata = {}
        self.embeddings = {}
        self.hash_to_uid = {}
        
    def meta_count(self):
        return len(self.metadata)

    def add(self, embedding, metadata=None, file_hash=None):
        vec = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        if vec.shape[1] != self.dim:
            raise ValueError("Embedding dimension mismatch")

        with self.lock:
            idx = self._next_idx
            self._next_idx += 1
            uid = str(uuid.uuid4())

            self.index.add_with_ids(vec, np.array([idx], dtype=np.int64))
            self.idx_to_uid[idx] = uid
            self.uid_to_idx[uid] = idx
            self.metadata[uid] = metadata or {}
            self.embeddings[uid] = vec.flatten().tolist()

            if file_hash:
                self.hash_to_uid[file_hash] = uid

        return uid

    def search_by_vector(self, query, k=5):
        q = np.asarray(query, dtype=np.float32).reshape(1, -1)
        if self.index.ntotal == 0:
            return []

        D, I = self.index.search(q, k)
        return [
            (self.idx_to_uid[int(i)], float(d), self.metadata.get(self.idx_to_uid[int(i)], {}))
            for d, i in zip(D[0], I[0]) if i != -1
        ]

    def search_by_uid(self, uid, k=5):
        emb = self.embeddings.get(uid)
        if emb is None:
            raise KeyError("UID not found")
        res = self.search_by_vector(emb, k + 1)
        return [r for r in res if r[0] != uid][:k]

    def save(self, index_path, meta_path):
        with self.lock:
            faiss.write_index(self.index, index_path)
            with open(meta_path, "w") as f:
                json.dump({
                    "next_idx": self._next_idx,
                    "idx_to_uid": self.idx_to_uid,
                    "metadata": self.metadata,
                    "embeddings": self.embeddings,
                    "hash_to_uid": self.hash_to_uid,
                }, f)

    def load(self, index_path, meta_path):
        with self.lock:
            self.index = faiss.read_index(index_path)
            with open(meta_path) as f:
                data = json.load(f)

            self._next_idx = data["next_idx"]
            self.idx_to_uid = {int(k): v for k, v in data["idx_to_uid"].items()}
            self.uid_to_idx = {v: k for k, v in self.idx_to_uid.items()}
            self.metadata = data["metadata"]
            self.embeddings = data["embeddings"]
            self.hash_to_uid = data.get("hash_to_uid", {})

    def count(self):
        return self.index.ntotal


class FaceFaissManager(FaissManager):
    def __init__(self, use_hnsw=True):
        self.dim = 512
        self._meta = {}
        self.use_hnsw = use_hnsw
        self.lock = threading.Lock()

        if use_hnsw and hasattr(faiss, "IndexHNSWFlat"):
            base = faiss.IndexHNSWFlat(
                self.dim, 32, faiss.METRIC_INNER_PRODUCT
            )
        else:
            base = faiss.IndexFlatIP(self.dim)

        self.index = faiss.IndexIDMap(base)
        self._next_idx = 1

        self.idx_to_uid = {}
        self.uid_to_idx = {}
        self.metadata = {}
        self.embeddings = {}
        self.hash_to_uid = {} 
      
    def meta_count(self):
        return len(self.metadata)

    def iter_metadata(self):
        """
        Safely iterate over face metadata.
        """
        for uid, meta in self.metadata.items():
            yield uid, meta         

    def add_face(
        self,
        embedding,
        source="",
        bbox=None,
        frame=None,
        timestamp=None,
        identity=None,
        enrolled: bool = False
    ):
        vec = np.asarray(embedding, dtype=np.float32)

        norm = np.linalg.norm(vec)
        if norm == 0:
            raise ValueError("Zero-norm face embedding")
        vec = vec / norm

        meta = {
            "type": "face",
            "source": source,
            "enrolled": bool(enrolled)
        }

        if identity:
            meta["identity"] = identity
        if bbox:
            meta["bbox"] = bbox
        if frame is not None:
            meta["frame"] = frame
        if timestamp is not None:
            meta["timestamp"] = timestamp

        return self.add(vec.tolist(), meta)
