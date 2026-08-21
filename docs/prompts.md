# Prompt Engineering & Guardrails

ClinicRAG uses tailored prompts to enforce strict medical safety, clinical structured formatting, and multi-turn patient context integration.

## System Prompt Design
The clinical system prompt instructs the underlying LLM on:
1. **Instant Greetings**: Intercepts greetings naturally without unnecessary overhead.
2. **Clinical Guardrails**:
   - Never provide unverified definitive diagnoses.
   - Present information as educational and decision support.
   - Prioritize red-flag emergency symptoms immediately.
   - Require patient consult with licensed physicians for prescriptions.
3. **Structured Response Format**:
   - Summary & Clinical Overview
   - Possible Etiology & Risk Factors
   - Safe Home Care & Lifestyle Guidance
   - Pharmaceutical Details & Contraindications (if requested)
   - Emergency Red-Flag Warning Signs
   - When to Seek Urgent Medical Care
   - Verifiable Sources & Safety Disclaimer
4. **Follow-Up Inquiries**: Suggests 3 relevant follow-up questions to guide patient exploration.
