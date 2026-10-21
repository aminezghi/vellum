"""Deep, evidence-linked appraisal of a single paper.

Why this exists
---------------
``extract_pdf_metadata`` in the entry script already reads a paper thoroughly:
sections, abstract, study design, statistical method names, sample size,
limitations, funding, ethics. What it cannot express is *where* in the paper a
finding came from, and it does not attempt the dimensions a reviewer actually
asks about — what kind of data this is, how it was sampled, how strong the
reported effects are, whether the reporting guideline was followed.

So this module sits on top and answers those, and it is deliberately built to
be checkable rather than impressive. Every finding is a span of text the paper
itself contains, with the page it was found on, and the page renders that span
next to the claim. Nothing here infers quality or decides whether a paper is
good; it reports what the paper says and lets a human judge.

Honesty rules this module follows
---------------------------------
* Every detected item carries its own snippet. No naked counts.
* A pattern match is labelled as a match. "Reports a manipulation check" means
  the words appeared, not that the check was sound.
* Absence is reported as absence, never as a negative finding about the
  authors. A missing ethics statement is often a two-column-paper artefact, not
  misconduct.
* Overlap is expected and allowed: a paper can legitimately be both
  quantitative and observational.
"""

from __future__ import annotations

import re
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# Lexicons
#
# Kept as (label, pattern) pairs rather than plain word sets so an entry can
# match a phrase ("semi-structured interview") that a word set would either
# miss or match inside an unrelated word. Order matters only for display.
# ══════════════════════════════════════════════════════════════════════════════

# ── Data modality: what kind of material the evidence is made of ──────────────
DATA_MODALITY = [
    ("Questionnaire / survey", r"\bquestionnaires?\b|\bsurvey(?:s)?\b|\bself[- ]report"),
    ("Structured interview", r"\bstructured interviews?\b|\bstandardised interviews?\b"),
    ("Semi-structured interview", r"\bsemi[- ]structured interviews?\b"),
    ("Unstructured / depth interview", r"\bin[- ]depth interviews?\b|\bdepth interviews?\b"),
    ("Focus group", r"\bfocus groups?\b"),
    ("Observation", r"\bobservation(?:s)?\b|\betnographic\b"),
    ("Laboratory experiment", r"\blaborator(?:y|ies)\b|\bexperimental setup\b|\bapparatus\b"),
    ("Field / in-situ study", r"\bin[- ]situ\b|\bfield (?:study|experiment|work)\b"),
("Clinical / physiological measures",
     # A question that *asks about* blood pressure is not a blood-pressure
     # measurement, and "physiological parameters could be used to..." is a
     # plan for future work, not something the study did. Both slipped through
     # a looser pattern against real papers. So a measure now has to name a
     # measurement noun, or sit next to a collection verb.
     r"\bphysiolog\w+\s+(?:measures?|data|recordings?|responses?|signals?)\b|"
     r"\bphysiolog\w+\s+\w{0,14}\s+(?:were|was|is|are)\s+"
     r"(?:measured|recorded|monitored|collected|captured)\b|"
     r"\b(?:measured|recorded|monitored|collected)\s+(?:their\s+|the\s+)?"
     r"(?:blood pressure|heart rate|heart[- ]rate variability|respiration rate|"
     r"respiratory rate|pupil\w*|skin conductance)\b|"
     r"\b(?:blood pressure|heart rate|heart[- ]rate variability|respiration rate)\s+"
     r"(?:was|were)\s+(?:measured|recorded|monitored|collected)\b"),
    # Bare uppercase acronyms are a trap here: case-insensitively, \bPET\b matches
    # "Pet Owners" and \bMRI\b matches "mri" inside ordinary prose. These are
    # matched case-sensitively by _compile, and each still needs a second word
    # that only imaging papers use.
    ("Neuroimaging", r"\bfMRI\b|\bfunctional magnetic resonance\b|\bpositron emission\b|"
                     r"\bvoxel[- ]based\b|\bfree[- ]surfer\b|\bdTI\b|\bstructural MRI\b"),
    ("Medical imaging", r"\bradiograph\w+|\bX[- ]ray\b|\bCT scan\w*|\bhistolog\w+|"
     r"\bhistopatholog\w+|\bmicroscop\w+|\bpatholog\w+"),
    # "sequencing" alone matched "to minimise sequencing effects", so the
    # genomic sense has to be pinned to biological vocabulary.
    ("Genomic / sequencing", r"\bgenom\w+|\bRNA[- ]seq\b|\btranscriptom\w+|\bgenotyp\w+|"
                             r"\bgenome[- ]wide\b|\bCRISPR\b|\bnext[- ]generation sequencing\b|"
                             r"\bwhole[- ]genome\b|\bDNA\b|\bSNP\b|\bGWAS\b"),
    ("Text / documents", r"\bcorpus\b|\btranscripts?\b|\bdocuments? were (?:analysed|analyzed)\b|"
     r"\bnewspapers?\b|\barchives?\b|\bqualitative (?:data|coding)\b"),
    ("Secondary / administrative data", r"\bsecondary (?:data|analysis)\b|\badministrative data\b|"
     r"\bregistry\b|\bcensus\b|\bclaims? data\b|\bpublicly available data\b|"
     r"\bdataset\b|\barchives? of\b"),
    ("Transactional / behavioural logs", r"\bpurchase(?:s)?\b|\btransaction\w*|\btransactional data\b|"
     r"\bclickstream\b|\blog(?:s|ging) data\b|\beye[- ]tracking\b|\bmouse tracking\b|"
     r"\bweb (?:behaviour|behavior|usage)\b"),
    ("Sensor / device data", r"\bwearable\w*|\bsensors?\b|\bIoT\b|\btelemetry\b|\baccelerometer\w*"),
]

# ── Measurement scale and unit of analysis ───────────────────────────────────
DATA_SCALE = [
    ("Nominal", r"\bnominal\b"),
    ("Ordinal", r"\bordinal\b|\bLikert\b|\branking scale\b|\b5[- ]point scale\b|"
                r"\b7[- ]point scale\b|\b(?:five|seven)[- ]point\b"),
    ("Interval", r"\binterval scale\b|\bLikert[- ]type\b"),
    ("Ratio", r"\bratio scale\b|\btrue zero\b"),
    ("Continuous", r"\bcontinuous (?:outcome|variable|data|measure)\w*\b"),
    ("Categorical / binary", r"\bcategorical\b|\bbinary (?:outcome|variable|data)\b|"
                             r"\bdichotom\w+|\b(?:yes|no) responses?\b"),
    ("Counts", r"\bcount data\b|\bfrequency data\b|\bcounts?\b"),
]

