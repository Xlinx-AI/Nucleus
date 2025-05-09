"""
Base and specialized error classes for the agent platform (with exit codes).
Author: 
"""

class AgentPlatformError(Exception):
    """Base error for agent platform."""
    exit_code = 1

class AuthenticationError(AgentPlatformError):
    """Authentication error (like invalid token)."""
    exit_code = 4

class BuildError(AgentPlatformError):
    """Build or packaging error."""
    exit_code = 7

class ConfigError(AgentPlatformError):
    """Config or parameter error."""
    exit_code = 9

class OperationError(AgentPlatformError):
    """Error during agent/tool operation."""
    exit_code = 6

class DataExtractError(AgentPlatformError):
    """Error extracting or processing data."""
    exit_code = 5

class NetworkError(AgentPlatformError):
    """Network interaction error."""
    exit_code = 2

class PublishError(AgentPlatformError):
    """Error publishing or releasing a package."""
    exit_code = 8

class ResourceNotFound(AgentPlatformError):
    """Requested resource not found."""
    exit_code = 3

class MCPError(Exception):
    """Base error for MCP protocol."""
    pass

class MCPTransportError(MCPError):
    """Transport-level MCP error."""
    pass