import logging
import re
from typing import Optional
from openai import AsyncOpenAI

from ...config import settings

logger = logging.getLogger("codeatlas.search.intent")

class IntentDetectionService:
    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
        self.intents = [
            "code_discovery", 
            "dependency_analysis", 
            "impact_analysis", 
            "architecture_understanding"
        ]

    def _heuristic_match(self, query: str) -> Optional[str]:
        """Fast regex-based intent classification."""
        query_lower = query.lower()
        
        # Impact Analysis
        if re.search(r'\b(break|breaks|change|changes|modify|modifying|impact|affected|affect)\b', query_lower):
            return "impact_analysis"
            
        # Dependency Analysis
        if re.search(r'\b(depends on|dependencies|import|imports|uses|calls|called by)\b', query_lower):
            return "dependency_analysis"
            
        # Architecture Understanding
        if re.search(r'\b(flow|architecture|lifecycle|explain|how does|how is|structure)\b', query_lower):
            return "architecture_understanding"
            
        # Code Discovery (Default / generic)
        if re.search(r'\b(where|find|show|which)\b', query_lower):
            return "code_discovery"
            
        return None

    async def detect_intent(self, query: str) -> str:
        """
        Detects the search intent. Tries fast heuristics first. 
        Falls back to LLM if ambiguity exists or heuristics fail.
        """
        # Try heuristic first for < 5ms latency
        intent = self._heuristic_match(query)
        if intent:
            logger.debug(f"Intent detected via heuristics: {intent}")
            return intent
            
        # Fallback to LLM
        if not self.openai_client:
            logger.warning("No OpenAI key available for intent detection. Defaulting to code_discovery.")
            return "code_discovery"
            
        try:
            logger.debug("Falling back to LLM for intent detection.")
            prompt = f"""
            Classify the following software engineering search query into exactly ONE of these categories:
            - code_discovery (finding specific implementations or files)
            - dependency_analysis (finding what components rely on others)
            - impact_analysis (understanding what breaks if a change is made)
            - architecture_understanding (high-level system flows, lifecycles, and design)
            
            Query: "{query}"
            
            Respond with ONLY the category string, nothing else.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip().lower()
            if result in self.intents:
                return result
            else:
                logger.warning(f"Unexpected LLM intent output: {result}. Defaulting to code_discovery.")
                return "code_discovery"
                
        except Exception as e:
            logger.error(f"LLM intent detection failed: {e}")
            return "code_discovery"