UNIT_OF_ANALYSIS = [
    ("Individual / participant", r"\bparticipants?\b|\bsubjects?\b|\brespondents?\b|"
                                 r"\bindividuals?\b|\bconsumers?\b|\bstudents?\b"),
    ("Household", r"\bhouseholds?\b"),
    ("Firm / organisation", r"\bfirms?\b|\bcompanies\b|\borgani[sz]ations?\b|\bfirms?\b|\bfirms\b"),
    ("Product / brand", r"\bproducts?\b|\bbrands?\b|\bitems?\b"),
    ("Trial / session", r"\btrials?\b|\bsessions?\b|\bruns?\b|\bblocks?\b"),
    ("Document / text unit", r"\barticles?\b|\bdocuments?\b|\bparagraphs?\b|\bsentences?\b"),
    ("Time point / day", r"\bper (?:day|week|month|wave)\b|\btime points?\b|\bwaves?\b"),
    ("Region / site", r"\b(?:sites?|regions?|countries|countries|counties)\b"),
]

# ── Sampling strategy ────────────────────────────────────────────────────────
SAMPLING = [
    ("Random / simple random", r"\brandom(?:ly|ised|ized)?\s+(?:selected|assigned|chosen|"
                               r"drawn|allocated)\b|\brandom\s+sampl\w+|\bsimple random\w*"),
    ("Stratified", r"\bstratif\w+"),
    ("Cluster", r"\bcluster\s+(?:sampl|sampling|design|randomi\w+)\b"),
    ("Systematic", r"\bsystematic\s+(?:sampl|sampling)\b"),
    ("Probability sampling", r"\bprobability\s+sampl\w+"),
    ("Convenience", r"\bconvenience\s+(?:sampl|sampling)\b"),
    ("Purposive / purposeful", r"\bpurposive\b|\bpurposeful(?:ly)?\s+(?:selected|sampled|chosen)\b"),
    ("Snowball", r"\bsnowball\b"),
    ("Quota", r"\bquota\s+(?:sampl|sampling)\b"),
    ("Self-selected / volunteer", r"\bself[- ]select\w+|\bvolunteers?\b|\bopted\s+in\b"),
    ("Recruited online / panel", r"\brecruited\s+(?:online|remotely|via\s+(?:a\s+)?panel|"
                                 r"through\s+(?:a\s+)?panel|through\s+qualtrics)\b|"
                                 r"\bonline\s+panel\b|\bprolific\b|\bmturk\b"),
    ("Recruited in person / site", r"\brecruited\s+(?:in\s+person|at\s+(?:a|the)\s+\w+)\b|"
                                    r"\brecruited\s+at\s+(?:the\s+)?(?:university|laborator\w+|"
                                    r"hospital|school|clinic)\b"),
    # "all participants received the same questions" is a study-design sentence,
    # not a census. A census claims the whole sampling frame was taken, so the
    # word has to be joined to inclusion, not merely preceded by "all".
    ("Census", r"\bcensus\b|\b(?:100|one hundred) ?(?:per ?cent|%) of\b|"
     r"\bcomplete (?:population|population[- ]wide) (?:sample|survey|census)\b|"
     r"\ball (?:eligible |sampled )?(?:patients|participants|students|records|cases|"
     r"households|employees)\s+(?:were|was)?\s*(?:included|enrolled|recruited|"
     r"approached|surveyed|interviewed|analy[sz]ed)\b|\btotal population\b"),
    ("Screening of a cohort", r"\bscreened\b|\bconsecutive(?:ly)?\b|\bcohort\b|\bregistry\b"),
]

# ── Instruments and validated scales ─────────────────────────────────────────
INSTRUMENTS = [
    ("Validated named scale", r"\b(?:validated|standardised|standardized|well[- ]established)\b"
                              r"[^.]{0,60}\b(?:scale|index|questionnaire|instrument)\b"),
    ("Likert-type items", r"\bLikert\b[^.]{0,40}\b(?:scale|type|items?|items)\b"),
    ("Established test name", r"\b(?:PANAS|SUS|SF-\d{2}|ECR[-_]?R|Big Five|NEO[-_]?\w+|"
                              r"MMSE|MoCA|WISC|WAIS|Raven'?s?\b|Stroop|Goldberg|Wilkinson|"
                              r"Maslach|Beck(?:'s)?\b|BDI\b|STAI|DASS|OSI|PSSS|COPE)\b"),
    ("Interview protocol", r"\binterview (?:guide|protocol|schedule|script)\b|\btopic guide\b"),
    ("Coding framework", r"\b(?:thematic|content|open|axial)\s+analysis\b|\bcoding (?:scheme|frame)\b|"
                         r"\bcodebook\b|\binter[- ]rater\b"),
    ("Hardware / apparatus", r"\b(?:apparatus|device|rig|eyetracker|eye[- ]tracker|EEG cap|"
                             r"reaction[- ]time (?:board|system)|force plate)\b"),
]

# ── Analysis software ────────────────────────────────────────────────────────
SOFTWARE = [
    ("R", r"\bR\s?(?:version\s)?(?:v?\d+\.\d+|\(development team\)|studio\b)|\bRStudio\b"),
    ("Python", r"\bPython\b|\bNumPy\b|\bpandas\b|\bscikit[- ]learn\b|\bPyTorch\b|\bTensorFlow\b"),
    ("SPSS", r"\bSPSS\b|\bIBM SPSS\b"),
    ("Stata", r"\bStata\b"),
    ("SAS", r"\bSAS\b|\bSAS Institute\b"),
    ("MATLAB", r"\bMATLAB\b"),
    ("Julia / R / other lang", r"\bJulia\b"),
    ("E-Views / AMOS / Mplus", r"\bE-Views\b|\bAMOS\b|\bMplus\b"),
    ("JASP / jamovi", r"\bJASP\b|\bjamovi\b|\bJAMOVI\b"),
    ("Qualitative software", r"\bNVivo\b|\bATLAS\.?ti\b|\bMAXQDA\b|\bDedoose\b"),
    ("Eye-tracking software", r"\bEyeLink\b|\bTobii\b|\bWebGazer\b"),
    ("OSF / registry", r"\bOpen Science Framework\b|\bOSF\b|\bICPSR\b|\bDataCite\b"),
    ("Registry (clinical)", r"\bClinicalTrials\.gov\b|\bISRCTN\b|\btrials?\b\s*(?:registry|number)"),
]

