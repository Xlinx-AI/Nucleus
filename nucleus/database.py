"""
AgentStorage for nucleus: manages agent configurations, flags, templates, and persistence.
If you want to keep your agents organized, this is your tired junior's friend.
"""

import logging

class AgentStorage:
    """
    This class handles agent storage, config, flags, and templates using PandasDB or whatever DB you use.
    """
    def __init__(self, db=None):
        self.logger = logging.getLogger("AgentStorage")
        self.db = db or {}  # In production, plug your PandasDB or real DB here.
        self.agents = {}

    def save_agent(self, agent_id, config):
        self.agents[agent_id] = config
        self.logger.info(f"Agent '{agent_id}' saved.")

    def load_agent(self, agent_id):
        return self.agents.get(agent_id, None)

    def purge_agents(self):
        self.agents.clear()
        self.logger.info("All agents purged.")

    def list_agents(self):
        return list(self.agents.keys())

    def get_agent_config(self, agent_id):
        return self.agents.get(agent_id, {})

    def create_agent_from_template(self, template_name, agent_id, custom_config=None):
        config = {"template": template_name, "custom": custom_config or {}}
        self.save_agent(agent_id, config)
        self.logger.info(f"Agent '{agent_id}' created from template '{template_name}'.")
        return config