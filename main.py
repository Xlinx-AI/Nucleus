"""Main entry point for the Universal Iterative AI Hub.

Initializes and connects all core modules, sets up dependencies, and starts the UI server.
All comments and docstrings are in English. No legacy code remains.
"""

from nucleus.app_core import ApplicationCore
from nucleus.skill_manager import SkillManager

def main():
    # Initialize core application
    app_core = ApplicationCore()
    # Inject SkillManager into AgentSystem for tight integration
    app_core.agent_system.skill_manager = app_core.skill_manager
    # Optionally, load or register additional skills, configs, etc. here

    # Start the UI server (FastAPI)
    app_core.ui_server.run(host="127.0.0.1", port=8080)

if __name__ == "__main__":
    main()