# ── Rigour of the measurement ────────────────────────────────────────────────
RELIABILITY = [
    ("Internal consistency (Cronbach's α)", r"Cronbach'?s?\s*(?:alpha|α)"),
    ("Inter-rater agreement (kappa)", r"\b(?:Cohen'?s\s*)?(?:kappa|κ)\b[^.]{0,40}"
                                      r"\b(?:agreement|reliability|inter[- ]rater)\b|"
                                      r"\binter[- ]rater (?:agreement|reliability)\b"),
    ("Test–retest reliability", r"\btest[- ]retest\b"),
    ("Construct validity", r"\bconstruct validity\b|\bconvergent validity\b|\bdiscriminant validity\b"),
    ("Instrument validation", r"\bpilot (?:test|study|ed)?\b[^.]{0,60}\b(?:instrument|scale|questionnaire)\b|"
                               r"\bvalidated\b[^.]{0,40}\bscale\b"),
    ("Calibration / verification", r"\bcalibrat\w+|\bverif(?:y|ied|ication)\b[^.]{0,40}\b(?:procedure|method)\b"),
]

# ── Statistical reporting detail ─────────────────────────────────────────────
# Named methods already come from the entry script; these are the *quantities*
# a reviewer asks about and nothing else in the codebase parses them.
EFFECT_SIZE_RX = [
    ("Pearson r", r"\br\s*=\s*[-−]?\d?\.\d+|\bPearson'?s? r\b"),
    ("Cohen's d", r"\b(?:Cohen'?s?\s*)?d\s*=\s*[-−]?\d?\.\d+|\bCohen'?s d\b|\bHedges'? g\b"),
    ("Regression coefficient (β)", r"\bβ\s*(?:₁|₂|3|\w)?\s*=\s*[-−]?\d?\.\d+|\bb\s*=\s*[-−]?\d?\.\d+"),
    ("Odds ratio (OR)", r"\b(?:OR|odds ratio)\s*(?:=|of)\s*[-−]?\d?\.\d+|\bOR\s*=\s*\d"),
    ("Risk ratio (RR)", r"\bRR\s*=\s*[-−]?\d?\.\d+|\brisk ratio\b"),
    ("Variance explained (R²)", r"\bR²\s*=\s*[-−]?\d?\.\d+|\bR\^?2\b|\badjusted R²\b"),
    ("Effect size (η² / partial η²)", r"\b(?:partial\s*)?η²\s*=\s*[-−]?\d?\.\d+|\betas? squared\b"),
    ("AUC / model fit", r"\bAUC\s*=\s*[-−]?\d?\.\d+|\bC-index\b|\bRMSE\b|\bMAE\b"),
    ("Standardised beta", r"\bstandardi[sz]ed beta\b|\bstd\.?\s*beta\b"),
]

CI_RX = r"\b95\s*%\s*(?:CI|confidence interval)|\bCI\s*[:=]\s*[-−(]|\bconfidence interval\b"
P_RX = r"\bp\s*[<=>≤≥]\s*\.?\d+|\bp[- ]value\b"
# A threshold ("p < .05") hides the magnitude; an exact one ("p = .03") does not.
# The ``p`` is required here -- an optional one turns the pattern into a bare
# "= 7" search that matched seven unrelated strings in a single paper.
P_EXACT_RX = r"\bp\s*=\s*\.?\d"
P_THRESHOLD_RX = r"\bp\s*[<≤]\s*\.?\d"

MULTIPLICITY = [
    ("Multiple-comparison correction", r"\bBonferroni\b|\bHolm[- ]Bonferroni\b|"
                                        r"\bBenjamini[- ]Hochberg\b|\bFDR\b|\bfalse discovery rate\b|"
                                        r"\bTukey(?:'s)?\b|\bDunn(?:'s)?\b|\bGames[- ]Howell\b|"
                                        r"\bŠidák\b|\bSidak\b"),
    ("Alpha level set", r"\balpha\s*(?:level)?\s*(?:of|=|was|at)?\s*\.0[0-5]\b|\bα\s*=\s*\.0[0-5]\b"),
    ("Missing-data handling", r"\blistwise deletion\b|\bpairwise deletion\b|\bcomplete[- ]case\b|"
                              r"\bmissing (?:completely )?at random\b|\bmultiple imputation\b|"
                              r"\bimputed\b|\bmissing data\b|\bmean imputation\b|\bLOCF\b"),
    ("Sensitivity / robustness check", r"\bsensitivity analysis\b|\brobustness check\b|"
                                       r"\bsensitivity (?:analyses|check)\b|\bwe additionally\b"),
    ("Power / sample-size justification", r"\bpower analysis\b|\bpost[- ]hoc power\b|\bG\*Power\b|"
                                          r"\bsample size (?:was )?(?:determined|calculated|justified)\b|"
                                          r"\ba priori power\b|\bstatistical power\b"),
    ("Assumption checking", r"\b(?:normality|homogeneity|multicollinearity|VIF|assumption)s?\b"
                             r"[^.]{0,40}\b(?:checked|tested|verified|assessed|confirmed)\b"),
    ("Robust standard errors", r"\bcluster[- ]robust\b|\bHuber[- ]White\b|\brobust standard errors?\b|"
                               r"\bNewey[- ]West\b"),
]

MODEL_TYPES = [
    ("Ordinary least squares", r"\b(?:OLS|ordinary least squares?|multiple linear regression)\b"),
    ("Generalised linear model", r"\b(?:GLM|generalized linear model|generalised linear model)\b|"
                                 r"\blogistic regression\b|\bPoisson regression\b|\bnegative binomial\b"),
    ("Mixed-effects model", r"\bmixed[- ]effects?\b|\bmixed[- ]model\b|\bmultilevel (?:model|regression)\b|"
                            r"\bGLMM\b|\brandom effects?\b"),
    ("Structural equation model", r"\b(?:SEM|structural equation)\w*\b|\bpath analysis\b|\bPLS[- ]SEM\b"),
    ("Survival analysis", r"\bKaplan[- ]Meier\b|\bCox (?:proportional hazards|regression)\b|\blog[- ]rank\b"),
    ("Time-series / panel", r"\b(?:ARIMA|GARCH|var\(|VAR\b|panel data|fixed[- ]effects?|"
                            r"difference[- ]in[- ]differences?\b|\bevent stud\w+)"),
    ("Machine learning", r"\b(?:random forest|gradient boosting|neural network|deep learning|"
                         r"\bSVM|support vector|k[- ]means|hierarchical clustering|lasso|elastic net)\b"),
    ("Latent class / factor", r"\b(?:latent class|factor analysis|confirmatory factor|"
                              r"\bstructural equation)\b|\bCFA\b|\bEFA\b|\bIRT\b|\bitem response\b"),
]

