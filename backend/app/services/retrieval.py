"""Permission-aware retrieval over tenant-scoped entities, documents and cases.

Two properties matter more than ranking quality here:
  1. **Bounded work.** Scoring the whole corpus in Python is fine for a demo and fatal at
     production rows. Candidate selection is pushed into the database (trigram on PostgreSQL) and
     capped, then BM25 re-ranks the candidate set. On small corpora the cap exceeds the corpus, so
     behaviour is identical to a full scan.
  2. **Clearance is enforced at retrieval time.** A record above the caller's clearance must never
     enter the candidate set, otherwise a summary can leak content through a citation.
"""
import math, re
from collections import Counter
from sqlalchemy.orm import Session
from ..models import Entity, Document, Case, Relationship

STOP = {"the", "a", "an", "of", "and", "or", "to", "in", "for", "on", "is", "are", "what",
        "which", "how", "why", "this", "that", "with", "from", "by", "be", "as", "at", "it"}

def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if t not in STOP and len(t) > 1]

class Retriever:
    def __init__(self, db: Session, user):
        self.db = db
        self.user = user

    def _scope(self):
        oid = self.user.organization_id
        if self.user.role == "platform_admin":
            return None
        return oid

    CANDIDATE_CAP = 500

    def _visible_classes(self) -> list[str]:
        from ..policy import CLASSIFICATION_RANK, clearance_of
        rank = clearance_of(self.user)
        return [c for c, r in CLASSIFICATION_RANK.items() if r <= rank]

    def _entities(self, q_tokens: list[str]):
        from sqlalchemy import or_
        from ..policy import scope_query
        base = scope_query(self.db.query(Entity), Entity, self.user).filter(Entity.canonical_id.is_(None))
        classes = self._visible_classes()
        base = base.filter(Entity.classification.in_(classes))
        rows, seen = [], set()

        def add(items):
            for e in items:
                if e.id not in seen:
                    seen.add(e.id)
                    rows.append(e)

        # Bounded prefilter: trigram similarity on PostgreSQL, LIKE on SQLite.
        if self.db.bind.dialect.name == "postgresql" and q_tokens:
            phrase = " ".join(q_tokens)
            cond = or_(Entity.name.op("%")(phrase),
                       *[Entity.name.ilike(f"%{t}%") for t in q_tokens[:6]])
            add(base.filter(cond).limit(self.CANDIDATE_CAP).all())
        # Top-up so a small corpus behaves exactly like a full scan, while a large one stays bounded.
        if len(rows) < self.CANDIDATE_CAP:
            add(base.order_by(Entity.name).limit(self.CANDIDATE_CAP).all())
        return rows

    def _simple(self, model, q_tokens: list[str]):
        from ..policy import scope_query
        base = scope_query(self.db.query(model), model, self.user)
        if hasattr(model, "classification"):
            base = base.filter(model.classification.in_(self._visible_classes()))
        rows = base.limit(self.CANDIDATE_CAP).all()
        if q_tokens and len(rows) == self.CANDIDATE_CAP:
            from sqlalchemy import or_
            like = or_(*[model.title.ilike(f"%{t}%") for t in q_tokens[:6]])
            rows = base.filter(like).limit(self.CANDIDATE_CAP).all()
        return rows

    def documents(self, q_tokens: list[str] | None = None):
        q_tokens = q_tokens or []
        return self._entities(q_tokens), self._simple(Document, q_tokens), self._simple(Case, q_tokens)

    def search(self, query: str, k: int = 8, min_coverage: float = 0.0) -> list[dict]:
        q_tokens = tokenize(query)
        if not q_tokens:
            return []
        ents, docs, cases = self.documents(q_tokens)
        corpus = []
        for e in ents:
            corpus.append({"kind": "entity", "id": e.id, "title": e.name,
                           "text": f"{e.name} {e.entity_type} {e.description} {e.district} {e.state}",
                           "classification": getattr(e, "classification", "INTERNAL"),
                           "organization_id": e.organization_id,
                           "synthetic": e.is_synthetic,
                           "meta": {"entity_type": e.entity_type, "district": e.district, "status": e.status}})
        for d in docs:
            corpus.append({"kind": "document", "id": d.id, "title": d.title,
                           "text": f"{d.title} {d.content_text}",
                           "classification": d.classification, "organization_id": d.organization_id,
                           "synthetic": d.is_synthetic, "meta": {"doc_type": d.doc_type}})
        for c in cases:
            corpus.append({"kind": "case", "id": c.id, "title": c.title,
                           "text": f"{c.title} {c.description}",
                           "classification": c.classification, "organization_id": c.organization_id,
                           "synthetic": True, "meta": {"status": c.status}})
        if not corpus:
            return []
        df = Counter()
        tokenized = []
        for d in corpus:
            toks = tokenize(d["text"])
            tokenized.append(toks)
            for t in set(toks):
                df[t] += 1
        N = len(corpus)
        avgdl = sum(len(t) for t in tokenized) / N or 1
        k1, b = 1.5, 0.75
        scored = []
        for d, toks in zip(corpus, tokenized):
            tf = Counter(toks)
            score = 0.0
            for qt in q_tokens:
                if tf[qt] == 0:
                    continue
                idf = math.log(1 + (N - df[qt] + 0.5) / (df[qt] + 0.5))
                denom = tf[qt] + k1 * (1 - b + b * (len(toks) / avgdl))
                score += idf * (tf[qt] * (k1 + 1)) / (denom or 1)
            # exact phrase bonus
            if len(q_tokens) > 1 and " ".join(q_tokens) in (d["text"] or "").lower():
                score *= 1.5
            if score <= 0:
                continue
            # Evidence-admission gate: a record must cover a sufficient share of the query's
            # distinct content terms to be treated as supporting evidence. This is what allows
            # the assistant to say "insufficient evidence" instead of citing weak lexical matches.
            coverage = len({q for q in q_tokens if q in tf}) / len(set(q_tokens))
            if coverage < min_coverage:
                continue
            snippet = (d["text"][:240] + "…") if len(d["text"]) > 240 else d["text"]
            scored.append({**{kk: v for kk, v in d.items() if kk != "text"},
                           "score": round(score, 3), "coverage": round(coverage, 2), "snippet": snippet.strip()})
        scored.sort(key=lambda x: -x["score"])
        return scored[:k]
