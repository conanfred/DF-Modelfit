(function () {
  const API = "/api";
  const PAGE_SIZE = 100;
  /** URL du lien de soutien financier à la recherche. */
  const SUPPORT_URL = "https://www.paypal.me/conanfredleseul";
  let system = null;
  let models = [];
  let currentPage = 0;
  let sortBy = null;
  let sortDir = "desc";
  const HISTORY_KEY = "df_modelfit_history_v1";
  const SETTINGS_KEY = "df_modelfit_settings_v1";
  let history = [];
  let selectedModels = [];
  let scoresChart = null;
  let currentScenario = null;
  let currentLang = "fr";
  let currentTheme = "dark";

  function applyTheme() {
    document.documentElement.setAttribute("data-theme", currentTheme === "light" ? "light" : "dark");
  }

  function syncThemeButtons() {
    document.querySelectorAll(".btn-theme").forEach((btn) => {
      const theme = btn.getAttribute("data-theme");
      btn.classList.toggle("active", theme === currentTheme);
    });
  }

  const I18N = {
    fr: {
      titlePage: "Recommandation de modèles LLM pour votre machine",
      tagline: "Quels modèles LLM tournent sur votre machine ? — DF AI Research",
      yourConfig: "Votre configuration",
      loading: "Chargement…",
      search: "Recherche",
      searchPlaceholder: "Nom ou fournisseur…",
      fitTable: "Fit (table)",
      all: "Tous",
      parfait: "Parfait",
      bon: "Bon",
      marginal: "Marginal",
      trop_juste: "Trop juste",
      usageIcons: "Usage (icônes)",
      usageIconsTitle: "Filtre par usage (54 types Hugging Face). Chaque option a une icône.",
      fitMinApi: "Fit min. (API)",
      fitMarginal: "≥ Marginal",
      fitBon: "≥ Bon",
      fitParfaitOnly: "Parfait uniquement",
      paramsMax: "Params max (B)",
      paramsPlaceholder: "ex. 8",
      contextMin: "Contexte min.",
      contextPlaceholder: "ex. 8192",
      results: "Résultats",
      scenariosQuick: "Scénarios rapides",
      scenarioCoding: "Dév. / coding",
      scenarioChat: "Chat général",
      scenarioReasoning: "Reasoning profond",
      scenarioEdge: "Edge / léger",
      maxPerUsageHf: "Max par usage (HF)",
      maxPerUsageHfTitle: "Nombre max de modèles par usage (pipeline HF).",
      reset: "Réinitialiser",
      resetTitle: "Réinitialiser les filtres et afficher toute la liste",
      launchRecommendation: "Lancer la recommandation",
      updateModels: "Mise à jour des modèles",
      updateModelsTitle: "Récupérer les modèles depuis Hugging Face (selon Max HF)",
      refreshBannerMsg: "Mise à jour Hugging Face en arrière-plan (54 × Max)…",
      refreshBannerDone: "Mise à jour terminée. Liste actualisée.",
      models: "Modèles",
      thSel: "Sel.",
      thSelTitle: "Sélectionner des modèles à comparer",
      thFit: "Fit",
      thFitTitle: "Niveau d'adaptation à votre machine",
      thState: "État",
      thStateTitle: "Nouveau ou mis à jour lors de la dernière synchronisation",
      thModel: "Modèle",
      thModelTitle: "Nom du modèle (dépôt Hugging Face)",
      thProvider: "Fournisseur",
      thProviderTitle: "Organisation ou éditeur du modèle",
      thParams: "Params",
      thParamsTitle: "Cliquer pour trier par paramètres",
      thMem: "Mémoire",
      thMemTitle: "Cliquer pour trier par mémoire",
      thMode: "Mode",
      thModeTitle: "Exécution sur GPU ou CPU",
      thContext: "Contexte",
      thContextTitle: "Cliquer pour trier par longueur de contexte",
      thUsage: "Usage",
      thUsageTitle: "Rôle du modèle (Code, Chat, RAG, Vision…)",
      thAvis: "Avis",
      thAvisTitle: "Cliquer pour trier par avis (likes)",
      loadingModels: "Chargement des modèles…",
      prevPage: "← Précédente",
      prevPageTitle: "Page précédente",
      nextPage: "Suivante →",
      nextPageTitle: "Page suivante",
      usageLegendTitle: "Usage (un modèle peut avoir plusieurs icônes) :",
      compareTitle: "Comparaison & graphiques",
      compareHelp: "Sélectionnez jusqu'à 3 modèles dans le tableau pour comparer leurs scores (Qualité, Vitesse, Fit, Contexte) et voir un exemple de snippet Python.",
      snippetTitle: "Snippet Python pour le modèle sélectionné",
      snippetHelp: "Ce code illustre comment interroger un serveur de modèle local avec le modèle choisi. Adaptez l'URL et les paramètres selon votre runtime.",
      copyCode: "Copier le code",
      historyTitle: "Historique des recommandations",
      historyReset: "Réinitialiser",
      historyResetTitle: "Vider l'historique local",
      historyHelp: "Chaque combinaison de filtres utilisée est sauvegardée localement dans votre navigateur. Cliquez sur une entrée pour rejouer la configuration.",
      historyEmpty: "Aucune recommandation enregistrée pour l'instant.",
      footerText: "DF Modelfit — par DF AI Research. Données modèles : Hugging Face. Fit calculé localement (RAM/VRAM).",
      footerLicense: "Usage gratuit pour le public. Entreprises et laboratoires : seule une licence écrite et signée de la main de l'auteur est acceptée.",
      footerTextHtml: "<strong>DF Modelfit</strong> — par <strong>DF AI Research</strong>. Données modèles : Hugging Face. Fit calculé localement (RAM/VRAM).",
      footerLicenseHtml: "Usage gratuit pour le public. Entreprises et laboratoires : seule une <strong>licence écrite et signée</strong> de la main de l'auteur est acceptée — aucune autre forme. <a href=\"/license\" rel=\"license\">Voir la licence</a>. Contact : <a href=\"mailto:contact@dfairesearch.com\">contact@dfairesearch.com</a> — <a href=\"https://dfairesearch.com/\" target=\"_blank\" rel=\"noopener noreferrer\">dfairesearch.com</a>.",
      footerSupportHtml: "Soutien à la recherche : <a href=\"" + SUPPORT_URL + "\" target=\"_blank\" rel=\"noopener noreferrer\">Soutenez notre recherche (don)</a>.",
      licenseLink: "Voir la licence",
      personalise: "Personnalisé",
      filtersDefault: "Filtres par défaut",
      fitAllLabel: "Fit : tous",
      pageInfo: "Page %1 sur %2",
      lastUpdatePrefix: "Dernière mise à jour : ",
      ramTotal: "RAM totale",
      ramAvailable: "RAM disponible",
      cpuCores: "Cœurs CPU",
      processor: "Processeur",
      gpu: "GPU",
      vram: "VRAM",
      backend: "Backend",
      noGpu: "Aucun",
      noModelsMatch: "Aucun modèle ne correspond aux filtres.",
      statusNew: "Nouveau",
      statusUpdated: "Mis à jour",
      createdLabel: "Créé :",
      updatedLabel: "Mis à jour :",
      modeGpu: "GPU",
      modeCpu: "CPU",
      modeGpuTitle: "Fonctionne sur GPU",
      modeCpuTitle: "Fonctionne sur CPU",
      likesOnHf: "sur Hugging Face",
      noRatingHf: "Pas de note sur Hugging Face",
      openOnHf: "Ouvrir sur Hugging Face",
      openOrgOnHf: "Ouvrir l'organisation sur Hugging Face",
      selectForCompare: "Sélectionner ce modèle pour la comparaison",
      modelNumber: "Modèle %1",
      chartQuality: "Qualité",
      chartSpeed: "Vitesse",
      chartFit: "Fit",
      chartContext: "Contexte",
      snippetPlaceholder: "Sélectionnez un modèle dans le tableau pour voir un exemple de snippet Python ici.",
      paginationAriaLabel: "Pagination des modèles",
      filtersFormAriaLabel: "Filtres des modèles",
      errorLoad: "Erreur : vérifiez que le serveur tourne (lance.bat).",
      errorModels: "Impossible de charger les modèles.",
      errorServer: "Erreur : lancez le serveur (lance.bat) puis ouvrez http://localhost:5050",
      loadingShort: "Chargement…",
      chartAriaLabel: "Comparaison des scores des modèles",
      errorNetwork: "Erreur réseau. Vérifiez que le serveur DF Modelfit tourne (python main.py) et que vous ouvrez http://localhost:5050",
      errorUpdateFail: "Échec de la mise à jour.",
      customProfile: "Profil personnalisé",
      applyCustom: "Appliquer le profil",
      resetCustom: "Revenir à la détection auto",
      compareTableTitle: "Comparaison détaillée",
      changelogTitle: "Changelog des modèles",
      changelogHelp: "Modèles récemment ajoutés ou mis à jour lors des dernières synchronisations Hugging Face.",
      changelogEmpty: "Aucun changement récent.",
      exportCsv: "CSV",
      exportJson: "JSON",
      compareMetric: "Métrique",
      compareNoSelection: "Sélectionnez des modèles pour voir le détail.",
      scenarioCodingLabel: "Dév. / coding",
      scenarioChatLabel: "Chat général",
      scenarioReasoningLabel: "Reasoning profond",
      scenarioEdgeLabel: "Edge / léger",
      scenarioCustomLabel: "Personnalisé",
      runtimesTitle: "IA locales installées",
      runtimesHelp: "Détection automatique des runtimes IA (Ollama, LM Studio, llama.cpp). Gérez vos modèles locaux : installer, mettre à jour ou supprimer.",
      localModelsTitle: "Modèles installés localement",
      installModelTitle: "Installer un modèle",
      installedBadge: "Installé",
      chatTitle: "💬 Chat IA",
      chatClose: "Fermer",
      chatSelectModel: "Sélectionner un modèle…",
      chatSettings: "⚙️ Paramètres",
      chatPresetSystem: "Preset système",
      chatCustomPrompt: "System prompt personnalisé",
      chatTemperature: "Temperature",
      chatTopP: "Top P",
      chatTopK: "Top K",
      chatMaxTokens: "Max tokens",
      chatContextWindow: "Context window",
      chatRepeatPenalty: "Repeat penalty",
      chatSeed: "Seed",
      chatResetDefaults: "Réinitialiser",
      chatNewConv: "➕ Nouvelle",
      chatConversations: "📋 Conversations",
      chatWelcomeTitle: "Discutez avec vos modèles IA locaux",
      chatWelcomeSub: "Sélectionnez un modèle installé via Ollama, posez vos questions, ou utilisez 📸 pour partager votre écran.",
      chatDropImage: "Glissez-déposez une image ici",
      chatCapture: "📸 Capture",
      chatAttach: "📎 Joindre",
      chatPlaceholder: "Écrivez votre message…",
      chatSend: "Envoyer",
      chatStop: "Arrêter",
      chatRegenerate: "Régénérer",
      chatGenerating: "Génération…",
      chatCopy: "Copier",
      chatCopied: "Copié ✓",
      chatOllamaNotRunning: "Ollama non démarré…",
      chatNoModels: "Aucun modèle installé",
      chatNoConversations: "Aucune conversation",
      chatDeleteConv: "Supprimer",
      chatScreenCaptured: "Écran capturé !",
      chatResetDone: "Paramètres réinitialisés",
      chatOpenPanel: "Ouvrir le chat IA",
      chatError: "Erreur : ",
      chatErrorCheck: "vérifiez qu'Ollama tourne",
      chatErrorUnknown: "inconnue",
    },
    en: {
      titlePage: "LLM model recommendation for your machine",
      tagline: "Which LLM models run on your machine? — DF AI Research",
      yourConfig: "Your configuration",
      loading: "Loading…",
      search: "Search",
      searchPlaceholder: "Name or provider…",
      fitTable: "Fit (table)",
      all: "All",
      parfait: "Perfect",
      bon: "Good",
      marginal: "Marginal",
      trop_juste: "Too tight",
      usageIcons: "Usage (icons)",
      usageIconsTitle: "Filter by usage (54 Hugging Face types). Each option has an icon.",
      fitMinApi: "Min. fit (API)",
      fitMarginal: "≥ Marginal",
      fitBon: "≥ Good",
      fitParfaitOnly: "Perfect only",
      paramsMax: "Max params (B)",
      paramsPlaceholder: "e.g. 8",
      contextMin: "Min. context",
      contextPlaceholder: "e.g. 8192",
      results: "Results",
      scenariosQuick: "Quick scenarios",
      scenarioCoding: "Dev. / coding",
      scenarioChat: "General chat",
      scenarioReasoning: "Deep reasoning",
      scenarioEdge: "Edge / light",
      maxPerUsageHf: "Max per usage (HF)",
      maxPerUsageHfTitle: "Max models per usage (HF pipeline).",
      reset: "Reset",
      resetTitle: "Reset filters and show full list",
      launchRecommendation: "Launch recommendation",
      updateModels: "Update models",
      updateModelsTitle: "Fetch models from Hugging Face (according to Max HF)",
      refreshBannerMsg: "Updating Hugging Face in background (54 × Max)…",
      refreshBannerDone: "Update complete. List refreshed.",
      models: "Models",
      thSel: "Sel.",
      thSelTitle: "Select models to compare",
      thFit: "Fit",
      thFitTitle: "Adaptation level to your machine",
      thState: "State",
      thStateTitle: "New or updated in last sync",
      thModel: "Model",
      thModelTitle: "Model name (Hugging Face repo)",
      thProvider: "Provider",
      thProviderTitle: "Organization or editor",
      thParams: "Params",
      thParamsTitle: "Click to sort by parameters",
      thMem: "Memory",
      thMemTitle: "Click to sort by memory",
      thMode: "Mode",
      thModeTitle: "GPU or CPU execution",
      thContext: "Context",
      thContextTitle: "Click to sort by context length",
      thUsage: "Usage",
      thUsageTitle: "Model role (Code, Chat, RAG, Vision…)",
      thAvis: "Likes",
      thAvisTitle: "Click to sort by likes",
      loadingModels: "Loading models…",
      prevPage: "← Previous",
      prevPageTitle: "Previous page",
      nextPage: "Next →",
      nextPageTitle: "Next page",
      usageLegendTitle: "Usage (a model can have multiple icons):",
      compareTitle: "Comparison & charts",
      compareHelp: "Select up to 3 models in the table to compare their scores (Quality, Speed, Fit, Context) and see a Python snippet example.",
      snippetTitle: "Python snippet for selected model",
      snippetHelp: "This code shows how to query a local model server with the chosen model. Adapt the URL and parameters to your runtime.",
      copyCode: "Copy code",
      historyTitle: "Recommendation history",
      historyReset: "Reset",
      historyResetTitle: "Clear local history",
      historyHelp: "Each filter combination used is saved locally in your browser. Click an entry to replay the configuration.",
      historyEmpty: "No recommendation recorded yet.",
      footerText: "DF Modelfit — by DF AI Research. Model data: Hugging Face. Fit computed locally (RAM/VRAM).",
      footerLicense: "Free use for the public. Companies and laboratories: only a written license signed by hand by the author is accepted.",
      footerTextHtml: "<strong>DF Modelfit</strong> — by <strong>DF AI Research</strong>. Model data: Hugging Face. Fit computed locally (RAM/VRAM).",
      footerLicenseHtml: "Free use for the public. Companies and laboratories: only a <strong>written, hand-signed license</strong> by the author is accepted — no other form. <a href=\"/license\" rel=\"license\">View license</a>. Contact: <a href=\"mailto:contact@dfairesearch.com\">contact@dfairesearch.com</a> — <a href=\"https://dfairesearch.com/\" target=\"_blank\" rel=\"noopener noreferrer\">dfairesearch.com</a>.",
      footerSupportHtml: "Support our research: <a href=\"" + SUPPORT_URL + "\" target=\"_blank\" rel=\"noopener noreferrer\">Donate to our research</a>.",
      licenseLink: "View license",
      personalise: "Custom",
      filtersDefault: "Default filters",
      fitAllLabel: "Fit: all",
      pageInfo: "Page %1 of %2",
      lastUpdatePrefix: "Last update: ",
      ramTotal: "Total RAM",
      ramAvailable: "Available RAM",
      cpuCores: "CPU cores",
      processor: "Processor",
      gpu: "GPU",
      vram: "VRAM",
      backend: "Backend",
      noGpu: "None",
      noModelsMatch: "No models match the filters.",
      statusNew: "New",
      statusUpdated: "Updated",
      createdLabel: "Created:",
      updatedLabel: "Updated:",
      modeGpu: "GPU",
      modeCpu: "CPU",
      modeGpuTitle: "Runs on GPU",
      modeCpuTitle: "Runs on CPU",
      likesOnHf: "on Hugging Face",
      noRatingHf: "No rating on Hugging Face",
      openOnHf: "Open on Hugging Face",
      openOrgOnHf: "Open organization on Hugging Face",
      selectForCompare: "Select this model for comparison",
      modelNumber: "Model %1",
      chartQuality: "Quality",
      chartSpeed: "Speed",
      chartFit: "Fit",
      chartContext: "Context",
      snippetPlaceholder: "Select a model in the table to see a Python snippet example here.",
      paginationAriaLabel: "Models pagination",
      filtersFormAriaLabel: "Model filters",
      errorLoad: "Error: make sure the server is running (lance.bat).",
      errorModels: "Unable to load models.",
      errorServer: "Error: start the server (lance.bat) then open http://localhost:5050",
      loadingShort: "Loading…",
      chartAriaLabel: "Model scores comparison",
      errorNetwork: "Network error. Make sure the DF Modelfit server is running (python main.py) and you open http://localhost:5050",
      errorUpdateFail: "Update failed.",
      customProfile: "Custom profile",
      applyCustom: "Apply profile",
      resetCustom: "Back to auto-detection",
      compareTableTitle: "Detailed comparison",
      changelogTitle: "Model changelog",
      changelogHelp: "Models recently added or updated during the latest Hugging Face syncs.",
      changelogEmpty: "No recent changes.",
      exportCsv: "CSV",
      exportJson: "JSON",
      compareMetric: "Metric",
      compareNoSelection: "Select models to see details.",
      scenarioCodingLabel: "Dev. / coding",
      scenarioChatLabel: "General chat",
      scenarioReasoningLabel: "Deep reasoning",
      scenarioEdgeLabel: "Edge / light",
      scenarioCustomLabel: "Custom",
      runtimesTitle: "Local AI runtimes",
      runtimesHelp: "Auto-detection of AI runtimes (Ollama, LM Studio, llama.cpp). Manage your local models: install, update, or delete.",
      localModelsTitle: "Locally installed models",
      installModelTitle: "Install a model",
      installedBadge: "Installed",
      chatTitle: "💬 AI Chat",
      chatClose: "Close",
      chatSelectModel: "Select a model…",
      chatSettings: "⚙️ Settings",
      chatPresetSystem: "System preset",
      chatCustomPrompt: "Custom system prompt",
      chatTemperature: "Temperature",
      chatTopP: "Top P",
      chatTopK: "Top K",
      chatMaxTokens: "Max tokens",
      chatContextWindow: "Context window",
      chatRepeatPenalty: "Repeat penalty",
      chatSeed: "Seed",
      chatResetDefaults: "Reset defaults",
      chatNewConv: "➕ New",
      chatConversations: "📋 Conversations",
      chatWelcomeTitle: "Chat with your local AI models",
      chatWelcomeSub: "Select a model via Ollama, ask questions, or use 📸 to share your screen.",
      chatDropImage: "Drop an image here",
      chatCapture: "📸 Capture",
      chatAttach: "📎 Attach",
      chatPlaceholder: "Type your message…",
      chatSend: "Send",
      chatStop: "Stop",
      chatRegenerate: "Regenerate",
      chatGenerating: "Generating…",
      chatCopy: "Copy",
      chatCopied: "Copied ✓",
      chatOllamaNotRunning: "Ollama not running…",
      chatNoModels: "No models installed",
      chatNoConversations: "No conversations",
      chatDeleteConv: "Delete",
      chatScreenCaptured: "Screen captured!",
      chatResetDone: "Settings reset",
      chatOpenPanel: "Open AI chat",
      chatError: "Error: ",
      chatErrorCheck: "check that Ollama is running",
      chatErrorUnknown: "unknown",
    },
  };

  function t(key) {
    return (I18N[currentLang] && I18N[currentLang][key]) || (I18N.fr[key]) || key;
  }

  function applyI18n() {
    document.documentElement.lang = currentLang;
    document.title = t("titlePage");
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const k = el.getAttribute("data-i18n");
      if (k) el.textContent = t(k);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const k = el.getAttribute("data-i18n-placeholder");
      if (k) el.placeholder = t(k);
    });
    document.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const k = el.getAttribute("data-i18n-title");
      if (k) el.title = t(k);
    });
    document.querySelectorAll("[data-i18n-html]").forEach((el) => {
      const k = el.getAttribute("data-i18n-html");
      if (k) el.innerHTML = t(k);
    });
    document.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
      const k = el.getAttribute("data-i18n-aria-label");
      if (k) el.setAttribute("aria-label", t(k));
    });
  }

  function syncLangButtons() {
    document.querySelectorAll(".btn-lang").forEach((btn) => {
      const lang = btn.getAttribute("data-lang");
      btn.classList.toggle("active", lang === currentLang);
      btn.title = lang === "fr" ? "Français" : "English";
    });
  }

  const el = {
    systemGrid: document.getElementById("system-grid"),
    count: document.getElementById("count"),
    modelsTbody: document.getElementById("models-tbody"),
    search: document.getElementById("search"),
    filterFit: document.getElementById("filter-fit"),
    filterUsage: document.getElementById("filter-usage"),
    minFit: document.getElementById("min-fit"),
    maxParams: document.getElementById("max-params"),
    minContext: document.getElementById("min-context"),
    limit: document.getElementById("limit"),
    maxModelsHf: document.getElementById("max-models-hf"),
    btnReset: document.getElementById("btn-reset"),
    btnRefresh: document.getElementById("btn-refresh"),
    btnHf: document.getElementById("btn-hf"),
    lastUpdate: document.getElementById("last-update"),
    pagination: document.getElementById("pagination"),
    paginationInfo: document.getElementById("pagination-info"),
    btnPrev: document.getElementById("btn-prev"),
    btnNext: document.getElementById("btn-next"),
    scenarioButtons: document.querySelectorAll(".btn-scenario"),
    compareList: document.getElementById("compare-list"),
    historyList: document.getElementById("history-list"),
    scoresChart: document.getElementById("scores-chart"),
    pythonSnippet: document.getElementById("python-snippet"),
    btnCopySnippet: document.getElementById("btn-copy-snippet"),
    btnExportCsv: document.getElementById("btn-export-csv"),
    btnExportJson: document.getElementById("btn-export-json"),
    btnToggleCustom: document.getElementById("btn-toggle-custom"),
    customPanel: document.getElementById("custom-profile-panel"),
    customRam: document.getElementById("custom-ram"),
    customCores: document.getElementById("custom-cores"),
    customVram: document.getElementById("custom-vram"),
    customBackend: document.getElementById("custom-backend"),
    btnApplyCustom: document.getElementById("btn-apply-custom"),
    btnResetCustom: document.getElementById("btn-reset-custom"),
    changelogCard: document.getElementById("changelog-card"),
    changelogList: document.getElementById("changelog-list"),
    compareTableWrap: document.getElementById("compare-table-wrap"),
    compareDetailTable: document.getElementById("compare-detail-table"),
  };

  let isCustomProfile = false;

  function formatLastUpdated(iso) {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return "";
      const locale = currentLang === "en" ? "en-GB" : "fr-FR";
      return d.toLocaleDateString(locale, { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
    } catch (_) {
      return "";
    }
  }

  function setLastUpdateText(iso) {
    const node = el.lastUpdate;
    if (!node) return;
    const text = formatLastUpdated(iso);
    if (text) {
      node.textContent = t("lastUpdatePrefix") + text;
      node.style.visibility = "visible";
    } else {
      node.textContent = "";
      node.style.visibility = "hidden";
    }
  }

  function getFitLabel(fitKey) {
    return t(fitKey in { parfait: 1, bon: 1, marginal: 1, trop_juste: 1 } ? fitKey : "marginal");
  }

  // Icônes visuelles pour l’usage (use case)
  function likesToStars(likes) {
    if (likes == null || typeof likes !== "number" || likes <= 0) return { stars: "", count: "" };
    const n = Math.min(5, Math.max(1, Math.floor(Math.log10(likes + 1) * 1.8)));
    const full = "★".repeat(n);
    const empty = "☆".repeat(5 - n);
    const count = likes >= 1000 ? (likes / 1000).toFixed(1).replace(".0", "") + "k" : String(likes);
    return { stars: full + empty, count };
  }

  // 54 usages (pipelines) Hugging Face — ordre aligné sur le backend
  const PIPELINE_USAGES = [
    { value: "text-generation-inference", icon: "🚀", label: "Inférence LLM" },
    { value: "text-classification", icon: "🏷️", label: "Classification de texte" },
    { value: "token-classification", icon: "🔤", label: "Classification de tokens" },
    { value: "table-question-answering", icon: "📊", label: "QA sur tables" },
    { value: "question-answering", icon: "🎯", label: "Question-réponse" },
    { value: "zero-shot-classification", icon: "⚡", label: "Classification zero-shot" },
    { value: "translation", icon: "🌐", label: "Traduction" },
    { value: "summarization", icon: "📎", label: "Résumé" },
    { value: "feature-extraction", icon: "🔢", label: "Extraction de traits" },
    { value: "text-generation", icon: "✨", label: "Génération de texte" },
    { value: "fill-mask", icon: "🔲", label: "Fill-mask" },
    { value: "sentence-similarity", icon: "🔗", label: "Similarité de phrases" },
    { value: "text-to-speech", icon: "🔊", label: "Texte vers parole" },
    { value: "text-to-audio", icon: "🎵", label: "Texte vers audio" },
    { value: "automatic-speech-recognition", icon: "🎤", label: "Reconnaissance vocale" },
    { value: "audio-to-audio", icon: "🔄", label: "Audio vers audio" },
    { value: "audio-classification", icon: "📻", label: "Classification audio" },
    { value: "audio-text-to-text", icon: "🎧", label: "Audio-texte vers texte" },
    { value: "voice-activity-detection", icon: "🗣️", label: "Détection de voix" },
    { value: "depth-estimation", icon: "📐", label: "Estimation de profondeur" },
    { value: "image-classification", icon: "🖼️", label: "Classification d'images" },
    { value: "object-detection", icon: "📦", label: "Détection d'objets" },
    { value: "image-segmentation", icon: "✂️", label: "Segmentation d'images" },
    { value: "text-to-image", icon: "🖌️", label: "Texte vers image" },
    { value: "image-to-text", icon: "📝", label: "Image vers texte" },
    { value: "image-to-image", icon: "🔄", label: "Image vers image" },
    { value: "image-to-video", icon: "🎬", label: "Image vers vidéo" },
    { value: "unconditional-image-generation", icon: "🎨", label: "Génération d'images" },
    { value: "video-classification", icon: "📹", label: "Classification vidéo" },
    { value: "reinforcement-learning", icon: "🎮", label: "Apprentissage par renforcement" },
    { value: "robotics", icon: "🤖", label: "Robotique" },
    { value: "tabular-classification", icon: "📋", label: "Classification tabulaire" },
    { value: "tabular-regression", icon: "📈", label: "Régression tabulaire" },
    { value: "tabular-to-text", icon: "📄", label: "Tableau vers texte" },
    { value: "table-to-text", icon: "📑", label: "Table vers texte" },
    { value: "multiple-choice", icon: "☑️", label: "Choix multiples" },
    { value: "text-ranking", icon: "📊", label: "Classement de texte" },
    { value: "text-retrieval", icon: "🔍", label: "Recherche de texte" },
    { value: "time-series-forecasting", icon: "📉", label: "Prévision de séries" },
    { value: "text-to-video", icon: "🎞️", label: "Texte vers vidéo" },
    { value: "image-text-to-text", icon: "👁️", label: "Image+texte vers texte" },
    { value: "image-text-to-image", icon: "🖼️", label: "Image+texte vers image" },
    { value: "image-text-to-video", icon: "🎥", label: "Image+texte vers vidéo" },
    { value: "visual-question-answering", icon: "❓", label: "QA visuelle" },
    { value: "document-question-answering", icon: "📑", label: "QA sur documents" },
    { value: "zero-shot-image-classification", icon: "⚡", label: "Image zero-shot" },
    { value: "graph-ml", icon: "🕸️", label: "Graph ML" },
    { value: "mask-generation", icon: "🎭", label: "Génération de masques" },
    { value: "zero-shot-object-detection", icon: "👁️", label: "Détection zero-shot" },
    { value: "text-to-3d", icon: "🧊", label: "Texte vers 3D" },
    { value: "image-to-3d", icon: "🔷", label: "Image vers 3D" },
    { value: "image-feature-extraction", icon: "🔎", label: "Traits d'image" },
    { value: "video-text-to-text", icon: "📺", label: "Vidéo+texte vers texte" },
    { value: "keypoint-detection", icon: "📍", label: "Détection de points-clés" },
    { value: "visual-document-retrieval", icon: "📂", label: "Recherche doc visuelle" },
    { value: "any-to-any", icon: "🔀", label: "Multimodal any-to-any" },
    { value: "video-to-video", icon: "🔄", label: "Vidéo vers vidéo" },
    { value: "other", icon: "📦", label: "Autre" },
  ];

  const PIPELINE_BY_VALUE = Object.fromEntries(PIPELINE_USAGES.map((p) => [p.value, p]));

  // Retourne les icônes d'usage : si pipeline_tag connu, son icône ; sinon fallback useCaseIcons(use_case, name)
  function getUsageIcons(model) {
    const tag = model && model.pipeline_tag;
    if (tag && PIPELINE_BY_VALUE[tag]) {
      return [{ icon: PIPELINE_BY_VALUE[tag].icon, key: tag }];
    }
    return useCaseIcons(model && model.use_case, model && model.name);
  }

  // Ancienne logique conservée pour modèles sans pipeline_tag (données locales)
  function useCaseIcons(useCase, modelName) {
    const u = ((useCase || "") + " " + (modelName || "")).toLowerCase();
    const list = [];
    const add = (icon, key) => { if (!list.some((x) => x.key === key)) list.push({ icon, key }); };
    if (u.includes("embed") || u.includes("rag") || u.includes("sentence-similarity")) add("🔗", "rag");
    if (u.includes("code") || u.includes("coder") || u.includes("starcoder")) add("💻", "code");
    if (u.includes("reason") || u.includes("raisonnement") || u.includes("r1") || u.includes("chain-of-thought")) add("🧠", "reason");
    if (u.includes("vision") || u.includes("multimodal") || u.includes("vl-") || u.includes("image-text")) add("👁️", "vision");
    if (u.includes("chat") || u.includes("instruct") || u.includes("instruction")) add("💬", "chat");
    if (u.includes("génération") || u.includes("text generation") || u.includes("texte") || u.includes("general purpose") || u.includes("text-generation")) add("✨", "text");
    if (u.includes("translation") || u.includes("traduction")) add("🌐", "translation");
    if (u.includes("tiny") || u.includes("small") || u.includes("mini") || u.includes("edge") || u.includes("lightweight")) add("📱", "edge");
    if (u.includes("research") || u.includes("scientific") || u.includes("recherche")) add("🔬", "research");
    if (u.includes("summar") || u.includes("extract") || u.includes("résumé")) add("📎", "summary");
    if (u.includes("question") || u.includes(" qa ") || u.includes("réponse")) add("🎯", "qa");
    if (list.length === 0) add("📦", "general");
    return list;
  }

  function renderSystem(s) {
    if (!s) return;
    const items = [
      { label: t("ramTotal"), value: `${s.total_ram_gb} Go` },
      { label: t("ramAvailable"), value: `${s.available_ram_gb} Go` },
      { label: t("cpuCores"), value: String(s.cpu_cores) },
      { label: t("processor"), value: s.cpu_name || "—" },
    ];
    if (s.has_gpu) {
      items.push({ label: t("gpu"), value: s.gpu_name || "—", cls: "gpu" });
      if (s.gpu_vram_gb != null) {
        items.push({ label: t("vram"), value: `${s.gpu_vram_gb} Go`, cls: "gpu" });
      }
      items.push({ label: t("backend"), value: s.backend || "—" });
    } else {
      items.push({ label: t("gpu"), value: t("noGpu") });
    }
    el.systemGrid.innerHTML = items
      .map(
        (i) =>
          `<div class="system-item ${i.cls || ""}"><div class="label">${i.label}</div><div class="value">${escapeHtml(i.value)}</div></div>`
      )
      .join("");
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function fitClass(level) {
    return "fit-" + (level === "trop_juste" ? "trop" : level);
  }

  function renderModels(list) {
    if (!list.length) {
      el.modelsTbody.innerHTML = '<tr><td colspan="11" class="loading">' + escapeHtml(t("noModelsMatch")) + '</td></tr>';
      return;
    }
    el.modelsTbody.innerHTML = list
      .map((row, idx) => {
        const m = row.model;
        const name = m.name || "—";
        const provider = m.provider || "—";
        const params = m.parameter_count || "—";
        const mem = `${row.mem_requise_gb} Go (${row.utilisation_pct} %)`;
        const modeGpu = row.mode === "gpu";
        const modeIcon = modeGpu ? "🎮" : "💻";
        const modeLabel = modeGpu ? t("modeGpu") : t("modeCpu");
        const modeTitle = modeGpu ? t("modeGpuTitle") : t("modeCpuTitle");
        const ctx = m.context_length ? String(m.context_length) : "—";
        const ucList = getUsageIcons(m);
        const ucHtml = ucList.map((x) => {
          const text = (PIPELINE_BY_VALUE[x.key] && PIPELINE_BY_VALUE[x.key].label) || x.key || "";
          return `<span class="use-case-icon" title="${escapeHtml(text)}">${x.icon}</span>`;
        }).join(" ");
        const fitLabel = getFitLabel(row.fit_level);
        const likesRaw = m.hf_likes != null ? m.hf_likes : m.likes;
        const likes = typeof likesRaw === "number" ? likesRaw : (parseInt(likesRaw, 10) || 0);
        const avis = likesToStars(likes);
        const likesLabel = likes > 0 ? (likes >= 1000 ? (likes / 1000).toFixed(1).replace(".0", "") + "k" : likes) + " likes" : "";
        const avisHtml = avis.stars
          ? `<span class="stars" title="${escapeHtml(likesLabel)} ${escapeHtml(t("likesOnHf"))}">${avis.stars}</span> <span class="stars-count">${escapeHtml(avis.count)}</span>`
          : '<span class="avis-none" title="' + escapeHtml(t("noRatingHf")) + '">—</span>';
        const status = row.status;
        const statusLabel = status === "new" ? t("statusNew") : status === "updated" ? t("statusUpdated") : "—";
        const dateTip = m.created_at || m.updated_at ? t("createdLabel") + " " + (m.created_at || "—") + "\n" + t("updatedLabel") + " " + (m.updated_at || "—") : "";
        const statusHtml = status ? `<span class="status-badge status-${status}" title="${escapeHtml(dateTip)}">${escapeHtml(statusLabel)}</span>` : "<span>—</span>";
        const modelLink = name && name !== "—" ? `<a href="${escapeHtml("https://huggingface.co/" + encodeURI(name))}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(t("openOnHf"))}">${escapeHtml(name)}</a>` : escapeHtml(name);
        const orgSlug = name && name.includes("/") ? name.split("/")[0] : "";
        const providerLink = orgSlug ? `<a href="${escapeHtml("https://huggingface.co/" + encodeURI(orgSlug))}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(t("openOrgOnHf"))}">${escapeHtml(provider)}</a>` : escapeHtml(provider);
        const rowId = typeof row._id === "number" ? row._id : idx;
        const checked = selectedModels.some((s) => (s._id ?? s.model.name) === (row._id ?? row.model.name));
        var favActive = isFavorite(name);
        return `<tr class="selectable-row${checked ? " row-selected" : ""}" data-row-id="${rowId}">
          <td><input type="checkbox" class="model-select" data-row-id="${rowId}" ${checked ? "checked" : ""} aria-label="${escapeHtml(t("selectForCompare"))}"> <button type="button" class="fav-star${favActive ? " fav-active" : ""}" data-fav-model="${escapeHtml(name)}" aria-label="Favori" title="Favori">${favActive ? "★" : "☆"}</button></td>
          <td><span class="fit-badge ${fitClass(row.fit_level)}">${escapeHtml(fitLabel)}</span></td>
          <td class="status-cell">${statusHtml}</td>
          <td class="mono">${modelLink}</td>
          <td>${providerLink}</td>
          <td>${escapeHtml(params)}</td>
          <td>${escapeHtml(mem)}</td>
          <td><span class="mode-badge" title="${escapeHtml(modeTitle)}">${modeIcon} ${escapeHtml(modeLabel)}</span></td>
          <td class="mono">${escapeHtml(ctx)}</td>
          <td><span class="use-case-cell">${ucHtml}</span></td>
          <td class="avis-cell">${avisHtml}</td>
        </tr>`;
      })
      .join("");
  }

  function applyFilters(resetPage) {
    if (resetPage !== false) currentPage = 0;
    const q = (el.search && el.search.value || "").trim().toLowerCase();
    const fit = (el.filterFit && el.filterFit.value) || "";
    const usage = (el.filterUsage && el.filterUsage.value) || "";
    let list = models;
    if (q) {
      list = list.filter(
        (r) =>
          (r.model.name || "").toLowerCase().includes(q) ||
          (r.model.provider || "").toLowerCase().includes(q)
      );
    }
    if (fit) {
      list = list.filter((r) => r.fit_level === fit);
    }
    if (usage) {
      list = list.filter((r) => {
        if (r.model.pipeline_tag === usage) return true;
        const icons = useCaseIcons(r.model.use_case, r.model.name);
        return icons.some((x) => x.key === usage);
      });
    }
    if (sortBy) {
      list = [...list].sort((a, b) => {
        let va, vb;
        if (sortBy === "params") {
          va = a.model.parameters_raw != null ? Number(a.model.parameters_raw) : 0;
          vb = b.model.parameters_raw != null ? Number(b.model.parameters_raw) : 0;
        } else if (sortBy === "mem") {
          va = a.mem_requise_gb != null ? Number(a.mem_requise_gb) : 0;
          vb = b.mem_requise_gb != null ? Number(b.mem_requise_gb) : 0;
        } else if (sortBy === "avis") {
          const likes = (m) => {
            const v = m.model.hf_likes != null ? m.model.hf_likes : m.model.likes;
            return typeof v === "number" ? v : (parseInt(v, 10) || 0);
          };
          va = likes(a);
          vb = likes(b);
        } else if (sortBy === "context") {
          va = a.model.context_length != null ? Number(a.model.context_length) : 0;
          vb = b.model.context_length != null ? Number(b.model.context_length) : 0;
        } else return 0;
        if (va < vb) return sortDir === "asc" ? -1 : 1;
        if (va > vb) return sortDir === "asc" ? 1 : -1;
        return 0;
      });
    }
    updateSortIndicators();
    const total = list.length;
    el.count.textContent = total;
    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    if (currentPage >= totalPages) currentPage = Math.max(0, totalPages - 1);
    const start = currentPage * PAGE_SIZE;
    const pageList = list.slice(start, start + PAGE_SIZE);
    renderModels(pageList);
    renderSelectionState();

    if (el.paginationInfo) {
      el.paginationInfo.textContent = t("pageInfo").replace("%1", String(currentPage + 1)).replace("%2", String(totalPages));
    }
    if (el.btnPrev) {
      el.btnPrev.disabled = currentPage === 0;
    }
    if (el.btnNext) {
      el.btnNext.disabled = totalPages <= 1 || currentPage >= totalPages - 1;
    }
  }

  function goToPage(delta) {
    currentPage = Math.max(0, currentPage + delta);
    applyFilters(false);
    saveSettings();
  }

  function updateSortIndicators() {
    const arrow = sortDir === "asc" ? " ↑" : (sortDir === "desc" ? " ↓" : "");
    ["params", "mem", "context", "avis"].forEach((key) => {
      const elm = document.getElementById("sort-" + key);
      if (elm) elm.textContent = sortBy === key ? arrow : "";
    });
  }

  function setSort(column) {
    if (sortBy === column) sortDir = sortDir === "asc" ? "desc" : "asc";
    else { sortBy = column; sortDir = "desc"; }
    currentPage = 0;
    applyFilters(false);
    saveSettings();
  }

  function currentApiFilters() {
    return {
      search: (el.search && el.search.value.trim()) || "",
      minFit: (el.minFit && el.minFit.value) || "marginal",
      maxParams: el.maxParams && el.maxParams.value ? Number(el.maxParams.value) : null,
      minContext: el.minContext && el.minContext.value ? Number(el.minContext.value) : null,
      limit: el.limit && el.limit.value ? Number(el.limit.value) : 20,
      scenario: currentScenario,
    };
  }

  function saveHistoryEntry() {
    const cfg = currentApiFilters();
    const now = new Date();
    const entry = {
      ...cfg,
      createdAt: now.toISOString(),
    };
    history.unshift(entry);
    history = history.slice(0, 15);
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (_) {
      // ignore
    }
    renderHistory();
  }

  function loadHistory() {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (!raw) {
        history = [];
        return;
      }
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        history = parsed;
      } else {
        history = [];
      }
    } catch (_) {
      history = [];
    }
  }

  function clearHistory() {
    history = [];
    try {
      localStorage.removeItem(HISTORY_KEY);
    } catch (_) {}
    renderHistory();
  }

  function getSettingsFromForm() {
    return {
      search: (el.search && el.search.value) ? String(el.search.value).trim() : "",
      filterFit: (el.filterFit && el.filterFit.value) || "",
      filterUsage: (el.filterUsage && el.filterUsage.value) || "",
      minFit: (el.minFit && el.minFit.value) || "marginal",
      maxParams: (el.maxParams && el.maxParams.value) ? String(el.maxParams.value).trim() : "",
      minContext: (el.minContext && el.minContext.value) ? String(el.minContext.value).trim() : "",
      limit: (el.limit && el.limit.value) ? String(el.limit.value).trim() : "20",
      maxModelsHf: (el.maxModelsHf && el.maxModelsHf.value) ? String(el.maxModelsHf.value).trim() : "20",
      scenario: currentScenario,
      sortBy: sortBy,
      sortDir: sortDir,
      currentPage: currentPage,
      lang: currentLang,
      theme: currentTheme,
    };
  }

  function saveSettings() {
    try {
      const s = getSettingsFromForm();
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(s));
    } catch (_) {}
  }

  function loadSettings() {
    try {
      const raw = localStorage.getItem(SETTINGS_KEY);
      if (!raw) return;
      const s = JSON.parse(raw);
      if (!s || typeof s !== "object") return;
      if (el.search && s.search != null) el.search.value = String(s.search);
      if (el.filterFit && s.filterFit != null) el.filterFit.value = String(s.filterFit);
      if (el.filterUsage && s.filterUsage != null) el.filterUsage.value = String(s.filterUsage);
      if (el.minFit && s.minFit != null) el.minFit.value = String(s.minFit);
      if (el.maxParams && s.maxParams != null) el.maxParams.value = String(s.maxParams);
      if (el.minContext && s.minContext != null) el.minContext.value = String(s.minContext);
      if (el.limit && s.limit != null) el.limit.value = String(s.limit);
      if (el.maxModelsHf && s.maxModelsHf != null) el.maxModelsHf.value = String(s.maxModelsHf);
      if (s.scenario != null) currentScenario = s.scenario;
      if (s.sortBy != null) sortBy = s.sortBy;
      if (s.sortDir != null) sortDir = s.sortDir;
      if (typeof s.currentPage === "number" && s.currentPage >= 0) currentPage = s.currentPage;
      if (s.lang === "en" || s.lang === "fr") currentLang = s.lang;
      if (s.theme === "light" || s.theme === "dark") currentTheme = s.theme;
      syncScenarioButtons();
      updateSortIndicators();
    } catch (_) {}
  }

  function describeScenario(scenario) {
    if (!scenario) return t("scenarioCustomLabel");
    switch (scenario) {
      case "coding": return t("scenarioCodingLabel");
      case "chat": return t("scenarioChatLabel");
      case "reasoning": return t("scenarioReasoningLabel");
      case "edge": return t("scenarioEdgeLabel");
      default: return t("scenarioCustomLabel");
    }
  }

  function renderHistory() {
    if (!el.historyList) return;
    if (!history.length) {
      el.historyList.innerHTML = '<p class="history-empty">' + escapeHtml(t("historyEmpty")) + '</p>';
      return;
    }
    el.historyList.innerHTML = history
      .map((h, idx) => {
        const d = new Date(h.createdAt || Date.now());
        const dateText = isNaN(d.getTime()) ? "" : d.toLocaleString("fr-FR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
        const scenarioLabel = describeScenario(h.scenario);
        const fitLabel = h.minFit ? `Fit ≥ ${h.minFit}` : t("fitAllLabel");
        const ctxLabel = h.minContext ? `Ctx ≥ ${h.minContext}` : "";
        const pLabel = h.maxParams ? `Params ≤ ${h.maxParams}B` : "";
        const pieces = [fitLabel, ctxLabel, pLabel].filter(Boolean).join(" · ");
        return `<button type="button" class="history-entry" data-history-index="${idx}">
          <span class="history-entry-main">
            <span class="history-entry-title">${escapeHtml(scenarioLabel)}</span>
            <span class="history-entry-meta">${escapeHtml(pieces || t("filtersDefault"))}</span>
          </span>
          <span class="history-entry-meta">${escapeHtml(dateText)}</span>
        </button>`;
      })
      .join("");
  }

  function applyHistoryEntry(index) {
    const entry = history[index];
    if (!entry) return;
    if (el.minFit) el.minFit.value = entry.minFit || "marginal";
    if (el.maxParams) el.maxParams.value = entry.maxParams != null ? String(entry.maxParams) : "";
    if (el.minContext) el.minContext.value = entry.minContext != null ? String(entry.minContext) : "";
    if (el.limit) el.limit.value = entry.limit != null ? String(entry.limit) : "20";
    currentScenario = entry.scenario || null;
    if (el.search) el.search.value = entry.search || "";
    // Filtres table (optionnels)
    if (el.filterFit) el.filterFit.value = "";
    if (el.filterUsage) el.filterUsage.value = "";
    syncScenarioButtons();
    saveSettings();
    fetchModels().catch(() => {});
  }

  function syncScenarioButtons() {
    if (!el.scenarioButtons) return;
    el.scenarioButtons.forEach((btn) => {
      const sc = btn.getAttribute("data-scenario");
      if (sc && sc === currentScenario) btn.classList.add("active");
      else btn.classList.remove("active");
    });
  }

  const FETCH_TIMEOUT_MS = 20000;
  const REFRESH_TIMEOUT_MS = 3600000; // 1 h (backend peut prendre 20–30 min pour 54 × 20)
  const REFRESH_POLL_INTERVAL_MS = 25000; // 25 s : vérifier si la liste a changé
  const REFRESH_POLL_MAX_MINUTES = 60;   // arrêter le poll après 60 min
  const AUTO_REFRESH_IF_OLDER_DAYS = 30;   // Mise à jour auto au démarrage uniquement si dernière MAJ > 1 mois

  let lastModelsUpdateIso = null;

  function parseLastUpdate(isoStr) {
    if (!isoStr || typeof isoStr !== "string") return null;
    const t = new Date(isoStr).getTime();
    return Number.isNaN(t) ? null : t;
  }

  /** true si la dernière mise à jour est plus vieille que N jours (ou date inconnue). */
  function isOlderThanDays(isoStr, days) {
    const t = parseLastUpdate(isoStr);
    if (t == null) return true;
    return (Date.now() - t) >= days * 24 * 3600 * 1000;
  }

  function applyApiResponse(data) {
    if (data.system) system = data.system;
    models = (data.models || []).map((m, idx) => ({ ...m, _id: idx }));
    lastModelsUpdateIso = data.last_updated || (system && system.models_last_updated) || null;
    renderSystem(system);
    if (data.last_updated) setLastUpdateText(data.last_updated);
    else if (system && system.models_last_updated) setLastUpdateText(system.models_last_updated);
    else setLastUpdateText(null);
    if (el.modelsTbody) el.modelsTbody.setAttribute('aria-busy', 'false');
    selectedModels = [];
    renderFitDistribution();
    applyFilters();
  }

  async function fetchFullModels() {
    if (el.modelsTbody) el.modelsTbody.innerHTML = '<tr><td colspan="11" class="loading">' + escapeHtml(t("loadingModels")) + '</td></tr>';
    const controller = new AbortController();
    const to = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    try {
      const res = await fetch(`${API}/models`, { signal: controller.signal });
      clearTimeout(to);
      if (!res.ok) throw new Error(res.statusText);
      const data = await res.json();
      applyApiResponse(data);
    } catch (err) {
      clearTimeout(to);
      if (el.modelsTbody) el.modelsTbody.innerHTML = '<tr><td colspan="11" class="loading">' + escapeHtml(err.message) + '. ' + escapeHtml(t("errorLoad")) + '</td></tr>';
      throw err;
    }
  }

  function showBackgroundRefreshBanner(maxPerUsage) {
    const banner = document.getElementById("background-refresh-banner");
    if (!banner) return;
    const msg = banner.querySelector(".background-refresh-msg");
    const done = banner.querySelector(".background-refresh-done");
    if (msg) msg.textContent = "Mise à jour Hugging Face en arrière-plan (54 × " + maxPerUsage + ")…";
    if (done) { done.hidden = true; done.textContent = ""; }
    banner.hidden = false;
  }

  function hideBackgroundRefreshBanner(success, failureMessage) {
    const banner = document.getElementById("background-refresh-banner");
    if (!banner) return;
    const msg = banner.querySelector(".background-refresh-msg");
    const done = banner.querySelector(".background-refresh-done");
    if (success && done) {
      done.textContent = "Mise à jour terminée. Liste actualisée.";
      done.hidden = false;
      if (msg) msg.hidden = true;
      setTimeout(() => { banner.hidden = true; if (msg) msg.hidden = false; }, 3000);
    } else if (failureMessage && done) {
      done.textContent = failureMessage;
      done.hidden = false;
      if (msg) msg.hidden = true;
      setTimeout(() => { banner.hidden = true; if (msg) msg.hidden = false; }, 6000);
    } else {
      banner.hidden = true;
    }
  }

  let refreshPollId = null;

  function clearRefreshPoll() {
    if (refreshPollId != null) {
      clearInterval(refreshPollId);
      refreshPollId = null;
    }
  }

  /** Mise à jour en arrière-plan : ne bloque pas l'UI. Polling pour voir le nouveau total même si le POST timeout. */
  function refreshThenLoadModelsInBackground() {
    const maxPerUsage = (el.maxModelsHf && el.maxModelsHf.value) ? String(el.maxModelsHf.value).trim() : "20";
    const initialCount = models.length;
    const initialLastUpdated = lastModelsUpdateIso || "";
    showBackgroundRefreshBanner(maxPerUsage);
    clearRefreshPoll();
    const pollStart = Date.now();
    refreshPollId = setInterval(() => {
      if (Date.now() - pollStart > REFRESH_POLL_MAX_MINUTES * 60 * 1000) {
        clearRefreshPoll();
        return;
      }
      fetch(`${API}/models`, { method: "GET" })
        .then((res) => res.ok ? res.json() : null)
        .then((data) => {
          if (!data || !data.models) return;
          const count = data.models.length;
          const updated = data.last_updated || "";
          if (count > initialCount || (updated && updated !== initialLastUpdated)) {
            clearRefreshPoll();
            applyApiResponse(data);
            hideBackgroundRefreshBanner(true);
          }
        })
        .catch(() => {});
    }, REFRESH_POLL_INTERVAL_MS);

    const base = (typeof window !== "undefined" && window.location && window.location.origin)
      ? window.location.origin + "/api/refresh"
      : "/api/refresh";
    const url = base + "?max_models=" + encodeURIComponent(maxPerUsage);
    const controller = new AbortController();
    const to = setTimeout(() => controller.abort(), REFRESH_TIMEOUT_MS);
    fetch(url, { method: "POST", signal: controller.signal })
      .then((res) => {
        if (!res.ok && res.status === 404) return fetch(url, { method: "GET", signal: controller.signal });
        return res;
      })
      .then((res) => {
        clearTimeout(to);
        return res.headers.get("content-type") && res.headers.get("content-type").includes("application/json") ? res.json() : { ok: false, message: "Réponse non JSON" };
      })
      .then((data) => {
        if (data && data.ok) {
          clearRefreshPoll();
          if (data.last_updated) setLastUpdateText(data.last_updated);
          fetchFullModels()
            .then(() => hideBackgroundRefreshBanner(true))
            .catch(() => hideBackgroundRefreshBanner(true));
          return;
        }
        clearRefreshPoll();
        const failureMsg = (data && data.message) ? "Mise à jour non appliquée : " + data.message : "Mise à jour non appliquée.";
        hideBackgroundRefreshBanner(false, failureMsg);
      })
      .catch((err) => {
        clearTimeout(to);
        clearRefreshPoll();
        hideBackgroundRefreshBanner(false, "Erreur : " + (err.message || "réseau ou timeout"));
      });
  }

  /** Lance la mise à jour HF en mode bloquant (bouton « Mise à jour des modèles »). */
  async function refreshThenLoadModels() {
    const maxPerUsage = (el.maxModelsHf && el.maxModelsHf.value) ? String(el.maxModelsHf.value).trim() : "20";
    if (el.modelsTbody) el.modelsTbody.innerHTML = '<tr><td colspan="11" class="loading loading-refresh"><span class="loading-refresh-msg">Récupération 54 × ' + escapeHtml(maxPerUsage) + ' modèles depuis Hugging Face…</span> <span class="loading-refresh-sub">(plusieurs minutes)</span></td></tr>';
    const base = (typeof window !== "undefined" && window.location && window.location.origin)
      ? window.location.origin + "/api/refresh"
      : "/api/refresh";
    const url = base + "?max_models=" + encodeURIComponent(maxPerUsage);
    const controller = new AbortController();
    const to = setTimeout(() => controller.abort(), REFRESH_TIMEOUT_MS);
    try {
      let res = await fetch(url, { method: "POST", signal: controller.signal });
      if (!res.ok && res.status === 404) res = await fetch(url, { method: "GET", signal: controller.signal });
      clearTimeout(to);
      const data = res.headers.get("content-type") && res.headers.get("content-type").includes("application/json") ? await res.json() : { ok: false };
      if (data.ok) {
        await fetchFullModels();
        if (data.last_updated) setLastUpdateText(data.last_updated);
      } else {
        await fetchFullModels();
      }
    } catch (err) {
      clearTimeout(to);
      if (el.modelsTbody) el.modelsTbody.innerHTML = '<tr><td colspan="11" class="loading">Timeout ou erreur. Chargement des données locales…</td></tr>';
      await fetchFullModels().catch(() => {});
    }
  }

  async function fetchModels() {
    const cfg = currentApiFilters();
    const params = new URLSearchParams();
    if (cfg.minFit) params.set("min_fit", cfg.minFit);
    if (cfg.maxParams != null) params.set("max_params", String(cfg.maxParams));
    if (cfg.minContext != null) params.set("min_context", String(cfg.minContext));
    if (cfg.limit != null) params.set("limit", String(cfg.limit));
    if (currentScenario === "coding") params.set("use_case", "code");
    if (currentScenario === "chat") params.set("use_case", "chat");
    if (currentScenario === "reasoning") params.set("use_case", "reason");
    if (currentScenario === "edge") params.set("use_case", "edge");
    const url = `${API}/recommend?${params.toString()}`;
    const controller = new AbortController();
    const to = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    try {
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(to);
      if (!res.ok) throw new Error(res.statusText);
      const data = await res.json();
      if (!data.models || data.models.length === 0) {
        return fetchFullModels();
      }
      applyApiResponse(data);
    } catch (err) {
      clearTimeout(to);
      throw err;
    }
  }

  function renderUsageLegend() {
    const container = document.getElementById("usage-legend-items");
    if (!container) return;
    container.innerHTML = PIPELINE_USAGES.map(
      (item) => `<span class="usage-legend-item"><span class="usage-legend-icon">${item.icon}</span> ${escapeHtml(item.label)}</span>`
    ).join("");
  }

  function renderUsageFilterOptions() {
    const sel = document.getElementById("filter-usage");
    if (!sel) return;
    sel.innerHTML =
      '<option value="">' + escapeHtml(t("all")) + '</option>' +
      PIPELINE_USAGES.map(
        (p) => `<option value="${escapeHtml(p.value)}">${p.icon} ${escapeHtml(p.label)}</option>`
      ).join("");
  }

  function exportFile(format) {
    const url = `/api/export/${format}`;
    const a = document.createElement("a");
    a.href = url;
    a.download = `df_modelfit_export.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function renderCompareTable() {
    if (!el.compareDetailTable || !el.compareTableWrap) return;
    if (!selectedModels.length) {
      el.compareTableWrap.hidden = true;
      return;
    }
    el.compareTableWrap.hidden = false;
    const metrics = [
      { key: "score", label: "Score global" },
      { key: "score_quality", label: t("chartQuality") },
      { key: "score_speed", label: t("chartSpeed") },
      { key: "score_fit", label: t("chartFit") },
      { key: "score_context", label: t("chartContext") },
      { key: "mem_requise_gb", label: t("thMem") + " (Go)" },
      { key: "utilisation_pct", label: "Utilisation (%)" },
      { key: "estimated_tps", label: "tok/s (est.)" },
      { key: "eco_level", label: "Énergie" },
      { key: "fit_level", label: t("thFit") },
      { key: "mode", label: t("thMode") },
    ];
    let html = "<thead><tr><th>" + escapeHtml(t("compareMetric")) + "</th>";
    selectedModels.forEach(function(row) {
      const name = (row.model && row.model.name) || "?";
      html += "<th>" + escapeHtml(name) + "</th>";
    });
    html += "</tr></thead><tbody>";
    metrics.forEach(function(m) {
      html += "<tr><td class='metric-label'>" + escapeHtml(m.label) + "</td>";
      selectedModels.forEach(function(row) {
        let val = row[m.key];
        if (val == null && row.model) val = row.model[m.key];
        var cls = m.key === 'score' ? scoreColorClass(val) : '';
        html += "<td" + (cls ? " class='" + cls + "'" : "") + ">" + escapeHtml(String(val != null ? val : "—")) + "</td>";
      });
      html += "</tr>";
    });
    html += "</tbody>";
    el.compareDetailTable.innerHTML = html;
  }

  function toggleCustomProfile() {
    if (!el.customPanel) return;
    el.customPanel.hidden = !el.customPanel.hidden;
  }

  async function applyCustomProfile() {
    const ram = parseFloat((el.customRam && el.customRam.value) || "32");
    const cores = parseInt((el.customCores && el.customCores.value) || "8", 10);
    const vramVal = (el.customVram && el.customVram.value) ? parseFloat(el.customVram.value) : null;
    const backend = (el.customBackend && el.customBackend.value) || "cpu";
    const body = {
      total_ram_gb: ram,
      cpu_cores: cores,
      gpu_vram_gb: vramVal && vramVal > 0 ? vramVal : null,
      backend: vramVal && vramVal > 0 ? backend : "cpu",
    };
    try {
      const res = await fetch(API + "/system/custom", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(res.statusText);
      const data = await res.json();
      isCustomProfile = true;
      updateCustomProfileBadge();
      applyApiResponse(data);
    } catch (err) {
      showToast("Erreur : " + (err.message || err), "error");
    }
  }

  async function resetCustomProfile() {
    isCustomProfile = false;
    updateCustomProfileBadge();
    if (el.customPanel) el.customPanel.hidden = true;
    await fetchFullModels().catch(function() {});
  }

  async function loadChangelog() {
    try {
      const res = await fetch(API + "/changelog");
      if (!res.ok) return;
      const data = await res.json();
      if (!data.entries || !data.entries.length) {
        if (el.changelogCard) el.changelogCard.hidden = true;
        return;
      }
      if (el.changelogCard) el.changelogCard.hidden = false;
      if (el.changelogList) {
        el.changelogList.innerHTML = data.entries.map(function(entry) {
          const badge = entry.status === "new"
            ? '<span class="status-badge status-new">' + escapeHtml(t("statusNew")) + '</span>'
            : '<span class="status-badge status-updated">' + escapeHtml(t("statusUpdated")) + '</span>';
          return '<div class="changelog-entry">' +
            badge + ' ' +
            '<span class="changelog-name">' + escapeHtml(entry.name) + '</span>' +
            ' <span class="changelog-meta">' + escapeHtml(entry.provider) + ' · ' + escapeHtml(entry.parameter_count || "") + '</span>' +
            '</div>';
        }).join("");
      }
    } catch (_) {
      if (el.changelogCard) el.changelogCard.hidden = true;
    }
  }

  // ===== Toast notification system =====
  function showToast(msg, type) {
    type = type || 'info';
    var container = document.getElementById('toast-container');
    if (!container) return;
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.setAttribute('role', 'status');
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(function() {
      toast.classList.add('toast-hide');
      setTimeout(function() { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
    }, 3500);
  }

  // ===== Export feedback =====
  function exportFileWithFeedback(format, btnEl) {
    exportFile(format);
    if (!btnEl) return;
    var orig = btnEl.textContent;
    btnEl.textContent = 'Downloaded ✓';
    setTimeout(function() { btnEl.textContent = orig; }, 1500);
  }

  // ===== Fit distribution rendering =====
  function renderFitDistribution() {
    var bar = document.getElementById('fit-distribution');
    var legend = document.getElementById('fit-distribution-legend');
    if (!bar || !legend) return;
    if (!models.length) { bar.innerHTML = ''; legend.innerHTML = ''; return; }
    var counts = { parfait: 0, bon: 0, marginal: 0, trop_juste: 0 };
    models.forEach(function(r) { if (counts.hasOwnProperty(r.fit_level)) counts[r.fit_level]++; });
    var total = models.length;
    var segments = [
      { key: 'parfait', cls: 'fit-seg-parfait', color: 'var(--fit-parfait)', label: t('parfait') },
      { key: 'bon', cls: 'fit-seg-bon', color: 'var(--fit-bon)', label: t('bon') },
      { key: 'marginal', cls: 'fit-seg-marginal', color: 'var(--fit-marginal)', label: t('marginal') },
      { key: 'trop_juste', cls: 'fit-seg-trop', color: 'var(--fit-trop)', label: t('trop_juste') }
    ];
    bar.innerHTML = segments.map(function(s) {
      var pct = total > 0 ? (counts[s.key] / total * 100) : 0;
      return '<div class="fit-seg ' + s.cls + '" style="width:' + pct.toFixed(1) + '%" title="' + escapeHtml(s.label) + ': ' + counts[s.key] + '"></div>';
    }).join('');
    legend.innerHTML = segments.map(function(s) {
      return '<span><span class="dot" style="background:' + s.color + '"></span>' + escapeHtml(s.label) + ': ' + counts[s.key] + '</span>';
    }).join('');
  }

  // ===== Score color function =====
  function scoreColorClass(val) {
    var n = parseFloat(val);
    if (isNaN(n)) return '';
    if (n >= 70) return 'score-green';
    if (n >= 40) return 'score-yellow';
    return 'score-red';
  }

  // ===== Compact mode =====
  var isCompactMode = false;
  function toggleCompactMode() {
    isCompactMode = !isCompactMode;
    var modelsCard = document.querySelector('.models.card');
    if (modelsCard) modelsCard.classList.toggle('compact-mode', isCompactMode);
    var btn = document.getElementById('btn-compact');
    if (btn) btn.textContent = isCompactMode ? '⊞ Détaillé' : '⊟ Compact';
  }

  // ===== Custom profile badge =====
  function updateCustomProfileBadge() {
    var badge = document.getElementById('custom-profile-badge');
    if (!badge) return;
    badge.classList.toggle('visible', isCustomProfile);
  }

  // ===== Search autocomplete =====
  function renderSearchAutocomplete(query) {
    var list = document.getElementById('search-autocomplete-list');
    var input = document.getElementById('search');
    if (!list || !input) return;
    if (!query || query.length < 1) {
      list.classList.remove('open');
      input.setAttribute('aria-expanded', 'false');
      return;
    }
    var q = query.toLowerCase();
    var matches = [];
    for (var i = 0; i < models.length && matches.length < 5; i++) {
      var name = (models[i].model && models[i].model.name) || '';
      if (name.toLowerCase().includes(q) && matches.indexOf(name) === -1) {
        matches.push(name);
      }
    }
    if (!matches.length) {
      list.classList.remove('open');
      input.setAttribute('aria-expanded', 'false');
      return;
    }
    list.innerHTML = matches.map(function(m, idx) {
      return '<div class="search-autocomplete-item" role="option" data-value="' + escapeHtml(m) + '">' + escapeHtml(m) + '</div>';
    }).join('');
    list.classList.add('open');
    input.setAttribute('aria-expanded', 'true');
  }

  function closeAutocomplete() {
    var list = document.getElementById('search-autocomplete-list');
    var input = document.getElementById('search');
    if (list) list.classList.remove('open');
    if (input) input.setAttribute('aria-expanded', 'false');
  }

  // ===== Favorites system =====
  var FAVORITES_KEY = 'df_modelfit_favorites_v1';
  function loadFavorites() {
    try {
      var raw = localStorage.getItem(FAVORITES_KEY);
      if (!raw) return [];
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) { return []; }
  }
  function saveFavorites(favs) {
    try { localStorage.setItem(FAVORITES_KEY, JSON.stringify(favs)); } catch (_) {}
  }
  function toggleFavorite(modelName) {
    var favs = loadFavorites();
    var idx = favs.indexOf(modelName);
    if (idx >= 0) favs.splice(idx, 1);
    else favs.push(modelName);
    saveFavorites(favs);
    return favs;
  }
  function isFavorite(modelName) {
    return loadFavorites().indexOf(modelName) >= 0;
  }

  // ===== Scroll-to-top button =====
  function initScrollTopButton() {
    var btn = document.getElementById('scroll-top-btn');
    if (!btn) return;
    window.addEventListener('scroll', function() {
      btn.classList.toggle('visible', window.scrollY > 400);
    });
    btn.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ===== Row tooltip =====
  var tooltipTimeout = null;
  function initRowTooltip() {
    var tooltip = document.getElementById('row-tooltip');
    if (!tooltip || !el.modelsTbody) return;
    el.modelsTbody.addEventListener('mouseover', function(e) {
      var row = e.target.closest('tr[data-row-id]');
      if (!row) return;
      clearTimeout(tooltipTimeout);
      var rowId = parseInt(row.getAttribute('data-row-id'), 10);
      var data = models.find(function(m) { return (m._id ?? m.model.name) === rowId; });
      if (!data) return;
      var tps = data.estimated_tps != null ? data.estimated_tps + ' tok/s' : '—';
      var eco = data.eco_level || '—';
      var mem = data.mem_requise_gb != null ? data.mem_requise_gb + ' Go' : '—';
      tooltip.textContent = 'tok/s: ' + tps + ' | Énergie: ' + eco + ' | Mém: ' + mem;
      tooltip.classList.add('visible');
      var rect = row.getBoundingClientRect();
      tooltip.style.top = (rect.bottom + window.scrollY + 4) + 'px';
      tooltip.style.left = (rect.left + window.scrollX) + 'px';
    });
    el.modelsTbody.addEventListener('mouseout', function(e) {
      var row = e.target.closest('tr[data-row-id]');
      if (!row) return;
      tooltipTimeout = setTimeout(function() {
        tooltip.classList.remove('visible');
      }, 150);
    });
  }

  // ── Runtimes / Local AI management ─────────────────────────────────
  var localModelsCache = [];
  var localMatchedCache = {};

  async function loadRuntimes() {
    var statusEl = document.getElementById('runtimes-status');
    if (!statusEl) return;
    try {
      var res = await fetch(API + '/runtimes');
      if (!res.ok) throw new Error(res.statusText);
      var data = await res.json();
      renderRuntimesStatus(data.runtimes);
      localModelsCache = data.local_models || [];
      renderLocalModels(localModelsCache);
      refreshLocalMatches();
    } catch (err) {
      statusEl.innerHTML = '<div class="runtime-card"><span class="runtime-card-name">Détection impossible</span><span class="runtime-card-error">' + escapeHtml(err.message) + '</span></div>';
    }
  }

  function renderRuntimesStatus(runtimes) {
    var statusEl = document.getElementById('runtimes-status');
    if (!statusEl || !runtimes) return;
    statusEl.innerHTML = runtimes.map(function(rt) {
      var dotClass = rt.running ? 'running' : (rt.installed ? 'installed' : 'not-found');
      var statusLabel = rt.running ? (currentLang === 'en' ? 'Running' : 'En cours') : (rt.installed ? (currentLang === 'en' ? 'Installed (stopped)' : 'Installé (arrêté)') : (currentLang === 'en' ? 'Not found' : 'Non trouvé'));
      var versionText = rt.version ? 'v' + escapeHtml(rt.version) : '';
      var modelsText = rt.running ? (rt.models_count + (currentLang === 'en' ? ' model(s)' : ' modèle(s)')) : '';
      var metaParts = [statusLabel, versionText, modelsText].filter(Boolean).join(' · ');
      var errorHtml = rt.error ? '<span class="runtime-card-error">' + escapeHtml(rt.error) + '</span>' : '';
      return '<div class="runtime-card">' +
        '<div class="runtime-card-header"><span class="runtime-card-name">' + escapeHtml(rt.name) + '</span><span class="runtime-status-dot ' + dotClass + '" title="' + escapeHtml(statusLabel) + '"></span></div>' +
        '<span class="runtime-card-meta">' + escapeHtml(metaParts) + '</span>' +
        errorHtml +
        '</div>';
    }).join('');
  }

  function renderLocalModels(models) {
    var section = document.getElementById('local-models-section');
    var tbody = document.getElementById('local-models-tbody');
    var countEl = document.getElementById('local-models-count');
    if (!section || !tbody) return;
    if (!models || models.length === 0) {
      section.hidden = true;
      return;
    }
    section.hidden = false;
    if (countEl) countEl.textContent = String(models.length);
    tbody.innerHTML = models.map(function(m) {
      var sizeText = m.size_gb != null ? m.size_gb + ' Go' : '—';
      return '<tr>' +
        '<td class="mono">' + escapeHtml(m.name) + '</td>' +
        '<td>' + escapeHtml(m.runtime) + '</td>' +
        '<td>' + escapeHtml(sizeText) + '</td>' +
        '<td>' + escapeHtml(m.quantization || '—') + '</td>' +
        '<td>' + escapeHtml(m.family || m.parameter_size || '—') + '</td>' +
        '<td><div class="btn-action-group">' +
          '<button type="button" class="btn-action" onclick="window._dfPullModel(\'' + escapeHtml(m.name) + '\')" title="Mettre à jour">🔄</button>' +
          '<button type="button" class="btn-action btn-danger" onclick="window._dfDeleteModel(\'' + escapeHtml(m.name) + '\')" title="Supprimer">🗑️</button>' +
        '</div></td>' +
        '</tr>';
    }).join('');
  }

  async function refreshLocalMatches() {
    try {
      var res = await fetch(API + '/runtimes/models');
      if (!res.ok) return;
      var data = await res.json();
      localMatchedCache = data.matched || {};
    } catch (_) {}
  }

  function isModelInstalledLocally(modelName) {
    if (!modelName) return false;
    if (localMatchedCache[modelName]) return true;
    var lower = modelName.toLowerCase();
    var short = lower.split('/').pop();
    return localModelsCache.some(function(lm) {
      var ln = lm.name.toLowerCase().split(':')[0];
      return ln === short || lower.includes(ln) || ln.includes(short);
    });
  }

  async function installModel(name) {
    if (!name) return;
    var progress = document.getElementById('install-progress');
    var progressText = progress ? progress.querySelector('.install-progress-text') : null;
    if (progress) progress.hidden = false;
    if (progressText) progressText.textContent = (currentLang === 'en' ? 'Installing ' : 'Installation de ') + name + '…';
    if (typeof showToast === 'function') showToast((currentLang === 'en' ? 'Installing ' : 'Installation de ') + name + '…', 'info');
    try {
      var res = await fetch(API + '/runtimes/install', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: name}),
      });
      var data = await res.json();
      if (data.ok) {
        if (typeof showToast === 'function') showToast(data.message || (name + ' installé !'), 'success');
        await loadRuntimes();
      } else {
        if (typeof showToast === 'function') showToast(data.message || 'Échec', 'error');
      }
    } catch (err) {
      if (typeof showToast === 'function') showToast('Erreur : ' + (err.message || err), 'error');
    } finally {
      if (progress) progress.hidden = true;
    }
  }

  async function deleteModel(name) {
    if (!name) return;
    var confirmMsg = currentLang === 'en'
      ? 'Delete model "' + name + '" from Ollama?'
      : 'Supprimer le modèle « ' + name + ' » d\'Ollama ?';
    if (!confirm(confirmMsg)) return;
    try {
      var res = await fetch(API + '/runtimes/delete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: name}),
      });
      var data = await res.json();
      if (data.ok) {
        if (typeof showToast === 'function') showToast(data.message || (name + ' supprimé.'), 'success');
        await loadRuntimes();
      } else {
        if (typeof showToast === 'function') showToast(data.message || 'Échec', 'error');
      }
    } catch (err) {
      if (typeof showToast === 'function') showToast('Erreur : ' + (err.message || err), 'error');
    }
  }

  window._dfPullModel = function(n) { installModel(n); };
  window._dfDeleteModel = function(n) { deleteModel(n); };

  // ── Chat Panel ────────────────────────────────────────────────────
  var CONVOS_KEY = 'df_modelfit_conversations_v2';
  var chatConversations = [];
  var currentConversationId = null;
  var chatModels = [];
  var chatPresets = {};
  var chatOptions = {
    temperature: 0.7, top_p: 0.9, top_k: 40,
    num_predict: 2048, repeat_penalty: 1.1, num_ctx: 4096, seed: 0
  };
  var chatStreaming = false;
  var chatAbortController = null;
  var chatAttachedImage = null;
  var chatLastStats = null;

  function initChat() {
    var panel = document.getElementById('chat-panel');
    var toggle = document.getElementById('btn-chat-toggle');
    var closeBtn = document.getElementById('btn-chat-close');
    var form = document.getElementById('chat-input-form');
    var input = document.getElementById('chat-input');
    var modelSel = document.getElementById('chat-model-select');

    if (toggle) toggle.addEventListener('click', function() {
      if (panel) {
        panel.classList.toggle('chat-panel-open');
        if (panel.classList.contains('chat-panel-open')) {
          loadChatModels();
          if (input) input.focus();
        }
      }
    });
    if (closeBtn && panel) closeBtn.addEventListener('click', function() {
      panel.classList.remove('chat-panel-open');
    });

    if (modelSel) modelSel.addEventListener('change', onModelChange);

    if (form) form.addEventListener('submit', function(e) {
      e.preventDefault();
      sendChatMessage();
    });

    if (input) {
      input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendChatMessage();
        }
      });
      input.addEventListener('input', function() {
        input.style.height = 'auto';
        var maxH = parseFloat(getComputedStyle(input).lineHeight) * 6;
        input.style.height = Math.min(input.scrollHeight, maxH) + 'px';
        updateTokenEstimate();
      });
    }

    var settingsBtn = document.getElementById('btn-chat-settings-toggle');
    if (settingsBtn) settingsBtn.addEventListener('click', toggleSettings);

    var resetBtn = document.getElementById('btn-chat-reset-defaults');
    if (resetBtn) resetBtn.addEventListener('click', resetToModelDefaults);

    var newBtn = document.getElementById('btn-chat-new');
    if (newBtn) newBtn.addEventListener('click', newConversation);

    var convosBtn = document.getElementById('btn-chat-convos-toggle');
    if (convosBtn) convosBtn.addEventListener('click', function() {
      var list = document.getElementById('chat-conversations-list');
      if (list) list.classList.toggle('chat-convos-open');
    });

    var stopBtn = document.getElementById('btn-chat-stop');
    if (stopBtn) stopBtn.addEventListener('click', stopGeneration);

    var regenBtn = document.getElementById('btn-chat-regenerate');
    if (regenBtn) regenBtn.addEventListener('click', regenerateLastResponse);

    var screenshotBtn = document.getElementById('btn-chat-screenshot');
    if (screenshotBtn) screenshotBtn.addEventListener('click', captureScreen);

    var fileInput = document.getElementById('chat-file-input');
    if (fileInput) fileInput.addEventListener('change', attachImage);

    var removeImgBtn = document.getElementById('btn-chat-remove-image');
    if (removeImgBtn) removeImgBtn.addEventListener('click', removeAttachedImage);

    var presetSel = document.getElementById('chat-preset-select');
    if (presetSel) presetSel.addEventListener('change', function() {
      selectPreset(presetSel.value);
    });

    ['chat-temperature', 'chat-top-p', 'chat-repeat-penalty'].forEach(function(id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener('input', updateSliderValues);
    });

    var dropZone = document.getElementById('chat-drop-zone');
    var messagesEl = document.getElementById('chat-messages');
    [dropZone, messagesEl].forEach(function(zone) {
      if (!zone) return;
      zone.addEventListener('dragover', function(e) {
        e.preventDefault();
        if (dropZone) dropZone.classList.add('drag-over');
      });
      zone.addEventListener('dragleave', function() {
        if (dropZone) dropZone.classList.remove('drag-over');
      });
      zone.addEventListener('drop', function(e) {
        e.preventDefault();
        if (dropZone) dropZone.classList.remove('drag-over');
        var files = e.dataTransfer && e.dataTransfer.files;
        if (files && files.length > 0) handleImageFile(files[0]);
      });
    });

    loadConversations();
    if (!chatConversations.length) newConversation();
    else {
      currentConversationId = chatConversations[0].id;
      renderChatMessages();
      renderConversationsList();
    }
    loadPresets();
  }

  function loadChatModels() {
    var modelSel = document.getElementById('chat-model-select');
    if (!modelSel) return;
    fetch(API + '/chat/models')
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (!data.available) {
          modelSel.innerHTML = '<option value="">' + escapeHtml(t('chatOllamaNotRunning')) + '</option>';
          chatModels = [];
          return;
        }
        chatModels = data.models || [];
        if (!chatModels.length) {
          modelSel.innerHTML = '<option value="">' + escapeHtml(t('chatNoModels')) + '</option>';
          return;
        }
        var prev = modelSel.value;
        var opts = '<option value="">' + escapeHtml(t('chatSelectModel')) + '</option>';
        chatModels.forEach(function(m) {
          var sizeTag = m.size_gb ? ' (' + m.size_gb + ' Go)' : '';
          opts += '<option value="' + escapeHtml(m.name) + '">' +
            escapeHtml(m.name) + sizeTag + '</option>';
        });
        modelSel.innerHTML = opts;
        var conv = getCurrentConversation();
        if (conv && conv.model) modelSel.value = conv.model;
        else if (prev) modelSel.value = prev;
        onModelChange();
      })
      .catch(function() {
        modelSel.innerHTML = '<option value="">' + escapeHtml(t('chatOllamaNotRunning')) + '</option>';
        chatModels = [];
      });
  }

  function getSelectedModel() {
    var found = null;
    var modelSel = document.getElementById('chat-model-select');
    if (!modelSel || !modelSel.value) return null;
    chatModels.forEach(function(m) {
      if (m.name === modelSel.value) found = m;
    });
    return found;
  }

  function onModelChange() {
    var modelSel = document.getElementById('chat-model-select');
    var input = document.getElementById('chat-input');
    var sendBtn = document.getElementById('btn-chat-send');
    var enabled = !!(modelSel && modelSel.value);
    if (input) input.disabled = !enabled;
    if (sendBtn) sendBtn.disabled = !enabled;

    var m = getSelectedModel();
    var badgesEl = document.getElementById('chat-model-badges');
    var infoEl = document.getElementById('chat-model-info');
    var imageZone = document.getElementById('chat-image-zone');

    if (badgesEl) {
      var badges = '';
      if (m && m.supports_vision) badges += '<span class="chat-badge chat-badge-vision">👁️ Vision</span>';
      if (m && m.supports_code) badges += '<span class="chat-badge chat-badge-code">💻 Code</span>';
      badgesEl.innerHTML = badges;
    }
    if (infoEl) {
      if (m) {
        infoEl.textContent = (m.size_gb ? m.size_gb + ' Go' : '') +
          (m.quantization ? ' · ' + m.quantization : '') +
          (m.default_ctx ? ' · ctx ' + m.default_ctx : '');
      } else {
        infoEl.textContent = '';
      }
    }
    if (imageZone) imageZone.hidden = !(m && m.supports_vision);

    if (m && m.defaults) {
      chatOptions.temperature = m.defaults.temperature;
      chatOptions.top_p = m.defaults.top_p;
      chatOptions.top_k = m.defaults.top_k;
      chatOptions.num_predict = m.defaults.num_predict;
      chatOptions.repeat_penalty = m.defaults.repeat_penalty;
      chatOptions.num_ctx = m.defaults.num_ctx;
      chatOptions.seed = m.defaults.seed;
      applyOptionsToUI();
      if (m.defaults.suggested_preset) {
        var presetSel = document.getElementById('chat-preset-select');
        if (presetSel) presetSel.value = m.defaults.suggested_preset;
      }
    }

    var conv = getCurrentConversation();
    if (conv && modelSel) conv.model = modelSel.value;
    saveConversations();
  }

  function loadPresets() {
    fetch(API + '/chat/presets')
      .then(function(res) { return res.json(); })
      .then(function(data) {
        chatPresets = data.presets || {};
      })
      .catch(function() { chatPresets = {}; });
  }

  function selectPreset(key) {
    if (!chatPresets[key]) return;
    var lang = currentLang === 'en' ? 'en' : 'fr';
    var prompt = chatPresets[key][lang] || chatPresets[key].fr || '';
    var ta = document.getElementById('chat-system-prompt');
    if (ta) ta.value = prompt;
  }

  function getSystemPrompt() {
    var ta = document.getElementById('chat-system-prompt');
    if (ta && ta.value.trim()) return ta.value.trim();
    var presetSel = document.getElementById('chat-preset-select');
    var key = (presetSel && presetSel.value) || 'default';
    if (chatPresets[key]) {
      var lang = currentLang === 'en' ? 'en' : 'fr';
      return chatPresets[key][lang] || chatPresets[key].fr || '';
    }
    if (currentLang === 'en') {
      return 'You are a helpful AI assistant integrated into DF Modelfit.';
    }
    return 'Tu es un assistant IA intégré à DF Modelfit.';
  }

  function getCurrentConversation() {
    var conv = null;
    chatConversations.forEach(function(c) {
      if (c.id === currentConversationId) conv = c;
    });
    return conv;
  }

  function sendChatMessage(existingConv) {
    var input = document.getElementById('chat-input');
    var modelSel = document.getElementById('chat-model-select');
    if (!modelSel || chatStreaming) return;

    var conv = existingConv || getCurrentConversation();

    if (!existingConv) {
      if (!input) return;
      var text = input.value.trim();
      if (!text && !chatAttachedImage) return;
      var model = modelSel.value;
      if (!model) return;

      if (!conv) { newConversation(); conv = getCurrentConversation(); }

      var userMsg = { role: 'user', content: text || '(image)' };
      if (chatAttachedImage) {
        userMsg.images = [chatAttachedImage];
        userMsg._hasImage = true;
      }
      conv.messages.push(userMsg);
      if (conv.messages.length === 1) {
        conv.title = text.slice(0, 50) || 'Image';
      }
      conv.model = model;
      renderChatMessages();
      input.value = '';
      input.style.height = 'auto';
      removeAttachedImage();
      updateTokenEstimate();
    }

    var model = modelSel.value || (conv && conv.model);
    if (!model) return;

    chatStreaming = true;
    chatAbortController = new AbortController();
    updateChatUI();

    var systemPrompt = getSystemPrompt();
    var messagesPayload = conv.messages.filter(function(m) {
      return m.role === 'user' || m.role === 'assistant';
    }).map(function(m) {
      var entry = { role: m.role, content: m.content };
      if (m.images) entry.images = m.images;
      return entry;
    });

    var opts = {};
    if (chatOptions.temperature !== undefined) opts.temperature = chatOptions.temperature;
    if (chatOptions.top_p !== undefined) opts.top_p = chatOptions.top_p;
    if (chatOptions.top_k !== undefined) opts.top_k = chatOptions.top_k;
    if (chatOptions.num_predict !== undefined) opts.num_predict = chatOptions.num_predict;
    if (chatOptions.repeat_penalty !== undefined) opts.repeat_penalty = chatOptions.repeat_penalty;
    if (chatOptions.num_ctx !== undefined) opts.num_ctx = chatOptions.num_ctx;
    if (chatOptions.seed && chatOptions.seed > 0) opts.seed = chatOptions.seed;

    fetch(API + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: chatAbortController.signal,
      body: JSON.stringify({
        model: model,
        messages: messagesPayload,
        system_prompt: systemPrompt,
        options: opts,
      }),
    })
    .then(function(res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.body.getReader();
    })
    .then(function(reader) {
      var decoder = new TextDecoder();
      var assistantMsg = { role: 'assistant', content: '' };
      conv.messages.push(assistantMsg);
      chatLastStats = null;
      renderChatMessages();

      function read() {
        return reader.read().then(function(result) {
          if (result.done) {
            chatStreaming = false;
            chatAbortController = null;
            updateChatUI();
            saveConversations();
            renderChatMessages();
            return;
          }
          var text = decoder.decode(result.value, { stream: true });
          var lines = text.split('\n');
          lines.forEach(function(line) {
            line = line.trim();
            if (!line || line === 'data: [DONE]') return;
            if (line.startsWith('data: ')) {
              try {
                var chunk = JSON.parse(line.slice(6));
                if (chunk.error) {
                  assistantMsg.content += '\n[' + t('chatError') + (chunk.detail || t('chatErrorUnknown')) + ']';
                } else if (chunk.message && chunk.message.content) {
                  assistantMsg.content += chunk.message.content;
                }
                if (chunk.done) {
                  updateGenerationStats(chunk);
                }
                renderChatMessages();
              } catch (_) {}
            }
          });
          return read();
        });
      }
      return read();
    })
    .catch(function(err) {
      if (err.name === 'AbortError') {
        chatStreaming = false;
        chatAbortController = null;
        updateChatUI();
        renderChatMessages();
        return;
      }
      conv.messages.push({
        role: 'error',
        content: t('chatError') + (err.message || t('chatErrorCheck')),
      });
      chatStreaming = false;
      chatAbortController = null;
      updateChatUI();
      renderChatMessages();
    });
  }

  function stopGeneration() {
    if (chatAbortController) {
      chatAbortController.abort();
    }
  }

  function regenerateLastResponse() {
    var conv = getCurrentConversation();
    if (!conv || !conv.messages.length) return;
    while (conv.messages.length > 0 && conv.messages[conv.messages.length - 1].role !== 'user') {
      conv.messages.pop();
    }
    chatLastStats = null;
    renderChatMessages();
    if (conv.messages.length > 0) {
      var input = document.getElementById('chat-input');
      if (input) input.value = '';
      sendChatMessage(conv);
    }
  }

  function renderChatMessages() {
    var container = document.getElementById('chat-messages');
    if (!container) return;
    var conv = getCurrentConversation();
    var messages = conv ? conv.messages : [];

    if (!messages.length) {
      container.innerHTML =
        '<div class="chat-welcome">' +
          '<p><strong>' + escapeHtml(t('chatWelcomeTitle')) + '</strong></p>' +
          '<p class="chat-welcome-sub">' + escapeHtml(t('chatWelcomeSub')) + '</p>' +
        '</div>';
      return;
    }

    var html = messages.map(function(msg, idx) {
      if (msg.role === 'error') {
        return '<div class="chat-bubble chat-bubble-error">' + escapeHtml(msg.content) + '</div>';
      }
      var cls = msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant';
      var imgHtml = '';
      if (msg._hasImage && msg.images && msg.images[0]) {
        imgHtml = '<img class="chat-bubble-img" src="data:image/png;base64,' + msg.images[0] + '" alt="Image" />';
      }
      var contentHtml = msg.role === 'assistant'
        ? formatMarkdown(msg.content)
        : escapeHtml(msg.content);
      var bubble = '<div class="chat-bubble ' + cls + '">' + imgHtml + contentHtml + '</div>';
      if (msg.role === 'assistant' && idx === messages.length - 1 && chatLastStats && !chatStreaming) {
        bubble += '<div class="chat-stats-pill">' + escapeHtml(chatLastStats) + '</div>';
      }
      return bubble;
    }).join('');

    if (chatStreaming) {
      html += '<div class="chat-typing">' + escapeHtml(t('chatGenerating')) + '</div>';
    }
    container.innerHTML = html;
    container.scrollTop = container.scrollHeight;
    addCopyButtons();
  }

  function formatMarkdown(text) {
    if (!text) return '';
    var escaped = escapeHtml(text);
    escaped = escaped.replace(/```(\w*)\n?([\s\S]*?)```/g, function(_, lang, code) {
      return '<pre><code>' + code + '</code></pre>';
    });
    escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    escaped = escaped.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    var lines = escaped.split('\n');
    var result = [];
    var i = 0;
    while (i < lines.length) {
      var ulMatch = lines[i].match(/^[-*]\s+(.+)/);
      if (ulMatch) {
        var items = [];
        while (i < lines.length && (ulMatch = lines[i].match(/^[-*]\s+(.+)/))) {
          items.push('<li>' + ulMatch[1] + '</li>');
          i++;
        }
        result.push('<ul>' + items.join('') + '</ul>');
        continue;
      }
      var olMatch = lines[i].match(/^\d+\.\s+(.+)/);
      if (olMatch) {
        var items = [];
        while (i < lines.length && (olMatch = lines[i].match(/^\d+\.\s+(.+)/))) {
          items.push('<li>' + olMatch[1] + '</li>');
          i++;
        }
        result.push('<ol>' + items.join('') + '</ol>');
        continue;
      }
      result.push(lines[i]);
      i++;
    }
    escaped = result.join('\n');
    escaped = escaped.replace(/\n/g, '<br>');
    return escaped;
  }

  function addCopyButtons() {
    var pres = document.querySelectorAll('#chat-messages .chat-bubble-assistant pre');
    pres.forEach(function(pre) {
      if (pre.querySelector('.chat-code-copy-btn')) return;
      var btn = document.createElement('button');
      btn.className = 'chat-code-copy-btn';
      btn.textContent = t('chatCopy');
      btn.type = 'button';
      btn.addEventListener('click', function() {
        var code = pre.querySelector('code');
        var txt = code ? code.textContent : pre.textContent;
        navigator.clipboard.writeText(txt).then(function() {
          btn.textContent = t('chatCopied');
          setTimeout(function() { btn.textContent = t('chatCopy'); }, 1500);
        });
      });
      pre.style.position = 'relative';
      pre.appendChild(btn);
    });
  }

  function updateChatUI() {
    var input = document.getElementById('chat-input');
    var sendBtn = document.getElementById('btn-chat-send');
    var stopBtn = document.getElementById('btn-chat-stop');
    var regenBtn = document.getElementById('btn-chat-regenerate');

    if (input) input.disabled = chatStreaming;
    if (sendBtn) sendBtn.hidden = chatStreaming;
    if (sendBtn) sendBtn.disabled = !document.getElementById('chat-model-select').value;
    if (stopBtn) stopBtn.hidden = !chatStreaming;

    var conv = getCurrentConversation();
    var hasAssistant = conv && conv.messages.length > 0 &&
      conv.messages[conv.messages.length - 1].role === 'assistant';
    if (regenBtn) regenBtn.hidden = !hasAssistant || chatStreaming;
  }

  function updateGenerationStats(data) {
    if (!data) return;
    var totalDur = data.total_duration;
    var evalCount = data.eval_count;
    var evalDur = data.eval_duration;
    if (evalCount && evalDur) {
      var tps = (evalCount / (evalDur / 1e9)).toFixed(1);
      var durMs = Math.round((totalDur || evalDur) / 1e6);
      chatLastStats = tps + ' tok/s · ' + evalCount + ' tokens · ' + durMs + 'ms';
    }
  }

  function updateTokenEstimate() {
    var input = document.getElementById('chat-input');
    var el = document.getElementById('chat-token-estimate');
    if (!el || !input) return;
    var text = input.value || '';
    var est = Math.ceil(text.length / 4);
    el.textContent = est > 0 ? '~' + est + ' tokens' : '';
  }

  function captureScreen() {
    if (typeof html2canvas !== 'function') {
      showToast('html2canvas non chargé', 'error');
      return;
    }
    var chatPanel = document.getElementById('chat-panel');
    if (chatPanel) chatPanel.style.visibility = 'hidden';

    html2canvas(document.body, {
      scale: 0.5, useCORS: true, logging: false,
      windowWidth: document.body.scrollWidth,
      windowHeight: document.body.scrollHeight,
    }).then(function(canvas) {
      if (chatPanel) chatPanel.style.visibility = '';
      chatAttachedImage = canvas.toDataURL('image/png').split(',')[1];
      showImagePreview();
      showToast(t('chatScreenCaptured'), 'success');
    }).catch(function(err) {
      if (chatPanel) chatPanel.style.visibility = '';
      showToast('Erreur capture : ' + err.message, 'error');
    });
  }

  function attachImage() {
    var fileInput = document.getElementById('chat-file-input');
    if (!fileInput || !fileInput.files || !fileInput.files[0]) return;
    handleImageFile(fileInput.files[0]);
    fileInput.value = '';
  }

  function handleImageFile(file) {
    if (!file || !file.type.startsWith('image/')) return;
    var reader = new FileReader();
    reader.onload = function(e) {
      chatAttachedImage = e.target.result.split(',')[1];
      showImagePreview();
    };
    reader.readAsDataURL(file);
  }

  function detectImageMime(b64) {
    if (!b64) return 'image/png';
    if (b64.indexOf('/9j/') === 0 || b64.indexOf('/9j/') !== -1 && b64.indexOf('/9j/') < 4) return 'image/jpeg';
    if (b64.indexOf('iVBOR') === 0) return 'image/png';
    if (b64.indexOf('R0lGOD') === 0) return 'image/gif';
    if (b64.indexOf('UklGR') === 0) return 'image/webp';
    return 'image/png';
  }

  function showImagePreview() {
    var preview = document.getElementById('chat-image-preview');
    var img = document.getElementById('chat-preview-img');
    if (preview) preview.hidden = false;
    if (img && chatAttachedImage) {
      var mime = detectImageMime(chatAttachedImage);
      img.src = 'data:' + mime + ';base64,' + chatAttachedImage;
    }
  }

  function removeAttachedImage() {
    chatAttachedImage = null;
    var preview = document.getElementById('chat-image-preview');
    if (preview) preview.hidden = true;
  }

  function newConversation() {
    var conv = {
      id: 'conv_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      title: t('chatNewConv'),
      messages: [],
      createdAt: new Date().toISOString(),
      model: ''
    };
    chatConversations.unshift(conv);
    currentConversationId = conv.id;
    chatLastStats = null;
    saveConversations();
    renderChatMessages();
    renderConversationsList();
    var input = document.getElementById('chat-input');
    if (input) input.focus();
  }

  function switchConversation(id) {
    currentConversationId = id;
    chatLastStats = null;
    renderChatMessages();
    renderConversationsList();
    var conv = getCurrentConversation();
    if (conv && conv.model) {
      var modelSel = document.getElementById('chat-model-select');
      if (modelSel) modelSel.value = conv.model;
      onModelChange();
    }
    updateChatUI();
  }

  function deleteConversation(id) {
    chatConversations = chatConversations.filter(function(c) { return c.id !== id; });
    if (currentConversationId === id) {
      if (chatConversations.length > 0) {
        currentConversationId = chatConversations[0].id;
      } else {
        newConversation();
        return;
      }
    }
    chatLastStats = null;
    saveConversations();
    renderChatMessages();
    renderConversationsList();
    updateChatUI();
  }

  function renderConversationsList() {
    var list = document.getElementById('chat-conversations-list');
    if (!list) return;
    if (!chatConversations.length) {
      list.innerHTML = '<div style="padding:0.5rem 1rem;font-size:0.8rem;color:var(--text-muted)">' + escapeHtml(t('chatNoConversations')) + '</div>';
      return;
    }
    list.innerHTML = chatConversations.map(function(c) {
      var d = new Date(c.createdAt);
      var dateStr = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
      var activeClass = c.id === currentConversationId ? ' active' : '';
      return '<div class="chat-convo-item' + activeClass + '" data-convo-id="' + c.id + '">' +
        '<span class="chat-convo-date">' + escapeHtml(dateStr) + '</span>' +
        '<span class="chat-convo-title">' + escapeHtml(c.title) + '</span>' +
        '<button type="button" class="chat-convo-delete" data-delete-id="' + c.id + '" title="' + escapeHtml(t('chatDeleteConv')) + '">🗑️</button>' +
        '</div>';
    }).join('');

    list.querySelectorAll('.chat-convo-item').forEach(function(item) {
      item.addEventListener('click', function(e) {
        if (e.target.classList.contains('chat-convo-delete')) return;
        switchConversation(item.getAttribute('data-convo-id'));
      });
    });
    list.querySelectorAll('.chat-convo-delete').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        deleteConversation(btn.getAttribute('data-delete-id'));
      });
    });
  }

  function saveConversations() {
    try {
      var toSave = chatConversations.map(function(c) {
        var msgs = c.messages.slice(-20);
        var lastImageIdx = -1;
        for (var i = msgs.length - 1; i >= 0; i--) {
          if (msgs[i].images && msgs[i].images.length > 0) {
            lastImageIdx = i;
            break;
          }
        }
        return {
          id: c.id, title: c.title, createdAt: c.createdAt, model: c.model,
          messages: msgs.map(function(m, idx) {
            var entry = { role: m.role, content: m.content };
            if (m._hasImage) entry._hasImage = true;
            if (m.images && m.images.length > 0 && idx === lastImageIdx) {
              entry.images = m.images;
            }
            return entry;
          })
        };
      }).slice(0, 50);
      localStorage.setItem(CONVOS_KEY, JSON.stringify(toSave));
    } catch (_) {}
  }

  function loadConversations() {
    try {
      var raw = localStorage.getItem(CONVOS_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) chatConversations = parsed;
      }
    } catch (_) {
      chatConversations = [];
    }
  }

  function toggleSettings() {
    var drawer = document.getElementById('chat-settings-drawer');
    if (drawer) drawer.classList.toggle('chat-settings-open');
  }

  function resetToModelDefaults() {
    var m = getSelectedModel();
    if (m && m.defaults) {
      chatOptions.temperature = m.defaults.temperature;
      chatOptions.top_p = m.defaults.top_p;
      chatOptions.top_k = m.defaults.top_k;
      chatOptions.num_predict = m.defaults.num_predict;
      chatOptions.repeat_penalty = m.defaults.repeat_penalty;
      chatOptions.num_ctx = m.defaults.num_ctx;
      chatOptions.seed = m.defaults.seed;
    } else {
      chatOptions = {
        temperature: 0.7, top_p: 0.9, top_k: 40,
        num_predict: 2048, repeat_penalty: 1.1, num_ctx: 4096, seed: 0
      };
    }
    applyOptionsToUI();
    showToast(t('chatResetDone'), 'success');
  }

  function applyOptionsToUI() {
    var el;
    el = document.getElementById('chat-temperature');
    if (el) el.value = chatOptions.temperature;
    el = document.getElementById('chat-top-p');
    if (el) el.value = chatOptions.top_p;
    el = document.getElementById('chat-top-k');
    if (el) el.value = chatOptions.top_k;
    el = document.getElementById('chat-num-predict');
    if (el) el.value = chatOptions.num_predict;
    el = document.getElementById('chat-num-ctx');
    if (el) el.value = chatOptions.num_ctx;
    el = document.getElementById('chat-repeat-penalty');
    if (el) el.value = chatOptions.repeat_penalty;
    el = document.getElementById('chat-seed');
    if (el) el.value = chatOptions.seed;
    updateSliderValues();
  }

  function updateSliderValues() {
    var temp = document.getElementById('chat-temperature');
    var tempVal = document.getElementById('chat-temp-val');
    if (temp && tempVal) {
      tempVal.textContent = parseFloat(temp.value).toFixed(1);
      chatOptions.temperature = parseFloat(temp.value);
    }
    var topp = document.getElementById('chat-top-p');
    var toppVal = document.getElementById('chat-topp-val');
    if (topp && toppVal) {
      toppVal.textContent = parseFloat(topp.value).toFixed(2);
      chatOptions.top_p = parseFloat(topp.value);
    }
    var rp = document.getElementById('chat-repeat-penalty');
    var rpVal = document.getElementById('chat-repeat-val');
    if (rp && rpVal) {
      rpVal.textContent = parseFloat(rp.value).toFixed(2);
      chatOptions.repeat_penalty = parseFloat(rp.value);
    }
    var topk = document.getElementById('chat-top-k');
    if (topk) chatOptions.top_k = parseInt(topk.value) || 40;
    var np = document.getElementById('chat-num-predict');
    if (np) chatOptions.num_predict = parseInt(np.value) || 2048;
    var nc = document.getElementById('chat-num-ctx');
    if (nc) chatOptions.num_ctx = parseInt(nc.value) || 4096;
    var seed = document.getElementById('chat-seed');
    if (seed) chatOptions.seed = parseInt(seed.value) || 0;
  }

  function initRuntimes() {
    var btnRefresh = document.getElementById('btn-refresh-runtimes');
    if (btnRefresh) btnRefresh.addEventListener('click', loadRuntimes);

    var btnInstall = document.getElementById('btn-install-model');
    var inputModel = document.getElementById('install-model-name');
    if (btnInstall && inputModel) {
      btnInstall.addEventListener('click', function() {
        var name = inputModel.value.trim();
        if (name) installModel(name);
      });
      inputModel.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
          var name = inputModel.value.trim();
          if (name) installModel(name);
        }
      });
    }

    document.querySelectorAll('.install-suggestion').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var model = btn.getAttribute('data-model');
        if (inputModel) inputModel.value = model;
        if (model) installModel(model);
      });
    });

    loadRuntimes();
  }

  function init() {
    renderUsageLegend();
    renderUsageFilterOptions();
    loadSettings();
    applyTheme();
    syncThemeButtons();
    applyI18n();
    syncLangButtons();
    renderSystem(system);
    loadHistory();
    renderHistory();
    if (el.modelsTbody) el.modelsTbody.innerHTML = '<tr><td colspan="11" class="loading">' + escapeHtml(t("loadingModels")) + '</td></tr>';
    fetchFullModels()
      .then(() => {
        if (isOlderThanDays(lastModelsUpdateIso, AUTO_REFRESH_IF_OLDER_DAYS)) {
          refreshThenLoadModelsInBackground();
        }
      })
      .catch(async (err) => {
        if (el.modelsTbody) el.modelsTbody.innerHTML = '<tr><td colspan="11" class="loading">' + escapeHtml(err.message) + '. ' + escapeHtml(t("errorLoad")) + '</td></tr>';
        try {
          await fetchModels();
        } catch (_) {
          if (el.systemGrid) el.systemGrid.innerHTML = '<div class="skeleton">' + escapeHtml(t("errorServer")) + '</div>';
          if (el.modelsTbody) el.modelsTbody.innerHTML = '<tr><td colspan="11" class="loading">' + escapeHtml(t("errorModels")) + '</td></tr>';
        }
      });

    const filtersForm = document.getElementById("filters-form");
    if (filtersForm) {
      filtersForm.addEventListener("submit", (e) => {
        e.preventDefault();
        fetchModels().catch(() => {});
      });
    }

    let searchSaveTo = null;
    if (el.search) {
      el.search.addEventListener("input", () => {
        applyFilters();
        if (searchSaveTo) clearTimeout(searchSaveTo);
        searchSaveTo = setTimeout(saveSettings, 400);
      });
      el.search.addEventListener("change", saveSettings);
      el.search.addEventListener("keydown", (e) => {
        if (e.key === "Enter") fetchModels();
      });
    }
    if (el.filterFit) {
      el.filterFit.addEventListener("change", () => { applyFilters(); saveSettings(); });
    }
    if (el.filterUsage) {
      el.filterUsage.addEventListener("change", () => { applyFilters(); saveSettings(); });
    }
    if (el.minFit) el.minFit.addEventListener("change", saveSettings);
    if (el.maxParams) el.maxParams.addEventListener("change", saveSettings);
    if (el.minContext) el.minContext.addEventListener("change", saveSettings);
    if (el.limit) el.limit.addEventListener("change", saveSettings);
    if (el.maxModelsHf) el.maxModelsHf.addEventListener("change", saveSettings);
    if (el.btnReset) el.btnReset.addEventListener("click", () => {
      if (el.search) el.search.value = "";
      if (el.filterFit) el.filterFit.value = "";
      if (el.filterUsage) el.filterUsage.value = "";
      if (el.minFit) el.minFit.value = "marginal";
      if (el.maxParams) el.maxParams.value = "";
      if (el.minContext) el.minContext.value = "";
      if (el.limit) el.limit.value = "20";
      currentScenario = null;
      syncScenarioButtons();
      currentPage = 0;
      fetchFullModels().catch(() => {});
    });
    if (el.btnRefresh) el.btnRefresh.addEventListener("click", () => {
      fetchModels()
        .then(() => saveHistoryEntry())
        .catch(() => {});
    });
    if (el.btnPrev) el.btnPrev.addEventListener("click", () => goToPage(-1));
    if (el.btnNext) el.btnNext.addEventListener("click", () => goToPage(1));

    document.querySelectorAll(".sortable").forEach((th) => {
      th.addEventListener("click", () => {
        const col = th.getAttribute("data-sort");
        if (col) setSort(col);
      });
    });

    if (el.btnHf) {
      el.btnHf.addEventListener("click", async () => {
        el.btnHf.disabled = true;
        el.btnHf.textContent = t("loadingShort");
        const maxModels = (el.maxModelsHf && el.maxModelsHf.value) ? String(el.maxModelsHf.value).trim() : "20";
        const base = (typeof window !== "undefined" && window.location && window.location.origin)
          ? window.location.origin + "/api/refresh"
          : "/api/refresh";
        const url = base + "?max_models=" + encodeURIComponent(maxModels);
        try {
          let res = await fetch(url, { method: "POST" });
          if (!res.ok && res.status === 404) res = await fetch(url, { method: "GET" });
          let data = {};
          const ct = res.headers.get("content-type") || "";
          if (ct.includes("application/json")) {
            try { data = await res.json(); } catch (_) { data = { ok: false, message: "Réponse invalide" }; }
          } else {
            const text = await res.text();
            data = { ok: false, message: "Erreur " + res.status + (text ? ": " + text.slice(0, 200) : "") };
          }
          if (data.ok) {
            await fetchModels();
            if (data.last_updated) setLastUpdateText(data.last_updated);
            el.btnHf.textContent = t("updateModels");
          } else {
            el.btnHf.textContent = t("updateModels");
            showToast(data.message || t("errorUpdateFail"), "error");
          }
        } catch (err) {
          el.btnHf.textContent = t("updateModels");
          showToast(t("errorNetwork"), "error");
        } finally {
          el.btnHf.disabled = false;
          if (el.btnHf.textContent === t("loadingShort")) el.btnHf.textContent = t("updateModels");
        }
      });
    }

    if (el.scenarioButtons && el.scenarioButtons.length) {
      el.scenarioButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
          const scenario = btn.getAttribute("data-scenario");
          currentScenario = scenario || null;
          syncScenarioButtons();
          // Ajuster quelques filtres par défaut selon le scénario
          if (scenario === "coding") {
            if (el.minFit) el.minFit.value = "bon";
            if (el.maxParams) el.maxParams.value = "8";
            if (el.minContext) el.minContext.value = "8192";
          } else if (scenario === "chat") {
            if (el.minFit) el.minFit.value = "marginal";
            if (el.maxParams) el.maxParams.value = "8";
            if (el.minContext) el.minContext.value = "8192";
          } else if (scenario === "reasoning") {
            if (el.minFit) el.minFit.value = "bon";
            if (el.maxParams) el.maxParams.value = "16";
            if (el.minContext) el.minContext.value = "32000";
          } else if (scenario === "edge") {
            if (el.minFit) el.minFit.value = "bon";
            if (el.maxParams) el.maxParams.value = "4";
            if (el.minContext) el.minContext.value = "4096";
          }
          saveSettings();
          fetchModels()
            .then(() => saveHistoryEntry())
            .catch(() => {});
        });
      });
    }

    if (el.historyList) {
      el.historyList.addEventListener("click", (e) => {
        const btn = e.target.closest(".history-entry");
        if (!btn) return;
        const idxAttr = btn.getAttribute("data-history-index");
        const idx = idxAttr != null ? parseInt(idxAttr, 10) : NaN;
        if (!Number.isNaN(idx)) {
          applyHistoryEntry(idx);
        }
      });
    }
    const btnResetHistory = document.getElementById("btn-reset-history");
    if (btnResetHistory) btnResetHistory.addEventListener("click", clearHistory);

    document.querySelectorAll(".btn-lang").forEach((btn) => {
      btn.addEventListener("click", () => {
        const lang = btn.getAttribute("data-lang");
        if (lang !== "fr" && lang !== "en") return;
        currentLang = lang;
        saveSettings();
        applyI18n();
        syncLangButtons();
        renderUsageFilterOptions();
        if (system) renderSystem(system);
        renderHistory();
        applyFilters(false);
        updateChart();
        updateSnippet();
        if (el.lastUpdate && el.lastUpdate.textContent) setLastUpdateText(lastModelsUpdateIso || "");
      });
    });

    document.querySelectorAll(".btn-theme").forEach((btn) => {
      btn.addEventListener("click", () => {
        const theme = btn.getAttribute("data-theme");
        if (theme !== "dark" && theme !== "light") return;
        currentTheme = theme;
        saveSettings();
        applyTheme();
        syncThemeButtons();
      });
    });

    if (el.modelsTbody) {
      el.modelsTbody.addEventListener("click", (e) => {
        const checkbox = e.target.closest(".model-select");
        const rowEl = e.target.closest("tr[data-row-id]");
        if (!rowEl) return;
        const rowIdAttr = rowEl.getAttribute("data-row-id");
        const rowId = rowIdAttr != null ? parseInt(rowIdAttr, 10) : NaN;
        if (Number.isNaN(rowId)) return;
        if (checkbox) {
          toggleSelection(rowId);
        } else {
          // Clic sur la ligne : sélectionner/désélectionner
          toggleSelection(rowId);
        }
      });
    }

    if (el.btnCopySnippet && el.pythonSnippet) {
      el.btnCopySnippet.addEventListener("click", async () => {
        const code = el.pythonSnippet.textContent || "";
        if (!code.trim()) return;
        try {
          await navigator.clipboard.writeText(code);
          el.btnCopySnippet.textContent = "Copié ✓";
          setTimeout(() => {
            el.btnCopySnippet.textContent = "Copier le code";
          }, 1500);
        } catch (_) {
          // ignore
        }
      });
    }

    if (el.btnExportCsv) el.btnExportCsv.addEventListener("click", function() { exportFileWithFeedback("csv", el.btnExportCsv); });
    if (el.btnExportJson) el.btnExportJson.addEventListener("click", function() { exportFileWithFeedback("json", el.btnExportJson); });

    if (el.btnToggleCustom) el.btnToggleCustom.addEventListener("click", toggleCustomProfile);
    if (el.btnApplyCustom) el.btnApplyCustom.addEventListener("click", applyCustomProfile);
    if (el.btnResetCustom) el.btnResetCustom.addEventListener("click", resetCustomProfile);

    // Compact mode toggle
    var btnCompact = document.getElementById('btn-compact');
    if (btnCompact) btnCompact.addEventListener('click', toggleCompactMode);

    // Search autocomplete
    if (el.search) {
      el.search.addEventListener('input', function() {
        renderSearchAutocomplete(el.search.value.trim());
      });
      el.search.addEventListener('blur', function() {
        setTimeout(closeAutocomplete, 200);
      });
    }
    var acList = document.getElementById('search-autocomplete-list');
    if (acList) {
      acList.addEventListener('mousedown', function(e) {
        var item = e.target.closest('.search-autocomplete-item');
        if (!item) return;
        var val = item.getAttribute('data-value');
        if (val && el.search) {
          el.search.value = val;
          closeAutocomplete();
          applyFilters();
          saveSettings();
        }
      });
    }

    // Favorites click handling
    if (el.modelsTbody) {
      el.modelsTbody.addEventListener('click', function(e) {
        var star = e.target.closest('.fav-star');
        if (!star) return;
        e.stopPropagation();
        var modelName = star.getAttribute('data-fav-model');
        if (!modelName) return;
        toggleFavorite(modelName);
        var active = isFavorite(modelName);
        star.classList.toggle('fav-active', active);
        star.textContent = active ? '★' : '☆';
      });
    }

    // ARIA: set aria-busy on tbody during loading
    if (el.modelsTbody) el.modelsTbody.setAttribute('aria-busy', 'true');

    // Scroll-to-top button
    initScrollTopButton();

    // Row tooltip
    initRowTooltip();

    // Custom profile badge
    updateCustomProfileBadge();

    loadChangelog();
    initRuntimes();
    initChat();
  }

  function renderSelectionState() {
    if (!el.modelsTbody) return;
    const selectedIds = new Set(
      selectedModels.map((s) => (s._id ?? s.model.name))
    );
    el.modelsTbody.querySelectorAll("tr[data-row-id]").forEach((tr) => {
      const rowIdAttr = tr.getAttribute("data-row-id");
      const rowId = rowIdAttr != null ? parseInt(rowIdAttr, 10) : NaN;
      const isSelected = !Number.isNaN(rowId) && selectedIds.has(rowId);
      if (isSelected) tr.classList.add("row-selected");
      else tr.classList.remove("row-selected");
      const cb = tr.querySelector(".model-select");
      if (cb) cb.checked = isSelected;
    });
    renderCompare();
    renderCompareTable();
    updateChart();
    updateSnippet();
  }

  function toggleSelection(rowId) {
    const row = models.find((m) => (m._id ?? m.model.name) === rowId);
    if (!row) return;
    const idx = selectedModels.findIndex(
      (s) => (s._id ?? s.model.name) === (row._id ?? row.model.name)
    );
    if (idx >= 0) {
      selectedModels.splice(idx, 1);
    } else {
      if (selectedModels.length >= 3) {
        selectedModels.shift();
      }
      selectedModels.push(row);
    }
    renderSelectionState();
  }

  function renderCompare() {
    if (!el.compareList) return;
    if (!selectedModels.length) {
      el.compareList.innerHTML = '<p class="history-empty">Sélectionnez 1 à 3 modèles dans le tableau pour les comparer.</p>';
      return;
    }
    el.compareList.innerHTML = selectedModels
      .map((row) => {
        const m = row.model;
        const ecoLabel =
          row.eco_level === "eco" ? "Éco" :
          row.eco_level === "moyen" ? "Moyen" :
          row.eco_level === "energivore" ? "Énergivore" :
          "—";
        return `<div class="compare-item">
          <div class="compare-item-header">
            <span class="compare-item-title">${escapeHtml(m.name || "—")}</span>
            <span class="compare-item-fit">${escapeHtml(row.fit_level || "")} • Score ${escapeHtml(String(row.score ?? "–"))}</span>
          </div>
          <div class="compare-item-metrics">
            <span>Q: ${escapeHtml(String(row.score_quality ?? "–"))}</span>
            <span>S: ${escapeHtml(String(row.score_speed ?? "–"))}</span>
            <span>F: ${escapeHtml(String(row.score_fit ?? "–"))}</span>
            <span>C: ${escapeHtml(String(row.score_context ?? "–"))}</span>
            <span>Énergie: ${escapeHtml(ecoLabel)}</span>
          </div>
        </div>`;
      })
      .join("");
  }

  function updateChart() {
    if (!el.scoresChart) return;
    const ctx = el.scoresChart.getContext("2d");
    const labels = [t("chartQuality"), t("chartSpeed"), t("chartFit"), t("chartContext")];
    const datasets = selectedModels.map((row, idx) => {
      const colors = [
        "rgba(124, 58, 237, 0.6)",
        "rgba(34, 197, 94, 0.6)",
        "rgba(234, 179, 8, 0.6)",
      ];
      const borderColors = [
        "rgba(124, 58, 237, 1)",
        "rgba(34, 197, 94, 1)",
        "rgba(234, 179, 8, 1)",
      ];
      return {
        label: row.model.name || t("modelNumber").replace("%1", String(idx + 1)),
        data: [
          Number(row.score_quality || 0),
          Number(row.score_speed || 0),
          Number(row.score_fit || 0),
          Number(row.score_context || 0),
        ],
        backgroundColor: colors[idx % colors.length],
        borderColor: borderColors[idx % borderColors.length],
        borderWidth: 1,
        pointRadius: 2,
      };
    });
    if (!scoresChart) {
      scoresChart = new Chart(ctx, {
        type: "radar",
        data: {
          labels,
          datasets,
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            r: {
              beginAtZero: true,
              max: 100,
            },
          },
          plugins: {
            legend: {
              labels: {
                color: getComputedStyle(document.documentElement).getPropertyValue('--text').trim() || '#e4e4e7',
              },
            },
          },
        },
      });
    } else {
      scoresChart.data.labels = labels;
      scoresChart.data.datasets = datasets;
      scoresChart.update();
    }
  }

  function buildPythonSnippet(row) {
    if (!row || !row.model) return "";
    const m = row.model;
    const modelName = m.name || "meta-llama/Llama-3.2-3B";
    return [
      "import requests",
      "",
      "BASE_URL = \"http://localhost:11434\"  # Exemple : serveur local de modèles",
      "",
      "",
      "def generate(prompt: str) -> str:",
      "    \"\"\"Exemple minimal d'appel à un modèle local.",
      "    Adaptez l'URL et le format de payload à votre runtime (Ollama, vLLM, OpenAI compatible, etc.).",
      "    \"\"\"",
      "    resp = requests.post(",
      "        f\"{BASE_URL}/api/generate\",",
      "        json={",
      `            "model": "${modelName}",`,
      "            \"prompt\": prompt,",
      "        },",
      "        timeout=60,",
      "    )",
      "    resp.raise_for_status()",
      "    data = resp.json()",
      "    # Adaptez la clé de réponse selon votre serveur",
      "    return data.get(\"response\") or data.get(\"output\") or \"\"",
      "",
      "",
      "if __name__ == \"__main__\":",
      "    print(generate(\"Bonjour, peux-tu te présenter en une phrase ?\"))",
      "",
    ].join("\n");
  }

  function updateSnippet() {
    if (!el.pythonSnippet) return;
    const row = selectedModels[selectedModels.length - 1] || selectedModels[0];
    if (!row) {
      el.pythonSnippet.textContent = "# " + t("snippetPlaceholder");
      return;
    }
    el.pythonSnippet.textContent = buildPythonSnippet(row);
  }

  init();
})();
