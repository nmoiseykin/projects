"""SQL template rendering with Jinja2."""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Any
from app.core.logging import logger


class SQLTemplateEngine:
    """Engine for rendering SQL templates with Jinja2."""
    
    def __init__(self):
        """Initialize template engine."""
        template_dir = Path(__file__).parent.parent / "sql" / "base_templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        logger.info(f"SQL template engine initialized from {template_dir}")
    
    def render(self, template_name: str, params: Dict[str, Any]) -> str:
        """
        Render a SQL template with given parameters.
        
        Args:
            template_name: Name of template file (e.g., "by_year.sql.j2")
            params: Dictionary of parameters for template
            
        Returns:
            Rendered SQL string
        """
        try:
            template = self.env.get_template(template_name)
            sql = template.render(**params)
            logger.debug(f"Rendered template {template_name} with params: {params}")
            return sql
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise
    
    def render_by_year(self, params: Dict[str, Any]) -> str:
        """Render by_year template."""
        return self.render("by_year.sql.j2", params)
    
    def render_by_dow(self, params: Dict[str, Any]) -> str:
        """Render by_dow template."""
        return self.render("by_dow.sql.j2", params)
    
    def render_by_candle(self, params: Dict[str, Any]) -> str:
        """Render by_candle template."""
        return self.render("by_candle.sql.j2", params)
    
    def render_trades(self, params: Dict[str, Any]) -> str:
        """Render trades template."""
        return self.render("trades.sql.j2", params)
    
    def render_hierarchical(self, params: Dict[str, Any]) -> str:
        """Render hierarchical template."""
        return self.render("hierarchical.sql.j2", params)
    
    def render_ifvg_data(self, params: Dict[str, Any]) -> str:
        """Render iFVG data fetching template."""
        return self.render("ifvg_data.sql.j2", params)
    
    def render_ifvg_path(self, params: Dict[str, Any]) -> str:
        """Render iFVG path simulation template."""
        return self.render("ifvg_path.sql.j2", params)


# Global instance
template_engine = SQLTemplateEngine()

