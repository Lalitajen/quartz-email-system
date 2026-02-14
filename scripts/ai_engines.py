"""
Advanced AI engines for Quartz Email System.
Provides intelligent intent detection, personalization, and automation.
"""

import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger('quartz_web')


class SmartIntentDetectionEngine:
    """
    Advanced multi-intent detection using Claude AI.
    Goal: 95%+ accuracy with multi-intent support, sentiment analysis, and confidence scoring.
    """

    # Intent mapping to pipeline stages
    INTENT_STAGE_MAP = {
        'info_request': 2,
        'technical_info_request': 3,
        'sample_request': 4,
        'quotation_request': 5,
        'contract_request': 6,
        'shipping_inquiry': 7,
        'repeat_order': 9,
        'declined': 10,
    }

    def __init__(self, api_key: str):
        """Initialize with Anthropic API key."""
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = "claude-sonnet-4-20250514"
        except ImportError:
            logger.error("anthropic package not installed")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            self.client = None

    def analyze_email_intent(
        self,
        email_body: str,
        subject: str = "",
        current_stage: int = 1,
        email_history: Optional[List[Dict]] = None,
        customer_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze email with advanced AI to detect multiple intents, sentiment, urgency.

        Args:
            email_body: The email body text
            subject: Email subject line
            current_stage: Current pipeline stage (1-10)
            email_history: Previous emails in thread
            customer_context: Additional context (company_name, industry, etc.)

        Returns:
            {
                "primary_intent": "sample_request",
                "secondary_intents": ["pricing_inquiry", "timeline_question"],
                "urgency_level": "high",  # high/medium/low
                "sentiment": "positive",   # positive/neutral/negative/mixed
                "buying_signals": ["ready to order", "budget approved"],
                "objections": ["price concern"],
                "timeline_mentioned": "2 weeks",
                "decision_maker_status": "confirmed",  # confirmed/suspected/unknown
                "next_best_action": "send_sample_quote_combo",
                "recommended_stage": 5,
                "confidence_score": 0.95,
                "detected_keywords": {...},
                "reasoning": "Customer mentioned..."
            }
        """
        if not self.client:
            logger.warning("AI client not available, cannot analyze intent")
            return self._fallback_response()

        try:
            prompt = self._build_intent_analysis_prompt(
                email_body, subject, current_stage, email_history, customer_context
            )

            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,  # Low temp for consistent classification
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Extract JSON from response
            result = self._parse_ai_response(response_text)
            logger.info(f"AI Intent Analysis: {result.get('primary_intent')} (confidence: {result.get('confidence_score', 0)})")
            return result

        except Exception as e:
            logger.error(f"AI intent analysis failed: {e}", exc_info=True)
            return self._fallback_response()

    def _build_intent_analysis_prompt(
        self,
        email_body: str,
        subject: str,
        current_stage: int,
        email_history: Optional[List[Dict]],
        customer_context: Optional[Dict]
    ) -> str:
        """Build comprehensive prompt for intent analysis."""

        context_info = ""
        if customer_context:
            context_info = f"""
**Customer Context:**
- Company: {customer_context.get('company_name', 'Unknown')}
- Industry: {customer_context.get('industry', 'Unknown')}
- Current Stage: {current_stage} (1=Lead, 4=Sample, 5=Quote, 10=Closed)
"""

        history_info = ""
        if email_history and len(email_history) > 0:
            history_info = "\n**Previous Emails in Thread:**\n"
            for i, email in enumerate(email_history[-3:]):  # Last 3 emails
                history_info += f"{i+1}. {email.get('subject', '')[:100]}\n"

        prompt = f"""You are an expert B2B sales intelligence assistant for a high-purity quartz mining and export company.

**Your Task:** Analyze this customer email and extract ALL intents, sentiment, urgency, and buying signals.

{context_info}
{history_info}

**Email Subject:** {subject}

**Email Body:**
{email_body}

---

**Instructions:**
1. **Primary Intent**: The main request/question (choose from: info_request, technical_info_request, sample_request, quotation_request, contract_request, shipping_inquiry, repeat_order, declined)
2. **Secondary Intents**: All other intents detected (list all, even if subtle)
3. **Urgency Level**: high (ASAP, urgent, deadline <7 days), medium (within 2 weeks), low (no urgency)
4. **Sentiment**: positive (enthusiastic, interested), neutral, negative (frustrated, declining), mixed
5. **Buying Signals**: Explicit signs of purchase intent ("budget approved", "ready to order", "need quote by Friday", "expanding production")
6. **Objections**: Any concerns raised ("price too high", "not ready", "using competitor", "need approval")
7. **Timeline Mentioned**: Any specific dates/timeframes mentioned
8. **Decision Maker**: confirmed (they explicitly state authority), suspected (title/role suggests it), unknown
9. **Recommended Stage**: Based on the strongest intent and buying signals, what pipeline stage (1-10) should this customer be in?
10. **Confidence Score**: Your confidence in this analysis (0.0-1.0)
11. **Reasoning**: Brief explanation of your analysis (1-2 sentences)

**Output Format (JSON only, no other text):**
{{
  "primary_intent": "sample_request",
  "secondary_intents": ["pricing_inquiry", "timeline_question"],
  "urgency_level": "high",
  "sentiment": "positive",
  "buying_signals": ["budget approved", "ready to order"],
  "objections": ["delivery timeline concern"],
  "timeline_mentioned": "need by March 15",
  "decision_maker_status": "confirmed",
  "recommended_stage": 5,
  "confidence_score": 0.92,
  "detected_keywords": {{
    "sample": ["sample", "trial"],
    "pricing": ["price", "quote"],
    "urgency": ["ASAP", "urgent"]
  }},
  "reasoning": "Customer explicitly requests sample and pricing with urgent deadline, strong buying signals present.",
  "next_best_action": "send_priority_sample_with_volume_pricing"
}}

**Few-Shot Examples:**

**Example 1:**
Email: "Hi, we're interested in learning more about your high-purity quartz. Can you send a brochure?"
Analysis: {{"primary_intent": "info_request", "secondary_intents": [], "urgency_level": "low", "sentiment": "neutral", "buying_signals": [], "objections": [], "timeline_mentioned": null, "decision_maker_status": "unknown", "recommended_stage": 2, "confidence_score": 0.95, "detected_keywords": {{"info": ["interested", "brochure"]}}, "reasoning": "Basic information request with no urgency or buying signals.", "next_best_action": "send_company_overview_brochure"}}

**Example 2:**
Email: "We need a 5kg sample ASAP for our new semiconductor fab. Also, what's your pricing for 10-ton monthly orders? Our purchasing manager wants quotes from 2-3 suppliers before Q3. Current supplier raised prices 15%."
Analysis: {{"primary_intent": "sample_request", "secondary_intents": ["quotation_request", "supplier_evaluation"], "urgency_level": "high", "sentiment": "positive", "buying_signals": ["new semiconductor fab", "10-ton monthly orders", "Q3 deadline", "purchasing manager involved"], "objections": ["competitor evaluation", "current supplier price increase"], "timeline_mentioned": "ASAP for sample, Q3 for decision", "decision_maker_status": "confirmed", "recommended_stage": 5, "confidence_score": 0.96, "detected_keywords": {{"sample": ["5kg sample", "ASAP"], "pricing": ["pricing", "quotes"], "urgency": ["ASAP", "before Q3"]}}, "reasoning": "Multi-intent with strong buying signals, competitive context, and confirmed decision maker involvement. Skip directly to quotation stage.", "next_best_action": "send_priority_sample_with_volume_pricing_and_competitive_positioning"}}

**Example 3:**
Email: "Thanks but we've decided to go with another supplier. Please remove us from your mailing list."
Analysis: {{"primary_intent": "declined", "secondary_intents": ["unsubscribe"], "urgency_level": "low", "sentiment": "negative", "buying_signals": [], "objections": ["chose competitor"], "timeline_mentioned": null, "decision_maker_status": "unknown", "recommended_stage": 10, "confidence_score": 0.98, "detected_keywords": {{"decline": ["decided to go with another", "remove from mailing list"]}}, "reasoning": "Clear rejection with competitor selection. Move to closed/lost stage.", "next_best_action": "mark_as_lost_and_unsubscribe"}}

**Example 4:**
Email: "Can you provide the technical specs and ICP analysis report for your HPQ-99.99 grade? We need SiO2 purity data."
Analysis: {{"primary_intent": "technical_info_request", "secondary_intents": [], "urgency_level": "medium", "sentiment": "neutral", "buying_signals": ["specific product grade interest"], "objections": [], "timeline_mentioned": null, "decision_maker_status": "suspected", "recommended_stage": 3, "confidence_score": 0.90, "detected_keywords": {{"technical": ["technical specs", "ICP analysis", "SiO2 purity"]}}, "reasoning": "Technical evaluation phase, likely technical buyer. Provide detailed specs.", "next_best_action": "send_technical_data_sheet_and_icp_report"}}

Now analyze the email above and return ONLY the JSON object:"""

        return prompt

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Extract and validate JSON from AI response."""
        # Find JSON object in response
        try:
            # Try to find JSON block
            if '{' in response_text and '}' in response_text:
                start = response_text.index('{')
                end = response_text.rindex('}') + 1
                json_str = response_text[start:end]
                result = json.loads(json_str)

                # Validate required fields
                required = ['primary_intent', 'confidence_score', 'recommended_stage']
                for field in required:
                    if field not in result:
                        logger.warning(f"AI response missing field: {field}")
                        return self._fallback_response()

                # Ensure defaults for optional fields
                result.setdefault('secondary_intents', [])
                result.setdefault('urgency_level', 'medium')
                result.setdefault('sentiment', 'neutral')
                result.setdefault('buying_signals', [])
                result.setdefault('objections', [])
                result.setdefault('timeline_mentioned', None)
                result.setdefault('decision_maker_status', 'unknown')
                result.setdefault('detected_keywords', {})
                result.setdefault('reasoning', 'AI analysis completed')
                result.setdefault('next_best_action', 'review_and_respond')

                return result
            else:
                logger.error("No JSON found in AI response")
                return self._fallback_response()

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {e}")
            return self._fallback_response()
        except Exception as e:
            logger.error(f"Error processing AI response: {e}")
            return self._fallback_response()

    def _fallback_response(self) -> Dict[str, Any]:
        """Return a safe fallback when AI analysis fails."""
        return {
            "primary_intent": "general_reply",
            "secondary_intents": [],
            "urgency_level": "medium",
            "sentiment": "neutral",
            "buying_signals": [],
            "objections": [],
            "timeline_mentioned": None,
            "decision_maker_status": "unknown",
            "recommended_stage": None,  # Don't auto-advance on fallback
            "confidence_score": 0.0,
            "detected_keywords": {},
            "reasoning": "AI analysis unavailable, manual review required",
            "next_best_action": "manual_review"
        }

    def get_stage_from_intent(self, intent: str) -> Optional[int]:
        """Map intent to pipeline stage."""
        return self.INTENT_STAGE_MAP.get(intent)


class EmailPersonalizationEngine:
    """
    Enhanced email personalization with context awareness.
    (To be implemented in Phase 2)
    """
    pass


class SmartPipelineEngine:
    """
    AI-powered pipeline stage management with confidence scoring.
    (To be implemented in Phase 3)
    """
    pass


class ObjectionHandlingEngine:
    """
    Detect and respond to sales objections using AI playbook.
    (To be implemented in Phase 3)
    """
    pass


class EmailQualityEngine:
    """
    Analyze and score email quality using AI rubric.
    (To be implemented in Phase 4)
    """
    pass


class ConversationMemoryEngine:
    """
    Track and recall conversation history across emails.
    (To be implemented in Phase 4)
    """
    pass
