"""AI service for scenario suggestions and explanations."""
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.core.logging import logger
from app.models.backtest import ScenarioParams, BacktestResult


class AIService:
    """Service for AI-powered features."""
    
    def __init__(self):
        """Initialize AI service."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set - AI features will be disabled")
            self.client = None
        else:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model_reasoning = "gpt-4-turbo-preview"
        self.model_fast = "gpt-4o-mini"
    
    async def suggest_scenarios(
        self,
        recent_results: Optional[List[Dict[str, Any]]] = None,
        context: Optional[str] = None,
        num_scenarios: int = 10
    ) -> List[ScenarioParams]:
        """
        Generate scenario suggestions based on recent results.
        
        Args:
            recent_results: Recent backtest results
            context: Additional context string
            
        Returns:
            List of suggested scenarios
        """
        if not self.client:
            logger.warning("AI service not available - returning empty suggestions")
            return []
        
        try:
            # Prepare context
            results_text = ""
            if recent_results:
                results_text = "\n".join([
                    f"Win Rate: {r.get('win_rate_percent', 0)}%, "
                    f"Trades: {r.get('total_trades', 0)}, "
                    f"Expectancy: {r.get('expectancy_r', 0)}R"
                    for r in recent_results[:10]
                ])
            
            system_prompt = f"""You are a quantitative strategy planner. Given backtest results, propose {num_scenarios} new scenarios to test.
Output ONLY valid JSON array of scenario objects. Each scenario must have:
- entry_time_start: string in HH:MM:SS format (start of entry time window)
- entry_time_end: string in HH:MM:SS format (end of entry time window)
- trade_end_time: string in HH:MM:SS format (when trade window closes, default 16:00:00 for 4pm)
- target_pts: number (positive)
- stop_pts: number (positive)
- direction: "bullish", "bearish", or null
- year_start: integer (2000-2100)
- year_end: integer (2000-2100)

IMPORTANT: entry_time_start and entry_time_end define a WINDOW where trades can be entered.
Each trade runs until trade_end_time (default 4pm) or until SL/TP is hit.
If neither SL nor TP is hit by trade_end_time, it's considered a timeout.

Vary parameters intelligently. Focus on robust clusters with high trade counts."""
            
            user_prompt = f"""Recent results:
{results_text if results_text else "No recent results"}

{context if context else ""}

Generate {num_scenarios} new scenarios as JSON array."""
            
            # Request JSON format
            system_prompt_json = system_prompt + "\n\nOutput a JSON object with a 'scenarios' array containing the scenario objects."
            
            response = self.client.chat.completions.create(
                model=self.model_fast,
                messages=[
                    {"role": "system", "content": system_prompt_json},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            # Parse response
            content = response.choices[0].message.content
            import json
            data = json.loads(content)
            
            # Extract scenarios array
            scenarios_data = data.get("scenarios", [])
            
            # Clean up the data - convert string "null" to None, handle direction enum
            cleaned_scenarios = []
            for s in scenarios_data:
                # Convert string "null" to None
                if s.get("direction") == "null" or s.get("direction") == "None":
                    s["direction"] = None
                # Ensure direction is valid enum or None
                if s.get("direction") not in [None, "bullish", "bearish", "neutral"]:
                    s["direction"] = None
                cleaned_scenarios.append(s)
            
            # If direction is not specified (None), generate scenarios for both directions
            expanded_scenarios = []
            for s in cleaned_scenarios:
                if s.get("direction") is None:
                    # Create two scenarios: one bullish, one bearish
                    s_bullish = s.copy()
                    s_bullish["direction"] = "bullish"
                    expanded_scenarios.append(s_bullish)
                    
                    s_bearish = s.copy()
                    s_bearish["direction"] = "bearish"
                    expanded_scenarios.append(s_bearish)
                else:
                    expanded_scenarios.append(s)
            
            scenarios = [ScenarioParams(**s) for s in expanded_scenarios]
            
            logger.info(f"Generated {len(scenarios)} AI suggestions (expanded for both directions when not specified)")
            return scenarios
            
        except Exception as e:
            logger.error(f"Error generating AI suggestions: {e}", exc_info=True)
            # Re-raise the exception so the API can handle it properly
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def explain_strategy(
        self,
        results: List[BacktestResult],
        context: Optional[str] = None
    ) -> str:
        """
        Generate strategy explanation from results.
        
        Args:
            results: List of backtest results
            context: Additional context
            
        Returns:
            Markdown-formatted explanation
        """
        if not self.client:
            logger.warning("AI service not available - returning placeholder")
            return "# Strategy Explanation\n\nAI service not configured."
        
        try:
            # Prepare results summary
            results_summary = []
            for r in results[:20]:  # Limit to first 20
                kpis = r.kpis
                grouping = r.grouping
                results_summary.append({
                    "grouping": grouping,
                    "win_rate": kpis.win_rate_percent,
                    "trades": kpis.total_trades,
                    "expectancy": kpis.expectancy_r
                })
            
            system_prompt = """You are a trading strategist. Analyze backtest results and provide:
1. Setup description
2. Key statistics summary
3. Why it works (edge explanation)
4. What to do (actionable checklist)
5. Risks and warnings
6. Trading checklist

Output in markdown format with clear headings and bullet points."""
            
            user_prompt = f"""Backtest Results:
{str(results_summary)}

{context if context else ""}

Provide a comprehensive strategy explanation."""
            
            response = self.client.chat.completions.create(
                model=self.model_reasoning,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5
            )
            
            explanation = response.choices[0].message.content
            logger.info("Generated AI strategy explanation")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating AI explanation: {e}")
            return f"# Error\n\nFailed to generate explanation: {str(e)}"
    
    async def analyze_strategy(
        self,
        results: List[BacktestResult],
        context: Optional[str] = None
    ) -> str:
        """
        Analyze strategy viability, testing adequacy, trustworthiness, and provide recommendations.
        
        Args:
            results: List of backtest results
            context: Additional context
            
        Returns:
            Markdown-formatted analysis
        """
        if not self.client:
            logger.warning("AI service not available - returning placeholder")
            return "# Strategy Analysis\n\nAI service not configured."
        
        try:
            # Prepare comprehensive results summary
            results_summary = []
            total_trades = 0
            total_wins = 0
            total_losses = 0
            total_timeouts = 0
            expectancies = []
            profit_factors = []
            
            for r in results[:50]:  # Limit to first 50 results
                kpis = r.kpis
                grouping = r.grouping
                totals = r.totals or {}
                
                total_trades += kpis.total_trades
                total_wins += totals.get('wins', 0)
                total_losses += totals.get('losses', 0)
                total_timeouts += totals.get('timeouts', 0)
                
                if kpis.expectancy_r is not None:
                    expectancies.append(kpis.expectancy_r)
                if kpis.profit_factor is not None:
                    profit_factors.append(kpis.profit_factor)
                
                results_summary.append({
                    "grouping": grouping,
                    "win_rate": kpis.win_rate_percent,
                    "trades": kpis.total_trades,
                    "wins": totals.get('wins', 0),
                    "losses": totals.get('losses', 0),
                    "timeouts": totals.get('timeouts', 0),
                    "expectancy": kpis.expectancy_r,
                    "profit_factor": kpis.profit_factor
                })
            
            avg_expectancy = sum(expectancies) / len(expectancies) if expectancies else 0
            avg_profit_factor = sum(profit_factors) / len(profit_factors) if profit_factors else 0
            overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
            
            system_prompt = """You are an expert quantitative trading strategist and risk analyst. Analyze backtest results and provide a comprehensive evaluation covering:

1. **Strategy Viability Assessment**
   - Is this a viable trading strategy? (Yes/No/Maybe with reasoning)
   - What are the key strengths and weaknesses?
   - What market conditions does it work best in?

2. **Testing Adequacy**
   - Has enough testing been done? (Consider sample size, time period, market conditions)
   - What additional testing would strengthen confidence?
   - Are there any gaps in the test coverage?

3. **Trustworthiness & Reliability**
   - Should I trust this strategy? (High/Medium/Low confidence)
   - What are the main risks and concerns?
   - What could cause this strategy to fail?

4. **Recommendations for Improvement**
   - Specific, actionable recommendations to improve the strategy
   - Parameter optimizations
   - Risk management enhancements
   - Entry/exit refinements

Output in clear markdown format with headings, bullet points, and specific numbers/metrics. Be honest and critical - highlight both strengths and weaknesses."""
            
            user_prompt = f"""Backtest Results Summary:
- Total Results Analyzed: {len(results_summary)}
- Total Trades: {total_trades:,}
- Total Wins: {total_wins:,}
- Total Losses: {total_losses:,}
- Total Timeouts: {total_timeouts:,}
- Overall Win Rate: {overall_win_rate:.2f}%
- Average Expectancy: {avg_expectancy:.3f}R
- Average Profit Factor: {avg_profit_factor:.2f}

Detailed Results:
{str(results_summary[:20])}  # First 20 for context

{context if context else ""}

Provide a comprehensive strategy analysis addressing viability, testing adequacy, trustworthiness, and recommendations."""
            
            response = self.client.chat.completions.create(
                model=self.model_reasoning,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            analysis = response.choices[0].message.content
            logger.info("Generated AI strategy analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}", exc_info=True)
            return f"# Error\n\nFailed to generate analysis: {str(e)}"


# Global instance
ai_service = AIService()

