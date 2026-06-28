import os
import re
from typing import Dict, Any
import chromadb
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from sentence_transformers import SentenceTransformer

class MedicalDataPipeline:
    def __init__(self, target_liasse_id: str):
        self.liasse_id = target_liasse_id
        self.lang = "fr"
        
        # spacy nlp engine setup
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": self.lang, "model_name": "fr_core_news_lg"}]
        }
        nlp_engine = SpacyNlpEngine(models=nlp_config["models"])
        nlp_engine.load()
        
        # presidio analyzer registry
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(languages=[self.lang], nlp_engine=nlp_engine)
        
        # custom medical regex patterns
        patient_pattern = Pattern(name="patient_name_pattern", regex=r"(?i)(?:nom\s*/\s*prénom|patient|assurée)\s*:?\s*([A-ZÀ-Ý][A-ZÀ-Ý\s-]+)", score=1.0)
        doctor_pattern = Pattern(name="doctor_name_pattern", regex=r"(?i)(?:Dr|Docteur)\s+([A-ZÀ-Ý][a-zà-ý]+(?:\s+[A-ZÀ-Ý][a-zà-ý]+)*)", score=1.0)
        date_pattern = Pattern(name="date_pattern", regex=r"(\d{2}/\d{2}/\d{4})", score=1.0)
        phone_pattern = Pattern(name="phone_pattern", regex=r"(0[1-9]\d{2}\s?\d{2}\s?\d{2}\s?\d{2})", score=0.96)
        ssn_pattern = Pattern(name="ssn_pattern", regex=r"([12]\s?\d{2}\s?\d{2}\s?\d{2,6}[\s,.]?\d{3,5}[\s,.]?\d{2,3}[\s,.]?\d{2})", score=1.0)
        rpps_pattern = Pattern(name="rpps_pattern", regex=r"(?:RPPS\s*)(\d{11,12})", score=1.0)
        
        registry.add_recognizer(PatternRecognizer(supported_entity="PATIENT", patterns=[patient_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="DOCTOR", patterns=[doctor_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="DATE_TIME", patterns=[date_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="PHONE_NUMBER", patterns=[phone_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="NISS", patterns=[ssn_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="RPPS", patterns=[rpps_pattern], supported_language=self.lang))
        
        self.anonymize_operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
            "PATIENT": OperatorConfig("replace", {"new_value": "<PATIENT>"}),
            "DOCTOR": OperatorConfig("replace", {"new_value": "<DOCTOR>"}),
            "DATE_TIME": OperatorConfig("replace", {"new_value": "<DATE>"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
            "NISS": OperatorConfig("replace", {"new_value": "<NISS>"}),
            "RPPS": OperatorConfig("replace", {"new_value": "<RPPS>"})
        }
        
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
        self.anonymizer = AnonymizerEngine()
        
        # database persistence config
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db_storage")
        self.collection = self.chroma_client.get_or_create_collection(name=f"liasse_{self.liasse_id}")
        
        # local embedding model loading
        self.model = SentenceTransformer("intfloat/multilingual-e5-large")
        self.splitter = SentenceSplitter(chunk_size=512, chunk_overlap=40)

    def _sanitize_metadata(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = raw_metadata.get("document_id") or raw_metadata.get("id") or raw_metadata.get("file_name") or "unknown_doc"
        page_num = raw_metadata.get("page_number") or raw_metadata.get("page") or raw_metadata.get("num_page") or 1
        return {
            "document_id": str(doc_id),
            "page_number": int(page_num)
        }

    def anonymize_text(self, raw_text: str) -> str:
        analysis_results = self.analyzer.analyze(text=raw_text, language=self.lang, score_threshold=0.60)
        anonymized = self.anonymizer.anonymize(text=raw_text, analyzer_results=analysis_results, operators=self.anonymize_operators)
        return anonymized.text

    def index_document(self, clean_text: str, raw_metadata: Dict[str, Any]) -> int:
        metadata = self._sanitize_metadata(raw_metadata)
        
        # e5 prefix injection as agreed with igor g
        formatted_text = f"passage: {clean_text}"
        
        doc_node = Document(text=formatted_text, metadata=metadata)
        chunks = self.splitter.get_nodes_from_documents([doc_node])
        
        # vector generation and database insertion loop
        for idx, chunk in enumerate(chunks):
            embedding = self.model.encode(chunk.text).tolist()
            
            self.collection.add(
                documents=[chunk.text],
                embeddings=[embedding],
                metadatas=[chunk.metadata],
                ids=[f"chk_{self.liasse_id}_{metadata['document_id']}_{idx}"]
            )
        return len(chunks)
    
    def search(self, query: str, document_id: str, n: int = 5) -> list[dict]:
        """
        Search for relevant chunks using multilingual-e5-large embeddings.
        Enforces strict document boundary isolation audit (T1).
        """
        # 1. Format query with the mandatory E5 prefix
        e5_query = f"query: {query}"
        
        # 2. Generate embedding vector using the correct variable 'self.model'
        query_embedding = self.model.encode(e5_query).tolist()
        
        # 3. Query the client collection applying the strict filter rule from Robin
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            where={"document_id": document_id}
        )
        
        formatted_chunks = []
        
        # 4. Map distance vectors to similarity metrics
        if results and results["documents"] and results["documents"][0]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0] * len(documents)
            
            for idx in range(len(documents)):
                similarity_score = 1.0 - distances[idx]
                
                formatted_chunks.append({
                    "text": documents[idx],
                    "metadata": metadatas[idx],
                    "similarity_score": round(similarity_score, 4)
                })
                
        return formatted_chunks

def process_document(pipeline: MedicalDataPipeline, raw_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    clean_text = pipeline.anonymize_text(raw_text)
    chunks_count = pipeline.index_document(clean_text, metadata)
    clean_metadata = pipeline._sanitize_metadata(metadata)
    
    return {
        "original": raw_text,
        "anonymized": clean_text,
        "chunks": chunks_count,
        "document_id": clean_metadata["document_id"]
    }