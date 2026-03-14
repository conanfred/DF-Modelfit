# Recommandation de modèles IA par profession — DF AI Research
"""
Associe chaque métier à des critères de sélection de modèles LLM :
priorités (qualité, vitesse, contexte), cas d'usage, taille max,
contexte min, et explications personnalisées.
"""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Profession:
    id: str
    icon: str
    name_fr: str
    name_en: str
    desc_fr: str
    desc_en: str
    use_cases: list[str]
    keywords: list[str]
    min_context: int = 8192
    max_params_b: float | None = None
    prefer_vision: bool = False
    prefer_code: bool = False
    prefer_speed: bool = False
    prefer_quality: bool = False
    prefer_long_context: bool = False
    weight_quality: float = 0.3
    weight_speed: float = 0.25
    weight_fit: float = 0.25
    weight_context: float = 0.2
    tips_fr: list[str] = field(default_factory=list)
    tips_en: list[str] = field(default_factory=list)


PROFESSIONS: list[Profession] = [
    Profession(
        id="developer",
        icon="💻",
        name_fr="Développeur / Programmeur",
        name_en="Developer / Programmer",
        desc_fr="Code, debugging, revue de code, documentation technique, scripts",
        desc_en="Code, debugging, code review, technical documentation, scripts",
        use_cases=["code", "coder", "instruct"],
        keywords=["code", "coder", "starcoder", "deepseek-coder", "codellama",
                   "phi", "qwen2.5-coder"],
        min_context=16384,
        prefer_code=True,
        prefer_quality=True,
        weight_quality=0.4,
        weight_speed=0.25,
        weight_fit=0.2,
        weight_context=0.15,
        tips_fr=[
            "Privilégiez les modèles « Coder » ou « Instruct » pour de meilleurs résultats en code.",
            "Un contexte long (≥ 32K) permet d'analyser des fichiers entiers.",
            "Temperature basse (0.2–0.4) pour du code plus déterministe.",
        ],
        tips_en=[
            "Prefer 'Coder' or 'Instruct' models for better coding results.",
            "Long context (≥ 32K) allows analyzing entire files.",
            "Low temperature (0.2–0.4) for more deterministic code.",
        ],
    ),
    Profession(
        id="designer",
        icon="🎨",
        name_fr="Designer / Graphiste",
        name_en="Designer / Graphic Artist",
        desc_fr="Prompts créatifs, descriptions visuelles, brainstorming, UX writing",
        desc_en="Creative prompts, visual descriptions, brainstorming, UX writing",
        use_cases=["chat", "text-generation", "image"],
        keywords=["instruct", "chat", "creative"],
        prefer_vision=True,
        prefer_quality=True,
        weight_quality=0.35,
        weight_speed=0.2,
        weight_fit=0.25,
        weight_context=0.2,
        tips_fr=[
            "Les modèles vision (LLaVA, Llama 3.2 Vision) peuvent analyser vos maquettes.",
            "Temperature élevée (0.8–1.2) pour plus de créativité.",
            "Utilisez des modèles instruct pour le UX writing.",
        ],
        tips_en=[
            "Vision models (LLaVA, Llama 3.2 Vision) can analyze your mockups.",
            "High temperature (0.8–1.2) for more creativity.",
            "Use instruct models for UX writing.",
        ],
    ),
    Profession(
        id="writer",
        icon="✍️",
        name_fr="Rédacteur / Écrivain",
        name_en="Writer / Author",
        desc_fr="Rédaction, correction, reformulation, traduction, storytelling",
        desc_en="Writing, editing, rephrasing, translation, storytelling",
        use_cases=["chat", "text-generation", "summarization", "translation"],
        keywords=["instruct", "chat"],
        min_context=32768,
        prefer_long_context=True,
        prefer_quality=True,
        weight_quality=0.4,
        weight_speed=0.15,
        weight_fit=0.2,
        weight_context=0.25,
        tips_fr=[
            "Un contexte long (≥ 32K) est essentiel pour travailler sur des chapitres entiers.",
            "Les modèles 14B+ offrent une meilleure qualité de prose.",
            "Variez la temperature selon le besoin : basse pour corriger, haute pour créer.",
        ],
        tips_en=[
            "Long context (≥ 32K) is essential for working on entire chapters.",
            "14B+ models offer better prose quality.",
            "Vary temperature by need: low for editing, high for creating.",
        ],
    ),
    Profession(
        id="researcher",
        icon="🔬",
        name_fr="Chercheur / Scientifique",
        name_en="Researcher / Scientist",
        desc_fr="Analyse de papiers, résumés scientifiques, exploration de données, hypothèses",
        desc_en="Paper analysis, scientific summaries, data exploration, hypotheses",
        use_cases=["reasoning", "chat", "summarization", "question-answering"],
        keywords=["instruct", "reasoning", "deepseek", "qwen"],
        min_context=32768,
        prefer_quality=True,
        prefer_long_context=True,
        weight_quality=0.45,
        weight_speed=0.1,
        weight_fit=0.2,
        weight_context=0.25,
        tips_fr=[
            "Les modèles « reasoning » (DeepSeek-R1, Qwen) sont optimisés pour l'analyse.",
            "Contexte long obligatoire pour ingérer des papiers complets.",
            "Temperature basse (0.1–0.3) pour des réponses factuelles.",
        ],
        tips_en=[
            "'Reasoning' models (DeepSeek-R1, Qwen) are optimized for analysis.",
            "Long context required to ingest full papers.",
            "Low temperature (0.1–0.3) for factual answers.",
        ],
    ),
    Profession(
        id="student",
        icon="🎓",
        name_fr="Étudiant",
        name_en="Student",
        desc_fr="Apprentissage, exercices, explications, résumés de cours, révisions",
        desc_en="Learning, exercises, explanations, course summaries, review",
        use_cases=["chat", "instruct", "question-answering"],
        keywords=["instruct", "chat", "llama", "gemma", "phi"],
        max_params_b=8,
        prefer_speed=True,
        weight_quality=0.25,
        weight_speed=0.35,
        weight_fit=0.25,
        weight_context=0.15,
        tips_fr=[
            "Les petits modèles (3B–7B) sont rapides et suffisants pour l'apprentissage.",
            "Phi-3.5 et Gemma 2 sont excellents pour les explications.",
            "Utilisez le mode chat pour un dialogue pédagogique interactif.",
        ],
        tips_en=[
            "Small models (3B–7B) are fast and sufficient for learning.",
            "Phi-3.5 and Gemma 2 are excellent for explanations.",
            "Use chat mode for interactive pedagogical dialogue.",
        ],
    ),
    Profession(
        id="datascientist",
        icon="📊",
        name_fr="Data Scientist / Analyste",
        name_en="Data Scientist / Analyst",
        desc_fr="Analyse de données, SQL, Python, visualisation, machine learning",
        desc_en="Data analysis, SQL, Python, visualization, machine learning",
        use_cases=["code", "reasoning", "chat"],
        keywords=["code", "coder", "instruct", "deepseek", "qwen"],
        min_context=16384,
        prefer_code=True,
        prefer_quality=True,
        weight_quality=0.35,
        weight_speed=0.2,
        weight_fit=0.2,
        weight_context=0.25,
        tips_fr=[
            "Les modèles Coder excellent pour Python, SQL et scripts d'analyse.",
            "Contexte long pour analyser des datasets ou notebooks entiers.",
            "Combinez un modèle code + un modèle reasoning pour l'interprétation.",
        ],
        tips_en=[
            "Coder models excel at Python, SQL, and analysis scripts.",
            "Long context for analyzing entire datasets or notebooks.",
            "Combine a code model + a reasoning model for interpretation.",
        ],
    ),
    Profession(
        id="sysadmin",
        icon="🖥️",
        name_fr="Admin Système / DevOps",
        name_en="System Admin / DevOps",
        desc_fr="Scripts shell, configuration, monitoring, CI/CD, Docker, cloud",
        desc_en="Shell scripts, configuration, monitoring, CI/CD, Docker, cloud",
        use_cases=["code", "instruct"],
        keywords=["code", "coder", "instruct", "llama"],
        prefer_code=True,
        prefer_speed=True,
        weight_quality=0.3,
        weight_speed=0.3,
        weight_fit=0.25,
        weight_context=0.15,
        tips_fr=[
            "Les modèles rapides (3B–7B) suffisent pour les scripts shell/YAML.",
            "Préférez les modèles Instruct pour des commandes précises.",
            "Temperature très basse (0.1) pour des configs déterministes.",
        ],
        tips_en=[
            "Fast models (3B–7B) are sufficient for shell/YAML scripts.",
            "Prefer Instruct models for precise commands.",
            "Very low temperature (0.1) for deterministic configs.",
        ],
    ),
    Profession(
        id="marketer",
        icon="📢",
        name_fr="Marketing / Communication",
        name_en="Marketing / Communication",
        desc_fr="Copywriting, réseaux sociaux, emails, SEO, stratégie de contenu",
        desc_en="Copywriting, social media, emails, SEO, content strategy",
        use_cases=["chat", "text-generation", "summarization"],
        keywords=["instruct", "chat"],
        prefer_speed=True,
        weight_quality=0.3,
        weight_speed=0.3,
        weight_fit=0.2,
        weight_context=0.2,
        tips_fr=[
            "Les modèles Chat/Instruct sont idéaux pour le copywriting.",
            "Temperature moyenne (0.6–0.8) pour un bon équilibre créativité/cohérence.",
            "Utilisez les modèles 7B+ pour une meilleure qualité de texte.",
        ],
        tips_en=[
            "Chat/Instruct models are ideal for copywriting.",
            "Medium temperature (0.6–0.8) for a good creativity/coherence balance.",
            "Use 7B+ models for better text quality.",
        ],
    ),
    Profession(
        id="lawyer",
        icon="⚖️",
        name_fr="Juriste / Avocat",
        name_en="Lawyer / Legal",
        desc_fr="Analyse de contrats, résumés juridiques, recherche de jurisprudence",
        desc_en="Contract analysis, legal summaries, case law research",
        use_cases=["reasoning", "summarization", "question-answering"],
        keywords=["instruct", "reasoning", "qwen", "llama"],
        min_context=65536,
        prefer_quality=True,
        prefer_long_context=True,
        weight_quality=0.45,
        weight_speed=0.1,
        weight_fit=0.15,
        weight_context=0.3,
        tips_fr=[
            "Contexte très long (≥ 64K) indispensable pour les contrats et textes de loi.",
            "Privilégiez la qualité : modèles 14B+ pour une meilleure compréhension.",
            "Temperature très basse (0.1) pour des analyses précises et factuelles.",
        ],
        tips_en=[
            "Very long context (≥ 64K) essential for contracts and legal texts.",
            "Prioritize quality: 14B+ models for better understanding.",
            "Very low temperature (0.1) for precise and factual analysis.",
        ],
    ),
    Profession(
        id="teacher",
        icon="👨‍🏫",
        name_fr="Enseignant / Formateur",
        name_en="Teacher / Trainer",
        desc_fr="Création d'exercices, corrections, explications pédagogiques, QCM",
        desc_en="Exercise creation, grading, pedagogical explanations, quizzes",
        use_cases=["chat", "instruct", "question-answering"],
        keywords=["instruct", "chat", "llama", "gemma", "phi"],
        prefer_speed=True,
        weight_quality=0.3,
        weight_speed=0.3,
        weight_fit=0.2,
        weight_context=0.2,
        tips_fr=[
            "Les modèles Instruct sont parfaits pour générer des exercices structurés.",
            "Modèles rapides (3B–7B) pour des réponses instantanées en classe.",
            "Variez la temperature : basse pour les corrections, haute pour la créativité.",
        ],
        tips_en=[
            "Instruct models are perfect for generating structured exercises.",
            "Fast models (3B–7B) for instant responses in class.",
            "Vary temperature: low for grading, high for creativity.",
        ],
    ),
    Profession(
        id="translator",
        icon="🌐",
        name_fr="Traducteur / Interprète",
        name_en="Translator / Interpreter",
        desc_fr="Traduction, localisation, adaptation culturelle, terminologie",
        desc_en="Translation, localization, cultural adaptation, terminology",
        use_cases=["translation", "chat", "instruct"],
        keywords=["instruct", "qwen", "llama", "aya"],
        min_context=16384,
        prefer_quality=True,
        weight_quality=0.4,
        weight_speed=0.15,
        weight_fit=0.2,
        weight_context=0.25,
        tips_fr=[
            "Les modèles multilingues (Qwen, Aya, Llama) sont recommandés.",
            "Contexte long pour traduire des documents entiers avec cohérence.",
            "Temperature basse (0.2–0.3) pour des traductions fidèles.",
        ],
        tips_en=[
            "Multilingual models (Qwen, Aya, Llama) are recommended.",
            "Long context for translating entire documents consistently.",
            "Low temperature (0.2–0.3) for faithful translations.",
        ],
    ),
    Profession(
        id="entrepreneur",
        icon="🚀",
        name_fr="Entrepreneur / Startup",
        name_en="Entrepreneur / Startup",
        desc_fr="Business plan, pitch, études de marché, brainstorming, emails pros",
        desc_en="Business plan, pitch, market research, brainstorming, pro emails",
        use_cases=["chat", "reasoning", "text-generation"],
        keywords=["instruct", "chat", "llama", "qwen", "mistral"],
        prefer_speed=True,
        weight_quality=0.3,
        weight_speed=0.25,
        weight_fit=0.25,
        weight_context=0.2,
        tips_fr=[
            "Les modèles Chat polyvalents (Llama, Mistral, Qwen) couvrent tous les besoins.",
            "Utilisez le mode reasoning pour l'analyse stratégique.",
            "Modèles 7B suffisent pour la plupart des tâches courantes.",
        ],
        tips_en=[
            "Versatile Chat models (Llama, Mistral, Qwen) cover all needs.",
            "Use reasoning mode for strategic analysis.",
            "7B models are sufficient for most everyday tasks.",
        ],
    ),
]