# ── Bias control and procedural rigour ───────────────────────────────────────
BIAS_CONTROL = [
    ("Randomisation", r"\brandomi[sz]ed\b|\brandom allocation\b|\brandomly assigned\b|\bRCT\b"),
    ("Allocation concealment", r"\ballocation concealment\b|\bconcealed allocation\b|\bsequence generation\b"),
    ("Blinding (single)", r"\bsingle[- ]blind\w*"),
    ("Blinding (double)", r"\bdouble[- ]blind\w*"),
    ("Masking", r"\bmask(?:ed|ing)\b"),
    ("Control / comparison group", r"\bcontrol group\b|\bcomparison group\b|\bplacebo\b|"
                                   r"\bwait[- ]list control\b|\bno[- ]treatment control\b"),
    ("Counterbalancing", r"\bcounterbalanc\w+|\bLatin square\b|\brandomi[sz]ed order\b"),
    ("Manipulation check", r"\bmanipulation check\w*\b"),
    ("Attention check", r"\battention check\w*\b|\binstruction comprehension check\b"),
    ("Practice trials", r"\bpractice (?:trial|run|item)s?\b"),
    ("Preregistered", r"\bpre[- ]?regist(?:ered|ration)\w*\b|\bregistered report\b"),
    ("Protocol / trial registration", r"\b(?:ClinicalTrials\.gov|ISRCTN)\b|\btrial (?:registration|number)\b"),
    ("Blinded outcome assessment", r"\bblind\w*\s+(?:to|of)\s+(?:the\s+)?(?:outcome|assessment|analys\w+)\b"),
]

# ── Validity, generalisability, causal language ──────────────────────────────
VALIDITY_THREATS = [
    ("Selection bias", r"\bselection bias\b"),
    ("Information / measurement bias", r"\binformation bias\b|\bmeasurement bias\b|\bmisclassification\b"),
    ("Recall bias", r"\brecall bias\b"),
    ("Social desirability bias", r"\bsocial desirability\b"),
    ("Non-response bias", r"\bnon[- ]?response bias\b"),
    ("Attrition / dropout", r"\battrition\b|\bdropout\b|\bdrop[- ]out\b|\blost to follow[- ]up\b"),
    ("Confounding", r"\bconfound(?:ing|er|ed)\b|\bconfounds?\b"),
    ("Performance bias", r"\bperformance bias\b"),
    ("Observer / expectancy bias", r"\bobserver bias\b|\bexpectancy bias\b|\bexperimenter bias\b"),
    ("Regression to the mean", r"\bregression to the mean\b"),
    ("Temporal / external validity", r"\bexternal validity\b|\btemporal validity\b|"
                                      r"\bgeneralisa\w+|\bgeneraliza\w+"),
    ("Heterogeneity", r"\bheterogene\w+|\bsubgroup (?:difference|variation)\b|\bmoderator\b"),
]

HEDGES = [
    ("Hedging language", r"\bmay\b|\bmight\b|\bcould\b|\bsuggests?\b|\bappears?\b|\bseems?\b|"
                         r"\bindicates?\b|\bpotentially\b|\bpossibly\b|\barguably\b"),
    ("Booster language", r"\bproves?\b|\bclearly\b|\bobviously\b|\bundoubtedly\b|\bdefinitiv\w+"),
    ("Causal language", r"\bcaused?\b|\bcausal\b|\bleads? to\b|\bresults? in\b|\bdrives?\b|"
                        r"\bimpacts?\b|\beffect of\b"),
    ("Limitation acknowledgement", r"\bwe (?:acknowledge|recognise|recognize)\w*\b|"
                                    r"\bsome limitations?\b|\bseveral limitations?\b|"
                                    r"\bis (?:subject|limited) to\b|\bmay not (?:generalise|generalize)\b"),
]

# ── Reporting guidelines ────────────────────────────────────────────────────
REPORTING_GUIDELINES = [
    ("CONSORT (RCT)", r"\bCONSORT\b"),
    ("STROBE (observational)", r"\bSTROBE\b"),
    ("PRISMA (systematic review)", r"\bPRISMA\b"),
    ("TRIPOD (prediction model)", r"\bTRIPOD\b"),
    ("ARRIVE (animal research)", r"\bARRIVE\b"),
    ("CHEERS (economic evaluation)", r"\bCHEERS\b"),
    ("SRQR / COREQ (qualitative)", r"\bSRQR\b|\bCOREQ\b"),
    ("MRC / mixed-methods reporting", r"\bMRC mixed methods\b|\bmixed methods reporting guideline\b|"
                                       r"\bGRAMMS\b"),
    ("APA style (7th)", r"\bAPA (?:7th|7)\b|\bAmerican Psychological Association\b"),
]

# ── Reference parsing ───────────────────────────────────────────────────────
_YEAR_RX = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")
# A reference list entry starts either with an index marker or a capitalised
# author surname; both styles are common and neither alone is reliable.
_REF_START_RX = re.compile(
    r"^\s*(?:\[\d{1,3}\]|\(\d{1,3}\)|\d{1,3}[.)])\s+\S"
    r"|^[A-Z][A-Za-z'’\-]{1,28},?\s+(?:[A-Z]\.|[A-Z][a-z])"
)


_ACRONYM_RE = re.compile(r"(?<![a-z])[A-Z]{2,}(?![a-z])")


def _compile(items):
    """Compile a lexicon into [(label, compiled pattern)].

    A pattern containing a literal uppercase acronym is compiled
    case-*sensitively*. That is not fussiness: under ``re.I`` a brain-imaging
    lexicon entry for ``\\bPET\\b`` matches "Pet Owners", and a genomics entry
    for ``\\bsequencing\\b`` matches "to minimise sequencing effects". Both were
    real false positives against a food-labelling paper. Words stay
    case-insensitive everywhere, which is what a reader expects.
    """
    out = []
    for label, pat in items:
        flags = 0 if _ACRONYM_RE.search(pat) else re.I
        out.append((label, re.compile(pat, flags)))
    return out


