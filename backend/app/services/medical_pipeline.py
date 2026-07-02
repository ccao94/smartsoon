import re
from typing import Dict, Any, List
import chromadb
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from sentence_transformers import SentenceTransformer

class PHILeakError(Exception):
    """Custom exception for residual PHI detected post-anonymization."""
    pass

class MedicalDataPipeline:
    # Whitelist pour proteger les acronymes medicaux et le token NISS des effets de bord de Presidio/spaCy
    _PROTECTED_MEDICAL_TERMS = [
        "TA", "FC", "IRM", "ITT", "AIPP", "SPO2", "GCS", "FLAIR", "T1", "T2",
        "AVC", "ECG", "EEG", "PL", "NFS", "CRP", "ALAT", "ASAT", "GGT", "PAL",
        "VGM", "TCMH", "CCMH", "PNN", "PNE", "PNB", "LYMPHO", "MONO", "PLAQ",
        "TP", "INR", "TCA", "FIB", "CREAT", "UREE", "IODE", "TDM", "TTC",
        "<NISS>"
    ]

    def __init__(self, target_liasse_id: str):
        self.liasse_id = target_liasse_id
        self.lang = "fr"
        
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": self.lang, "model_name": "fr_core_news_lg"}]
        }
        nlp_engine = SpacyNlpEngine(models=nlp_config["models"])
        nlp_engine.load()
        
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(languages=[self.lang], nlp_engine=nlp_engine)
        
        patient_pattern = Pattern(
            name="patient_name_pattern",
            regex=(
                r"(?i)(?:nom\s*/\s*pr[ée]nom|patient\s*[\(\[]?\s*e?\s*[\)\]]?|"
                r"assur[ee]\s*[\(\[]?\s*e?\s*[\)\]]?)\s*:?\s*\n?\s*"
                r"([A-ZÀ-Ý][A-Za-zà-ý\s-']{1,}(?:\s+[A-ZÀ-Ý][a-zà-ý\s-']+){1,2})"
            ),
            score=1.0
        )
        
        doctor_pattern = Pattern(
            name="doctor_name_pattern",
            regex=r"(?i)(?:Dr|Docteur|Pr|Professeur)\s+([A-ZÀ-Ý][a-zà-ý]+(?:\s+[A-ZÀ-Ý][a-zà-ý]+)*)",
            score=1.0
        )
        
        date_pattern = Pattern(name="date_pattern", regex=r"(\d{2}/\d{2}/\d{4})", score=1.0)
        
        date_letter_pattern = Pattern(
            name="date_letter_pattern",
            regex=(
                r"(\d{1,2}\s+(?:janvier|f[ée]vrier|mars|avril|mai|juin|"
                r"juillet|ao[ûu]t|septembre|octobre|novembre|d[ée]cembre)\s+\d{4})"
            ),
            score=0.95
        )
        
        phone_pattern = Pattern(name="phone_pattern", regex=r"(0[1-9]\d{2}\s?\d{2}\s?\d{2}\s?\d{2})", score=0.96)
        rpps_pattern = Pattern(name="rpps_pattern", regex=r"\b\d{11,12}\b", score=1.0)
        
        dossier_pattern = Pattern(
            name="dossier_ref_pattern",
            regex=r"([A-Z]{2,5}-\d{4}-[A-Z]{2,5}-\d{5,6})",
            score=0.90
        )

        # Utilisation d'un lookbehind positif pour eviter de supprimer la formule de politesse
        signature_pattern = Pattern(
            name="signature_pattern",
            regex=r"(?i)(?<=salutations|cordialement|respectueusement)\.?\s*\n?\s*([A-ZÀ-Ý][a-zà-ý\-]+(?:\s+[A-ZÀ-Ý][a-zà-ý\-]+)+)",
            score=0.95
        )
        
        registry.add_recognizer(PatternRecognizer(supported_entity="PATIENT", patterns=[patient_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="DOCTOR", patterns=[doctor_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="DATE_TIME", patterns=[date_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="DATE_LETTER", patterns=[date_letter_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="PHONE_NUMBER", patterns=[phone_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="RPPS", patterns=[rpps_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="DOSSIER", patterns=[dossier_pattern], supported_language=self.lang))
        registry.add_recognizer(PatternRecognizer(supported_entity="PERSON", patterns=[signature_pattern], supported_language=self.lang))
        
        self.anonymize_operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
            "ORGANIZATION": OperatorConfig("replace", {"new_value": "<ORGANIZATION>"}),
            "PATIENT": OperatorConfig("replace", {"new_value": "<PATIENT>"}),
            "DOCTOR": OperatorConfig("replace", {"new_value": "<DOCTOR>"}),
            "DATE_TIME": OperatorConfig("replace", {"new_value": "<DATE>"}),
            "DATE_LETTER": OperatorConfig("replace", {"new_value": "<DATE>"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
            "RPPS": OperatorConfig("replace", {"new_value": "<RPPS>"}),
            "DOSSIER": OperatorConfig("replace", {"new_value": "<DOSSIER>"})
        }
        
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
        self.anonymizer = AnonymizerEngine()
        
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db_storage")
        self.collection = self.chroma_client.get_or_create_collection(name=f"liasse_{self.liasse_id}")
        
        self.model = SentenceTransformer("intfloat/multilingual-e5-large")
        self.splitter = SentenceSplitter(chunk_size=512, chunk_overlap=40)

    def _sanitize_metadata(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = raw_metadata.get("document_id") or raw_metadata.get("id") or raw_metadata.get("file_name") or "unknown_doc"
        page_num = raw_metadata.get("page_number") or raw_metadata.get("page") or raw_metadata.get("num_page") or 1
        return {
            "document_id": str(doc_id),
            "page_number": int(page_num)
        }

    def _apply_medical_whitelist(self, text: str) -> tuple[str, Dict[str, str]]:
        placeholders = {}
        processed_text = text
        for idx, term in enumerate(self._PROTECTED_MEDICAL_TERMS):
            pattern = rf"\b{term}\b" if not term.startswith("<") else re.escape(term)
            if re.search(pattern, processed_text):
                placeholder = f"PROTECTEDNUM{1000 + idx}"
                placeholders[placeholder] = term
                processed_text = re.sub(pattern, placeholder, processed_text)
        return processed_text, placeholders

    def _restore_medical_whitelist(self, text: str, placeholders: Dict[str, str]) -> str:
        restored_text = text
        for placeholder, original_term in placeholders.items():
            restored_text = restored_text.replace(placeholder, original_term)
        return restored_text

    def _pre_mask_critical_phi(self, text: str) -> str:
        t = text

        # 1. Masquage du numero de Securite Sociale (NISS)
        ssn_regex = r"(?i)(?:N°\s*S[eé]curit[eé]\s*Sociale|NISS|NIR)\s*:?\s*([\d\s.,]+)"
        t = re.sub(ssn_regex, "N° Sécurité Sociale <NISS> ", t)

        # 2. Masquage des adresses dans l'en-tete
        header_addr = r"(?i)(\d{1,4}\s+[A-Za-zà-ý\s'’\-—]+?\d{5}\s+[A-Za-zà-ý\s'’\-—]+?(?=\s*(?:cedex|Référence|Objet|Nature|\n|$)))"
        t = re.sub(header_addr, "<ADRESSE>", t)

        # 3. Masquage des adresses en ligne standard
        inline_addr = (
            r"(?i)(\d{1,4}(?:\s*,\s*|\s+)(?:rue|avenue|boulevard|all[ée]e|place|route|"
            r"chemin|impasse|cours|quai|square|bd|av)\s+[A-Za-zà-ý\s'’\-—]+?\d{5}\s+[A-Za-zà-ý\s'’\-—]+?(?=\s*(?:cedex|Référence|Objet|Nature|\n|$)))"
        )
        t = re.sub(inline_addr, "<ADRESSE>", t)

        # 4. Masquage des adresses partielles ou moins structurees
        loose_addr = (
            r"(?i)(\d{1,4}(?:\s*,\s*|\s+)(?:rue|avenue|boulevard|all[ée]e|place|route|"
            r"chemin|impasse|cours|quai|square|bd|av)\s+[A-Za-zà-ý\s'’\-—]+)"
        )
        t = re.sub(loose_addr, "<ADRESSE>", t)

        return t

    def _residual_phi(self, text: str) -> None:
        patterns = {
            "NIR/NISS": r"([12]\s?\d{2}\s?\d{2}\s?\d{2,6}[\s,.]?\d{3,5}[\s,.]?\d{2,3}[\s,.]?\d{2})",
            "RPPS": r"\b\d{11,12}\b",
            "DATE_FORMAT": r"(\d{2}/\d{2}/\d{4})",
            "DATE_LETTER": r"(\d{1,2}\s+(?:janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|d[ée]cembre)\s+\d{4})",
            "DOSSIER_REF": r"([A-Z]{2,5}-\d{4}-[A-Z]{2,5}-\d{5,6})",
            "PHONE": r"(0[1-9]\d{2}\s?\d{2}\s?\d{2}\s?\d{2})",
            "POSTAL_CODE": r"\b\d{5}\b"
        }
        
        clean_check_text = text
        for operator in self.anonymize_operators.values():
            placeholder_value = operator.params.get("new_value", "")
            if placeholder_value:
                clean_check_text = clean_check_text.replace(placeholder_value, "")
        
        clean_check_text = (
            clean_check_text.replace("<ADRESSE>", "")
            .replace("<POSTAL_CODE>", "")
            .replace("<NISS>", "")
            .replace("<LOCATION>", "")
            .replace("<ORGANIZATION>", "")
            .replace("<PERSON>", "")
            .replace("<RPPS>", "")
        )

        detected_leaks = []
        for name, regex in patterns.items():
            matches = re.findall(regex, clean_check_text)
            if matches:
                detected_leaks.append(f"{name}: {matches}")
        
        context_keywords = {
            r"n[o°]\s*s[eé]cu": "<NISS>",
            r"n[o°]\s*insee": "<NISS>",
            r"adresse\s*:": "<ADRESSE>"
        }
        
        for kw, expected_placeholder in context_keywords.items():
            for match in re.finditer(kw, text, re.IGNORECASE):
                end = match.end()
                context_after = text[end:end+40]
                if expected_placeholder not in context_after and "<PERSON>" not in context_after:
                    if not any(p.params.get("new_value", "") in context_after for p in self.anonymize_operators.values()):
                        detected_leaks.append(f"Suspicious unmasked keyword context near '{text[match.start():match.start()+15]}'")

        if detected_leaks:
            raise PHILeakError(f"Fail-Closed Protection Blocked Residual PHI Leak: {', '.join(detected_leaks)}")

    def anonymize_text(self, raw_text: str) -> str:
        # 1. Pre-masquage deterministe
        pre_masked = self._pre_mask_critical_phi(raw_text)
        
        # 2. Protection de la whitelist
        protected_text, placeholders = self._apply_medical_whitelist(pre_masked)
        
        # 3. Execution de l'analyse et de l'anonymisation Presidio
        analysis_results = self.analyzer.analyze(text=protected_text, language=self.lang, score_threshold=0.85)
        anonymized = self.anonymizer.anonymize(text=protected_text, analyzer_results=analysis_results, operators=self.anonymize_operators)
        processed_text = anonymized.text
        
        # 4. Restauration de la whitelist
        final_text = self._restore_medical_whitelist(processed_text, placeholders)
        
        # 5. Verification de securite fail-closed
        self._residual_phi(final_text)
        
        return final_text

    def index_document(self, clean_text: str, raw_metadata: Dict[str, Any]) -> int:
        metadata = self._sanitize_metadata(raw_metadata)
        formatted_text = f"passage: {clean_text}"
        doc_node = Document(text=formatted_text, metadata=metadata)
        chunks = self.splitter.get_nodes_from_documents([doc_node])
        
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
        """Recherche sémantique dans ChromaDB avec isolation par document."""
        e5_query = f"query: {query}"
        query_embedding = self.model.encode(e5_query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            where={"document_id": document_id}
        )
        
        formatted_chunks = []
        if results and results["documents"] and results["documents"][0]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0] * len(documents)
            for idx in range(len(documents)):
                formatted_chunks.append({
                    "text": documents[idx],
                    "metadata": metadatas[idx],
                    "similarity_score": round(1.0 - distances[idx], 4)
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