PROFESSIONS_BY_ID = {p.id: p for p in PROFESSIONS}


def get_all_professions(lang: str = "fr") -> list[dict]:
    """Retourne la liste des professions pour l'UI."""
    return [
        {
            "id": p.id,
            "icon": p.icon,
            "name": p.name_fr if lang == "fr" else p.name_en,
            "description": p.desc_fr if lang == "fr" else p.desc_en,
            "prefer_vision": p.prefer_vision,
            "prefer_code": p.prefer_code,
        }
        for p in PROFESSIONS
    ]


def score_model_for_profession(
    model_fit: dict, profession: Profession,
) -> tuple[float, list[str]]:
    """
    Score un modèle pour une profession donnée.
    Retourne (score 0–100, liste de raisons).
    """
    reasons: list[str] = []
    model = model_fit.get("model", {})
    name_lower = (model.get("name") or "").lower()
    use_case_lower = (model.get("use_case") or "").lower()
    params_raw = model.get("parameters_raw") or 0
    params_b = params_raw / 1e9 if params_raw else 0
    ctx = model.get("context_length") or 4096

    bonus = 0.0

    for kw in profession.keywords:
        if kw in name_lower or kw in use_case_lower:
            bonus += 8
            break

    if profession.prefer_code and ("code" in name_lower or "coder" in name_lower):
        bonus += 10
        reasons.append("code" if not reasons else "")

    if profession.prefer_vision:
        families = model.get("families") or []
        if any(f in ["clip", "mllama"] for f in families):
            bonus += 10

    if profession.prefer_long_context and ctx >= profession.min_context:
        bonus += 5

    if profession.max_params_b and params_b > profession.max_params_b:
        bonus -= 15

    if ctx < profession.min_context:
        bonus -= 10

    sq = float(model_fit.get("score_quality") or 0)
    ss = float(model_fit.get("score_speed") or 0)
    sf = float(model_fit.get("score_fit") or 0)
    sc = float(model_fit.get("score_context") or 0)

    weighted = (
        profession.weight_quality * sq
        + profession.weight_speed * ss
        + profession.weight_fit * sf
        + profession.weight_context * sc
        + bonus
    )

    return max(0.0, min(100.0, round(weighted, 1))), reasons