_MODALITY_RX = _compile(DATA_MODALITY)
_SCALE_RX = _compile(DATA_SCALE)
_UNIT_RX = _compile(UNIT_OF_ANALYSIS)
_SAMPLING_RX = _compile(SAMPLING)
_INSTRUMENT_RX = _compile(INSTRUMENTS)
_SOFTWARE_RX = _compile(SOFTWARE)
_RELIABILITY_RX = _compile(RELIABILITY)
_MULTIPLICITY_RX = _compile(MULTIPLICITY)
_MODEL_RX = _compile(MODEL_TYPES)
_BIAS_RX = _compile(BIAS_CONTROL)
_VALIDITY_RX = _compile(VALIDITY_THREATS)
_HEDGE_RX = _compile(HEDGES)
_GUIDELINE_RX = _compile(REPORTING_GUIDELINES)
_EFFECT_RX = _compile(EFFECT_SIZE_RX)
_CI_RE = re.compile(CI_RX, re.I)
_P_RE = re.compile(P_RX)
_P_EXACT_RE = re.compile(P_EXACT_RX, re.I)
_P_THRESHOLD_RE = re.compile(P_THRESHOLD_RX, re.I)


# ══════════════════════════════════════════════════════════════════════════════
# Page-level scanning
# ══════════════════════════════════════════════════════════════════════════════

def _clean(text):
    """Collapse whitespace so a matched span can be shown inline."""
    return re.sub(r"\s+", " ", text or "").strip()


def _snippet(text, start, end, pad=90):
    """A readable window of page text around a match."""
    lo = max(0, start - pad)
    hi = min(len(text), end + pad)
    out = _clean(text[lo:hi])
    return ("…" if lo > 0 else "") + out + ("…" if hi < len(text) else "")


def scan(pages, pattern, per_page=2, max_hits=6, min_chars=0):
    """Find a pattern across pages, reporting where each hit is.

    Returns ``[{page, text}]`` with 1-based page numbers. Only the first
    ``per_page`` hits on any page are kept: a pattern that matches every page
    tells the reader nothing about *where* to look, and a long list is worse
    than the top few.

    A pattern may be given as a string, which is compiled case-insensitively --
    every lexicon in this module is written as prose regexes, so letting a
    caller pass one raw is convenient and costs nothing.
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern, re.I)
    hits, seen = [], 0
    for idx, page_text in enumerate(pages):
        text = page_text or ""
        if len(text) < min_chars:
            continue
        found = 0
        for m in pattern.finditer(text):
            if found >= per_page:
                break
            hits.append({"page": idx + 1, "text": _snippet(text, m.start(), m.end())})
            found += 1
            seen += 1
            if seen >= max_hits:
                return hits
    return hits


def scan_lexicon(pages, lexicon, per_page=1, max_hits=5, min_chars=0):
    """Apply a whole lexicon, keeping only labels that actually match.

    Returns ``[{label, hits}]`` sorted by first appearance in the paper, so the
    reading order follows the argument rather than the alphabet.
    """
    found = []
    for label, pattern in lexicon:
        hits = scan(pages, pattern, per_page=per_page, max_hits=max_hits,
                    min_chars=min_chars)
        if hits:
            found.append({"label": label, "hits": hits})
    found.sort(key=lambda item: item["hits"][0]["page"])
    return found


def count_in(text, pattern):
    """Total matches of a pattern in a blob of text."""
    if not text:
        return 0
    return len(pattern.findall(text))


def first_hits(pages, pattern, per_page=1, max_hits=3):
    """Shorthand for a single pattern's evidence."""
    return scan(pages, pattern, per_page=per_page, max_hits=max_hits)


def _page_text(pages, n, window=1):
    """Concatenate a page and its neighbours, for a readable quote."""
    lo = max(0, n - 1 - window)
    hi = min(len(pages), n + window)
    # A page can be None when extraction failed, so join defensively as
    # scan() and references_start() already do.
    return _clean(" ".join((p or "") for p in pages[lo:hi]))


# ══════════════════════════════════════════════════════════════════════════════
# Locating the body, the methods section and the reference list
#
# Everything below needs the same three boundaries, and getting them wrong is
# how a paper about food labels ends up "using neuroimaging": the bibliography
# quotes other papers' methods in full, so an unscoped search matches the
# references of a hundred studies.
# ══════════════════════════════════════════════════════════════════════════════

_HEAD_NUM_RX = r"(?:\d+(?:\.\d+)*\s*[.)|]?\s*)?"

_REFERENCES_HEAD_RX = re.compile(
    rf"^[ \t]*{_HEAD_NUM_RX}(?:references?|bibliography|works\s+cited|literature\s+cited)\s*$",
    re.I)

_HEAD_NUM = r"(?:\d+(?:\.\d+)*\s*[.)|]?\s*)?"

# A heading is either alone on its line or carries a section number and pipe,
# as in "3 | Results 3.1 | General Characteristics". Both requirements matter:
# matching the bare word "results" finds prose ("the results show that...") and
# puts the methods window three pages too early.
_METHODS_HEAD_RX = re.compile(
    rf"(?:^[ \t]*{_HEAD_NUM}(?:materials?\s+and\s+methods?|method(?:ology|s)?|"
    r"experimental\s+design|research\s+method(?:ology)?|methods?|approach|study\s+design|"
    r"data\s+analysis|statistical\s+analysis|statistical\s+methods?|statistics|"
    r"participants?|materials?|procedure)[ \t]*$)"
    rf"|(?:\|\s*{_HEAD_NUM}(?:materials?\s+and\s+methods?|method(?:ology|s)?|"
    r"experimental\s+design|research\s+method(?:ology)?|methods?|approach|study\s+design|"
    r"data\s+analysis|statistical\s+analysis|statistical\s+methods?|statistics|"
    r"participants?|materials?|procedure)\b)", re.I | re.M)

_RESULTS_HEAD_RX = re.compile(
    rf"(?:^[ \t]*{_HEAD_NUM}(?:results?|findings?)[ \t]*$)"
    rf"|(?:\|\s*{_HEAD_NUM}(?:results?|findings?)\b)", re.I | re.M)


def references_start(pages):
    """Index of the page where the bibliography begins, or None.

    A heading on its own line is the only reliable signal. Matching the word
    "references" anywhere would fire on a citation sentence in the discussion.
    """
    for idx in range(len(pages) - 1, -1, -1):
        for line in (pages[idx] or "").splitlines():
            if _REFERENCES_HEAD_RX.match(line.rstrip()):
                return idx
    return None


