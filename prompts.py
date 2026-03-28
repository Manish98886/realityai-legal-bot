# Task-specific prompt templates

DRAFTING_PROMPT = """You are drafting a legal document. Based on the case details provided, draft a professional, court-ready document.

Document type: {doc_type}
Case details: {case_details}
Additional instructions: {instructions}

Format the document properly with:
- Court name (if applicable)
- Case number (if available)
- Parties
- Body of the document
- Prayer/relief sought
- Date and signature block

Language: Match the user's language preference. If Hindi, draft in Hindi with English legal terms where needed."""

STRATEGY_PROMPT = """Analyze this case and provide a comprehensive legal strategy:

Case Details:
Title: {title}
Type: {case_type}
Court: {court}
FIR Number: {fir_number}
Sections: {sections}
Parties: {parties}
Description: {description}

Provide:
1. CASE ANALYSIS - Brief analysis of the case
2. STRONG ARGUMENTS (5-10) - Our best arguments
3. COUNTER-ARGUMENTS - What the opposing side might argue
4. POSSIBLE DEFENSES - Defense strategies
5. JUDGE APPROACH - How to present to the judge
6. RISK ASSESSMENT - Strengths and weaknesses
7. NEXT STEPS - Recommended immediate actions
8. DOCUMENTS NEEDED - Checklist of documents to collect"""

SEARCH_PROMPT = """The user is searching for legal information about: "{query}"

Provide:
1. Explanation of the relevant section(s)/law
2. Key legal points
3. Relevant past judgments and precedents (case names, years, court)
4. Practical implications
5. Related sections that might apply

Be thorough and cite specific judgments where possible. If the query is about a specific IPC/CrPC/CPC section, explain it in detail with punishments, bailable/non-bailable status, cognizable/non-cognizable, etc."""

DOCUMENT_ANALYSIS_PROMPT = """Analyze this legal document. The document content is:

{document_text}

Provide:
1. DOCUMENT SUMMARY - Brief summary of what this document is
2. KEY LEGAL POINTS - Important legal points found
3. WEAKNESSES - Weaknesses or issues in the document
4. STRONG ARGUMENTS - Strong points that can be used
5. EVIDENCE CHECKLIST - What additional evidence/documents are needed based on this
6. RECOMMENDATIONS - What to do next"""

SUMMARY_PROMPT = """Generate a concise daily summary of the following case/hearing information:

{data}

Format as a clean, readable summary with:
- Upcoming hearings (date, case, purpose)
- Pending evidence/documents
- Cases needing attention
- Quick stats"""

CASE_CONTEXT_PROMPT = """Here is the context for the current case discussion:

Case ID: {case_id}
Title: {title}
Type: {case_type}
Court: {court}
FIR Number: {fir_number}
Sections: {sections}
Parties: {parties}
Description: {description}
Status: {status}
Evidence: {evidence}
Hearings: {hearings}

Use this context when answering the user's question."""
