
import hashlib
import re
import unicodedata

from datetime import datetime, timezone
from uuid import uuid4

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from pipeline.egypt_media_vault.config.settings import get_settings
from pipeline.egypt_media_vault.domain.article import Article
from pipeline.egypt_media_vault.domain.story_cluster import StoryCluster


class StoryClusterer:
    """
    Groups articles that discuss the same specific news story.

    Matching considers:
    - Semantic similarity between titles.
    - Semantic similarity between article context.
    - Important keyword overlap.
    - Publication time compatibility.
    - Average similarity with existing cluster members.

    The matching strategy prioritizes precision over broad event-level
    grouping to avoid merging different stories about the same event.
    """

    DEFAULT_MODEL_NAME = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    MAX_CONTEXT_LENGTH = 1200
    MAX_STORY_AGE_DAYS = 7

    TITLE_WEIGHT = 0.55
    CONTEXT_WEIGHT = 0.45

    # More conservative matching thresholds.
    MIN_TITLE_SIMILARITY = 0.50
    MIN_KEYWORD_OVERLAP = 0.12
    MIN_CONTEXT_SIMILARITY = 0.75

    ARABIC_STOP_WORDS = {
        "في", "من", "علي", "الي", "عن", "مع",
        "هذا", "هذه", "ذلك", "تلك", "هو", "هي",
        "كان", "كانت", "يكون", "تم", "قد", "ما",
        "لم", "لن", "لا", "ان", "او",
        "و", "ثم", "بعد", "قبل", "بين", "حتي",
        "كما", "حيث", "الذي", "التي", "الذين",
        "اليوم", "امس", "غدا", "جدا",
    }

    def __init__(
        self,
        similarity_threshold: float | None = None,
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:

        settings = get_settings()

        self.similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.story_similarity_threshold
        )

        if not 0.0 <= self.similarity_threshold <= 1.0:
            raise ValueError(
                "Similarity threshold must be between 0.0 and 1.0."
            )

        self.model_name = model_name
        self.model = SentenceTransformer(self.model_name)

    # --------------------------------------------------
    # ARTICLE IDENTIFICATION
    # --------------------------------------------------

    @staticmethod
    def _get_article_id(article: Article) -> str:

        if article.canonical_url_hash:
            return article.canonical_url_hash

        canonical_url = article.effective_canonical_url.strip()

        return hashlib.sha256(
            canonical_url.encode("utf-8")
        ).hexdigest()

    # --------------------------------------------------
    # ARABIC TEXT NORMALIZATION
    # --------------------------------------------------

    @staticmethod
    def _normalize_arabic_text(text: str) -> str:

        if not text:
            return ""

        text = unicodedata.normalize("NFKC", text)

        text = re.sub(
            r"[\u064B-\u065F\u0670]",
            "",
            text,
        )

        text = text.replace("ـ", "")

        text = re.sub(
            r"[إأآٱ]",
            "ا",
            text,
        )

        text = text.replace("ى", "ي")
        text = text.replace("ی", "ي")
        text = text.replace("ک", "ك")

        text = re.sub(
            r"[^\w\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip().casefold()

    # --------------------------------------------------
    # KEYWORD EXTRACTION
    # --------------------------------------------------

    @classmethod
    def _extract_keywords(cls, text: str) -> set[str]:

        normalized_text = cls._normalize_arabic_text(text)

        words = re.findall(
            r"\w+",
            normalized_text,
        )

        keywords = set()

        for word in words:

            if word.startswith("و") and len(word) > 3:
                word = word[1:]

            if word.startswith("ف") and len(word) > 3:
                word = word[1:]

            if (
                len(word) > 2
                and word not in cls.ARABIC_STOP_WORDS
            ):
                keywords.add(word)

        return keywords

    @classmethod
    def _calculate_keyword_overlap(
        cls,
        text_a: str,
        text_b: str,
    ) -> float:

        keywords_a = cls._extract_keywords(text_a)
        keywords_b = cls._extract_keywords(text_b)

        if not keywords_a or not keywords_b:
            return 0.0

        intersection = keywords_a.intersection(keywords_b)
        union = keywords_a.union(keywords_b)

        return len(intersection) / len(union)

    # --------------------------------------------------
    # ARTICLE CONTEXT
    # --------------------------------------------------

    @classmethod
    def _build_context(cls, article: Article) -> str:

        parts = []

        if article.description:
            parts.append(article.description)

        if article.content:
            parts.append(
                article.content[:cls.MAX_CONTEXT_LENGTH]
            )

        return " ".join(parts).strip()

    @classmethod
    def _build_matching_text(cls, article: Article) -> str:

        parts = [
            article.title,
            article.description or "",
            (article.content or "")[:cls.MAX_CONTEXT_LENGTH],
        ]

        return " ".join(
            part.strip()
            for part in parts
            if part and part.strip()
        )

    # --------------------------------------------------
    # SEMANTIC SIMILARITY
    # --------------------------------------------------

    def _encode_texts(self, texts: list[str]):

        if not texts:
            return []

        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def calculate_similarity_matrix(
        self,
        titles: list[str],
    ):

        if not titles:
            return []

        embeddings = self._encode_texts(titles)

        return cosine_similarity(embeddings)

    def _calculate_article_similarities(
        self,
        articles: list[Article],
    ):

        titles = [
            article.title
            for article in articles
        ]

        contexts = [
            self._build_context(article)
            for article in articles
        ]

        title_embeddings = self._encode_texts(titles)

        title_matrix = cosine_similarity(
            title_embeddings
        )

        context_matrix = None

        context_indices = [
            index
            for index, context in enumerate(contexts)
            if context
        ]

        if context_indices:

            available_contexts = [
                contexts[index]
                for index in context_indices
            ]

            context_embeddings = self._encode_texts(
                available_contexts
            )

            available_matrix = cosine_similarity(
                context_embeddings
            )

            context_matrix = {}

            for row, article_i in enumerate(context_indices):

                for column, article_j in enumerate(context_indices):

                    context_matrix[
                        (article_i, article_j)
                    ] = float(
                        available_matrix[row, column]
                    )

        return title_matrix, context_matrix

    # --------------------------------------------------
    # TIME COMPATIBILITY
    # --------------------------------------------------

    @classmethod
    def _is_time_compatible(
        cls,
        article_a: Article,
        article_b: Article,
    ) -> bool:

        date_a = article_a.publication_date
        date_b = article_b.publication_date

        if not isinstance(date_a, datetime):
            return True

        if not isinstance(date_b, datetime):
            return True

        if (
            (date_a.tzinfo is None)
            != (date_b.tzinfo is None)
        ):
            return True

        time_difference = abs(
            (date_a - date_b).total_seconds()
        )

        maximum_seconds = (
            cls.MAX_STORY_AGE_DAYS * 24 * 60 * 60
        )

        return time_difference <= maximum_seconds

    # --------------------------------------------------
    # PAIR DIAGNOSTICS
    # --------------------------------------------------

    def analyze_pair(
        self,
        article_a: Article,
        article_b: Article,
        title_similarity: float,
        context_similarity: float | None,
    ) -> dict:

        keyword_similarity = self._calculate_keyword_overlap(
            self._build_matching_text(article_a),
            self._build_matching_text(article_b),
        )

        time_compatible = self._is_time_compatible(
            article_a,
            article_b,
        )

        title_passed = (
            title_similarity >= self.MIN_TITLE_SIMILARITY
        )

        keyword_passed = (
            keyword_similarity >= self.MIN_KEYWORD_OVERLAP
        )

        context_passed = (
            context_similarity is not None
            and context_similarity >= self.MIN_CONTEXT_SIMILARITY
        )

        evidence_passed = (
            keyword_passed or context_passed
        )

        if not time_compatible:
            decision = "TIME_INCOMPATIBLE"
            eligible = False

        elif not title_passed:
            decision = "TITLE_SIMILARITY_TOO_LOW"
            eligible = False

        elif not evidence_passed:
            decision = "INSUFFICIENT_KEYWORD_AND_CONTEXT_EVIDENCE"
            eligible = False

        else:
            decision = "ELIGIBLE_FOR_FINAL_SCORING"
            eligible = True

        if context_similarity is not None:

            final_score = (
                self.TITLE_WEIGHT * title_similarity
                + self.CONTEXT_WEIGHT * context_similarity
            )

        else:

            final_score = title_similarity

        final_score = max(
            0.0,
            min(1.0, final_score),
        )

        if not eligible:
            final_score = 0.0

        matches_threshold = (
            eligible
            and final_score >= self.similarity_threshold
        )

        if eligible and matches_threshold:
            decision = "MATCH"

        elif eligible:
            decision = "FINAL_SCORE_BELOW_THRESHOLD"

        return {
            "title_similarity": float(title_similarity),
            "context_similarity": (
                float(context_similarity)
                if context_similarity is not None
                else None
            ),
            "keyword_similarity": float(keyword_similarity),
            "time_compatible": time_compatible,
            "title_gate_passed": title_passed,
            "keyword_gate_passed": keyword_passed,
            "context_gate_passed": context_passed,
            "evidence_gate_passed": evidence_passed,
            "eligible": eligible,
            "final_score": final_score,
            "matches_threshold": matches_threshold,
            "decision": decision,
        }

    # --------------------------------------------------
    # PAIR MATCHING
    # --------------------------------------------------

    def _calculate_pair_score(
        self,
        article_a: Article,
        article_b: Article,
        title_matrix,
        context_matrix,
        index_a: int,
        index_b: int,
    ) -> float:

        title_similarity = float(
            title_matrix[index_a, index_b]
        )

        context_similarity = None

        if context_matrix is not None:

            context_similarity = context_matrix.get(
                (index_a, index_b)
            )

        diagnostics = self.analyze_pair(
            article_a=article_a,
            article_b=article_b,
            title_similarity=title_similarity,
            context_similarity=context_similarity,
        )

        return diagnostics["final_score"]

    # --------------------------------------------------
    # CLUSTER SCORING
    # --------------------------------------------------

    @staticmethod
    def _calculate_cluster_score(
        member_scores: list[float],
    ) -> float:
        """
        Calculate average similarity between the new article
        and all existing members of a cluster.

        This avoids single-link matching where one similar
        article can pull an unrelated article into a cluster.
        """

        if not member_scores:
            return 0.0

        return sum(member_scores) / len(member_scores)

    # --------------------------------------------------
    # CLUSTER CREATION
    # --------------------------------------------------

    def _create_cluster(
        self,
        article: Article,
    ) -> StoryCluster:

        now = datetime.now(timezone.utc)

        cluster = StoryCluster(
            cluster_id=f"story_{uuid4().hex}",
            representative_title=article.title,
            articles=[
                self._get_article_id(article)
            ],
            created_at=now,
            updated_at=now,
            similarity_threshold=self.similarity_threshold,
        )

        article.story_cluster_id = cluster.cluster_id

        return cluster

    # --------------------------------------------------
    # MAIN CLUSTERING
    # --------------------------------------------------

    def cluster(
        self,
        articles: list[Article],
    ) -> list[StoryCluster]:

        if not articles:
            return []

        titles = [
            article.title.strip()
            for article in articles
        ]

        if any(not title for title in titles):
            raise ValueError(
                "All articles must have a non-empty title."
            )

        title_matrix, context_matrix = (
            self._calculate_article_similarities(articles)
        )

        clusters: list[StoryCluster] = []

        cluster_member_indices: list[list[int]] = []

        for article_index, article in enumerate(articles):

            best_cluster_index = None
            best_score = -1.0

            for cluster_index, member_indices in enumerate(
                cluster_member_indices
            ):

                member_scores = []

                for member_index in member_indices:

                    score = self._calculate_pair_score(
                        article,
                        articles[member_index],
                        title_matrix,
                        context_matrix,
                        article_index,
                        member_index,
                    )

                    member_scores.append(score)

                cluster_score = self._calculate_cluster_score(
                    member_scores
                )

                if cluster_score > best_score:

                    best_score = cluster_score
                    best_cluster_index = cluster_index

            if (
                best_cluster_index is not None
                and best_score >= self.similarity_threshold
            ):

                selected_cluster = clusters[
                    best_cluster_index
                ]

                selected_cluster.add_article(
                    self._get_article_id(article)
                )

                selected_cluster.updated_at = datetime.now(
                    timezone.utc
                )

                cluster_member_indices[
                    best_cluster_index
                ].append(article_index)

                article.story_cluster_id = (
                    selected_cluster.cluster_id
                )

            else:

                new_cluster = self._create_cluster(article)

                clusters.append(new_cluster)

                cluster_member_indices.append(
                    [article_index]
                )

        return clusters