def references_slice(pages):
    """The text of the bibliography, so the reference parser can start after it.

    Returns ``(entries_text, start_page)``. When the heading sits mid-page the
    lines above it are dropped, otherwise a funding note printed just above the
    heading becomes reference number one.
    """
    idx = references_start(pages)
    if idx is None:
        return None, None
    head = (pages[idx] or "").splitlines()
    tail = head
    for n, line in enumerate(head):
        if _REFERENCES_HEAD_RX.match(line.rstrip()):
            tail = head[n + 1:]
            break
    chunks = ["\n".join(tail)] + list(pages[idx + 1:])
    return "\n".join(chunks), idx


def methods_range(pages, ref_idx):
    """(first, last) page of the methods-ish span, or (None, None).

    Scoped to the body so a "Methods" phrase inside the bibliography cannot
    shift the window. Both edges are best-effort: many journals run
    ``3 | Results`` mid-line, so the patterns accept a pipe or newline in front
    of the heading rather than requiring the line to start with it.
    """
    stop_at = len(pages) if ref_idx is None else ref_idx
    start = None
    for idx in range(stop_at):
        text = pages[idx] or ""
        if start is None:
            m = _METHODS_HEAD_RX.search(text)
            if m:
                start = idx
        else:
            if _RESULTS_HEAD_RX.search(text):
                return start, max(start, idx)
    if start is None:
        return None, None
    return start, max(start, stop_at - 1)


# ══════════════════════════════════════════════════════════════════════════════
# Reference list
# ══════════════════════════════════════════════════════════════════════════════

def parse_references(pages, authors=None, max_refs=400):
    """Split the reference list into entries and describe it.

    The entry script already counts references four independent ways and keeps
    the largest figure, which is right for a count but throws the list away.
    Here the entries themselves are recovered so the reader can see how many are
    empirical, how recent, and how much of the list is the authors citing
    themselves.
    """
    blob, start_idx = references_slice(pages)
    if blob is None:
        return {"entries": [], "count": 0, "years": [], "span": None,
                "empirical": 0, "self_citations": 0, "found": False,
                "start_page": None}

    entries, current = [], None
    for line in blob.splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        if _REF_START_RX.match(line):
            if current:
                entries.append(current)
            current = line.strip()
        elif current is not None and len(current) < 900:
            # A wrapped reference continues the previous entry: author-year
            # styles break titles across two or three lines.
            current += " " + line.strip()
        if len(entries) >= max_refs:
            break
    if current and len(entries) < max_refs:
        entries.append(current)

    years = []
    empirical = 0
    surnames = set()
    if authors:
        for a in authors:
            parts = re.split(r"[,;]", str(a))
            for part in parts:
                token = part.strip().split()[-1] if part.strip() else ""
                if len(token) > 2:
                    surnames.add(token.lower())

    for entry in entries:
        m = _YEAR_RX.search(entry)
        if m:
            years.append(int(m.group(1)))
        if re.search(r"\b(empirical|experiment(?:al)?|survey|field stud|"
                     r"randomi[sz]ed|participants?|respondents?)\b", entry, re.I):
            empirical += 1

    self_cites = 0
    if surnames:
        for entry in entries:
            head = entry[:80].lower()
            if any(re.search(rf"\b{re.escape(s)}\b", head) for s in surnames):
                self_cites += 1

    return {"entries": entries,
            "count": len(entries),
            "years": sorted(years),
            "span": (min(years), max(years)) if years else None,
            "empirical": empirical,
            "self_citations": self_cites,
            "found": True,
            "start_page": None if start_idx is None else start_idx + 1}


# ══════════════════════════════════════════════════════════════════════════════
# The analysis itself
# ══════════════════════════════════════════════════════════════════════════════

def _data_type_verdict(modalities, scale, unit):
    """Name the data type from what was found, or admit it was not found."""
    qualitative = any(m["label"] in ("Unstructured / depth interview",
                                     "Semi-structured interview",
                                     "Structured interview", "Focus group",
                                     "Text / documents", "Observation")
                      for m in modalities)
    quantitative = any(m["label"] in ("Questionnaire / survey",
                                      "Transactional / behavioural logs",
                                      "Clinical / physiological measures",
                                      "Neuroimaging", "Medical imaging",
                                      "Genomic / sequencing",
                                      "Sensor / device data") for m in modalities)

    # A named scale settles it even when the modality is generic: "Likert
    # responses analysed with t-tests" is quantitative whichever noun the
    # methods section happens to use for the instrument.
    if any(s["label"].startswith(("Ordinal", "Interval", "Ratio", "Continuous",
                                  "Nominal", "Categorical", "Counts"))
           for s in scale):
        quantitative = True

    if qualitative and quantitative:
        verdict = "Mixed methods"
    elif qualitative:
        verdict = "Qualitative"
    elif quantitative:
        verdict = "Quantitative"
    else:
        verdict = "Not identifiable from the text"
    return verdict, bool(unit)