def recommend_for_profession(
    profession_id: str,
    all_model_fits: list[dict],
    limit: int = 10,
    lang: str = "fr",
) -> dict:
    """Recommande les meilleurs modèles pour une profession."""
    profession = PROFESSIONS_BY_ID.get(profession_id)
    if not profession:
        return {"error": True, "message": f"Profession '{profession_id}' inconnue."}

    scored: list[dict] = []
    for mf in all_model_fits:
        fit_level = mf.get("fit_level", "trop_juste")
        if fit_level == "trop_juste":
            continue
        score, reasons = score_model_for_profession(mf, profession)
        scored.append({
            **mf,
            "profession_score": score,
            "profession_reasons": reasons,
        })

    scored.sort(key=lambda x: -x["profession_score"])

    tips = profession.tips_fr if lang == "fr" else profession.tips_en

    return {
        "profession": {
            "id": profession.id,
            "icon": profession.icon,
            "name": profession.name_fr if lang == "fr" else profession.name_en,
            "description": profession.desc_fr if lang == "fr" else profession.desc_en,
        },
        "models": scored[:limit],
        "tips": tips,
        "settings": {
            "min_context": profession.min_context,
            "max_params_b": profession.max_params_b,
            "prefer_vision": profession.prefer_vision,
            "prefer_code": profession.prefer_code,
            "suggested_temperature": (
                0.3 if profession.prefer_code
                else 0.9 if profession.id in ("designer", "writer")
                else 0.1 if profession.id in ("lawyer", "researcher")
                else 0.7
            ),
        },
    }