def analyse(pdf_path, meta, pages):
    """Deep appraisal of one paper.

    Parameters
    ----------
    pdf_path : str | Path
        The PDF, used only for its filename.
    meta : dict
        Output of ``vellum_analysis.extract_one`` — supplies the section bodies
        and the study-design classification this module builds on.
    pages : list[str]
        Page-indexed text, so every finding can cite a page.

    Returns a dict of report sections. Nothing in here raises: a field that
    cannot be read is absent, and the page says so.
    """
    pages = [p or "" for p in (pages or [])]
    meta = meta or {}
    if not pages:
        return {"ok": False, "reason": "no text layer",
                "filename": Path(pdf_path).name}

    # Scope every claim to the body of the paper. The bibliography restates the
    # methods of a hundred other studies in full, so an unscoped search over a
    # 137-reference paper reports its influences' methods as its own -- that is
    # how a food-labelling study first came back tagged "genomic" and
    # "neuroimaging".
    ref_idx = references_start(pages)
    body = pages[:ref_idx] if ref_idx is not None else pages
    m_first, m_last = methods_range(pages, ref_idx)
    methods_zone = body[m_first:m_last + 1] if m_first is not None else []

    def in_methods(hits):
        """Keep only the hits that fall inside the methods section.

        Page-based, not term-based: asking whether the *label* appears in the
        methods text never fires, because a methods section never says "Census".
        """
        if m_first is None:
            return []
        return [h for h in hits if m_first <= (h["page"] - 1) <= m_last]

    whole = _clean(" ".join(body))
    methods_text = _clean(meta.get("methodology") or "")

    # ── Where the evidence came from, and what it cannot cover ───────────────
    # A null result here means "not in the extracted text", which is a very
    # different claim from "the paper does not report it". Tables are the usual
    # reason: a publisher PDF often carries the prose in the text layer and its
    # numeric tables as images, so every p-value and effect size vanishes while
    # the running text survives intact.
    table_refs = len(re.findall(r"\b(?:tables?|tabs?\.)\s*\d+", whole, re.I))
    fig_refs = len(re.findall(r"\b(?:figures?|figs?\.)\s*\d+", whole, re.I))
    notation = bool(_P_RE.search(whole) or _CI_RE.search(whole)
                    or any(p.search(whole) for _l, p in _EFFECT_RX))
    diagnostics = {
        "pages_read": len(pages),
        "body_pages": len(body),
        "characters": len(whole),
        "words": len(whole.split()),
        "references_start_page": None if ref_idx is None else ref_idx + 1,
        "methods_pages": None if m_first is None else (m_first + 1, m_last + 1),
        "table_mentions": table_refs,
        "figure_mentions": fig_refs,
        "statistical_notation_found": notation,
    }

    # ── Data types ──────────────────────────────────────────────────────────
    # A study declares its data in the abstract and the methods. Later sections
    # name data the authors only speculate about: this paper's "physiological
    # parameters could be used to discern..." is a plan for future work, and a
    # body-wide search reported it as a measure the study took. So the
    # declaration zone wins, with the whole body as a fallback.
    decl_zone = body[:(m_last + 1)] if m_last is not None else body
    modalities_decl = scan_lexicon(decl_zone, _MODALITY_RX, per_page=1, max_hits=3)
    modalities_all = scan_lexicon(body, _MODALITY_RX, per_page=1, max_hits=3)
    modalities = modalities_decl or modalities_all
    modality_zone = ("abstract and methods" if modalities_decl
                     else "whole body (no methods heading found)")
    scale = scan_lexicon(decl_zone, _SCALE_RX, per_page=1, max_hits=2)
    unit = scan_lexicon(decl_zone, _UNIT_RX, per_page=1, max_hits=2)
    verdict, _ = _data_type_verdict(modalities, scale, unit)

    secondary = first_hits(body, re.compile(
        r"\bsecondary (?:data|analysis)\b|\bpreviously published\b|\barchival\b|"
        r"\bpublic(?:ly)? available (?:data|dataset)\b|\bre[- ]?analysis\b|"
        r"\bwe (?:downloaded|obtained) the (?:data|dataset)\b", re.I), max_hits=3)

    # Every unit noun in the language turns up in a methods section somewhere,
    # so an unqualified list of seven is noise. Prefer the units the methods
    # section itself uses, and say so plainly when the term is only generic.
    unit_in_methods = [u for u in unit if in_methods(u["hits"])]
    unit_ambiguous = len(unit) >= 5 and not unit_in_methods
    unit_shown = ([] if unit_ambiguous else
                  (unit_in_methods[:3] or unit[:3]))

    data = {
        "verdict": verdict,
        "modalities": modalities,
        "modality_zone": modality_zone,
        "modalities_in_methods": [m for m in modalities if in_methods(m["hits"])],
        "scale": scale,
        "unit": unit_shown,
        "unit_ambiguous": unit_ambiguous,
        "unit_candidates": len(unit),
        "secondary": secondary,
        "sample_size": meta.get("sample_size"),
        "sample_label": meta.get("sample_size_label"),
        "figures": meta.get("n_figures"),
        "tables": meta.get("n_tables"),
    }

    # ── Sampling and participants ───────────────────────────────────────────
    strategy = scan_lexicon(body, _SAMPLING_RX, per_page=1, max_hits=2)
    sampling_in_methods = [s for s in strategy if in_methods(s["hits"])]
    inclusion = first_hits(body, re.compile(
        r"inclusion criteria|exclusion criteria|eligibility (?:criteria|requirements)|"
        r"(?:were|was) (?:included|excluded|recruited|selected|screened) (?:if|when|based)", re.I),
        max_hits=3)

    demographics = []
    for label, rx in (("Age", r"\b(?:mean|average|median)\s+age\b|\bage range\b|\baged?\s+\d{1,3}\b|"
                                r"\byears old\b|\bage of\b|\bage group\b"),
                      ("Gender / sex", r"\bmale\b|\bfemale\b|\bnon[- ]binary\b|\bgender\b|\bsex\b"),
                      ("Education", r"\beducation level\b|\buniversity degree\b|\bhigh school\b|"
                                    r"\bpostgraduate\b|\bacademic (?:year|degree)\b|\bqualification\b"),
                      ("Ethnicity / race", r"\bethnic(?:ity|ities)\b|\brace\b|\bracial\b"),
                      ("Income / SES", r"\bincome\b|\bsocioeconomic status\b|\bSES\b|\boccupation\b|"
                                       r"\bemployment\b"),
                      ("Recruitment channel", r"\brecruited (?:via|through|from|online|in person)\b|"
                                              r"\b(?:university|school|company|panel|registry)s? (?:webpage|site|pool)\b")):
        hit = first_hits(methods_zone or body, rx, max_hits=1)
        if hit:
            demographics.append({"label": label, "hits": hit})

    participants_text = meta.get("participants") or ""
    sampling = {
        "strategy": strategy,
        "in_methods": sampling_in_methods,
        "criteria": inclusion,
        "demographics": demographics,
        "participants_text": participants_text,
        "participants_found": bool(participants_text),
        "range_located": m_first is not None,
    }

    # ── Method detail ───────────────────────────────────────────────────────
    instruments = scan_lexicon(body, _INSTRUMENT_RX, per_page=1, max_hits=2)
    software = scan_lexicon(body, _SOFTWARE_RX, per_page=1, max_hits=2)
    reliability = scan_lexicon(body, _RELIABILITY_RX, per_page=1, max_hits=2)
    bias = scan_lexicon(body, _BIAS_RX, per_page=1, max_hits=2)

    method = {
        "design": meta.get("study_design_label") or meta.get("study_design"),
        "text": methods_text,
        "instruments": instruments,
        "software": software,
        "reliability": reliability,
        "bias_control": bias,
        "in_methods": {
            "instruments": [i for i in instruments if in_methods(i["hits"])],
            "software": [i for i in software if in_methods(i["hits"])],
            "reliability": [i for i in reliability if in_methods(i["hits"])],
            "bias_control": [i for i in bias if in_methods(i["hits"])],
        },
    }

    # ── Statistics ──────────────────────────────────────────────────────────
    effects = scan_lexicon(body, _EFFECT_RX, per_page=1, max_hits=3)
    ci_hits = first_hits(body, _CI_RE, per_page=1, max_hits=3)
    p_total = count_in(whole, _P_RE)
    p_exact = count_in(whole, _P_EXACT_RE)
    p_threshold = count_in(whole, _P_THRESHOLD_RE)
    multiplicity = scan_lexicon(body, _MULTIPLICITY_RX, per_page=1, max_hits=2)
    models = scan_lexicon(body, _MODEL_RX, per_page=1, max_hits=2)

    stat_zone = _clean(" ".join(filter(None, [methods_text,
                                             meta.get("participants") or "",
                                             meta.get("findings") or ""])))
    named = [m for m in (meta.get("statistical_methods") or [])]

    statistics = {
        "named_methods": named,
        "models": models,
        "effects": effects,
        "ci": ci_hits,
        "n_p_values": p_total,
        "p_exact": p_exact,
        "p_threshold": p_threshold,
        "multiplicity": multiplicity,
        "reports_p": bool(p_total),
        "reports_effect_size": bool(effects),
        "reports_ci": bool(ci_hits),
        "stat_zone": stat_zone,
    }

    # ── Rigour and reporting ────────────────────────────────────────────────
    validity = scan_lexicon(body, _VALIDITY_RX, per_page=1, max_hits=2)
    language = scan_lexicon(body, _HEDGE_RX, per_page=1, max_hits=3)
    guidelines = scan_lexicon(body, _GUIDELINE_RX, per_page=1, max_hits=2)

    rigour = {
        "validity": validity,
        "language": language,
        "guidelines": guidelines,
        "limitations": meta.get("limitations"),
        "limitations_found": bool(meta.get("limitations")),
        "ethics": meta.get("ethics"),
        "ethics_found": bool(meta.get("ethics")),
        "consent_found": bool(re.search(r"\binformed consent\b", whole, re.I)),
        "funding": meta.get("funding"),
        "funding_found": bool(meta.get("funding")),
        "data_availability": meta.get("data_availability"),
        "data_availability_found": bool(meta.get("data_availability")),
        "conflicts": meta.get("conflicts"),
        "conflicts_found": bool(meta.get("conflicts")),
        "contributions": meta.get("author_contributions"),
        "preregistered": bool(re.search(r"\bpre[- ]?regist", whole, re.I)),
        "word_count": meta.get("word_count"),
        "pages": meta.get("pages"),
    }

    # Causal verbs in a paper with no design that could support them is worth
    # surfacing — as a prompt to check, never as a verdict on the authors.
    causal_hits = first_hits(body, _HEDGE_RX[2][1], per_page=1, max_hits=3)
    design = (method["design"] or "").lower()
    can_be_causal = any(k in design for k in
                        ("rct", "experiment", "quasi", "trial", "longitudinal",
                         "meta-analysis", "randomised", "randomized"))
    rigour["causal_language"] = {
        "hits": causal_hits,
        "design_supports_causality": can_be_causal,
        "note": ("Causal wording is present and the design is observational — "
                 "worth checking whether the claim is bounded."
                 if causal_hits and not can_be_causal else
                 "No causal wording found, or the design can support it."),
    }

    references = parse_references(pages, authors=meta.get("authors"))

    # ── Limits of this report ───────────────────────────────────────────────
    # A deep analysis that overstates its own reach is worse than a shallow one
    # that admits its edges, so the caveats travel with the findings.
    caveats = []
    if ref_idx is None and diagnostics["table_mentions"]:
        caveats.append(
            "No bibliography heading was found, so a few reference-like passages "
            "may still be counted as body text.")
    if diagnostics["methods_pages"] is None:
        caveats.append(
            "The methods section could not be located, so hits cannot be "
            "weighted towards it.")
    if (not notation and diagnostics["table_mentions"]):
        caveats.append(
            f"The running text cites {diagnostics['table_mentions']} tables but the "
            "extracted text contains no statistical notation. The numbers are most "
            "likely in tables that are images in this PDF, so no p-values or effect "
            "sizes were found. That is a limit of the text layer, not evidence that "
            "the paper omits them.")
    if meta.get("scanned") or len(whole) < 500 * max(1, len(pages)):
        caveats.append(
            "This looks like a scanned or image-heavy PDF. Run text extraction on it "
            "for the numeric detail.")
    if body and ref_idx is not None and ref_idx + 1 < len(pages):
        caveats.append(
            f"{len(pages) - ref_idx - 1} page(s) of bibliography were excluded from "
            "every search, so a method named only in the reference list is not "
            "attributed to this paper.")
    if diagnostics["methods_pages"] and diagnostics["methods_pages"][0] > 2:
        caveats.append(
            f"The methods section starts on page {diagnostics['methods_pages'][0]}; "
            "material before it was treated as front matter.")

    # A download that stopped early looks like a paper with no methods and no
    # references, and reporting that as an appraisal finding would be worse than
    # useless -- it would read as a criticism of the authors.
    tail = _clean(body[-1]) if body else ""
    if ref_idx is None and len(pages) <= 4:
        caveats.append(
            f"This file has only {len(pages)} page(s) and no reference list, so it is "
            "probably a partial download rather than a whole paper. Coverage of "
            "methods, results and references will be incomplete.")
    elif ref_idx is None and len(pages) > 4:
        caveats.append(
            "No 'References' heading was found. Either the paper has no reference "
            "list or the file stops before it.")
    if len(pages) > 1 and len(tail) < 120:
        caveats.append(
            f"The final page holds only {len(tail)} characters of text, which usually "
            "means the file is truncated.")

    return {
        "ok": True,
        "filename": Path(pdf_path).name,
        "path": str(pdf_path),
        "pages_read": len(pages),
        "diagnostics": diagnostics,
        "caveats": caveats,
        "identity": {
            "title": meta.get("title"),
            "authors": meta.get("authors"),
            "journal": meta.get("journal"),
            "year": meta.get("year"),
            "doi": meta.get("doi"),
            "abstract": meta.get("abstract"),
            "keywords": meta.get("keywords"),
        },
        "data": data,
        "sampling": sampling,
        "method": method,
        "statistics": statistics,
        "rigour": rigour,
        "references": references,
    }