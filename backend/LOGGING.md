# Logging Configuration for detective-L

## Overview

The detective-L backend uses Python's built-in `logging` module with a centralized configuration in `app/core/logging_config.py`.

## How It Works

### Initialization
When the backend starts, `logging_config.py` is imported, which automatically:
- Creates a `logs/` directory in the backend folder
- Sets up file rotation (max 10MB per file, keeps 5 backup files)
- Configures both console and file handlers
- Applies consistent formatting across all loggers

### Log Locations
- **Console**: Prints INFO and above to terminal (real-time feedback during development)
- **Files**: Stores DEBUG and above in `backend/logs/detective-L_YYYYMMDD.log`
  - One log file per day
  - Old files are rotated automatically when they reach 10MB

### Log Format
```
2026-04-24 10:30:45 | INFO     | app.agents.planner:45 | Processing query: What are...
```

Structure: `timestamp | level | module:line | message`

## Usage in Code

### Getting a Logger
```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Log at different levels
logger.debug("Detailed debug info")
logger.info("Normal operation")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical issue")
```

### Log Levels
- **DEBUG**: Detailed diagnostic information (e.g., LLM chain invocations, large data structures)
- **INFO**: Confirmation of successful operations (e.g., agents completing, number of results)
- **WARNING**: Warning conditions (e.g., low confidence claims, missing data)
- **ERROR**: Error conditions with traceback
- **CRITICAL**: Critical failures requiring immediate attention

## Current Implementation

### Integrated Modules
All agent nodes now include comprehensive logging:
- `app/agents/planner.py`: Logs query processing and subtopic generation
- `app/agents/web_researcher.py`: Logs search queries and results found
- `app/agents/synthesis.py`: Logs finding merging and report generation
- `app/agents/critic.py`: Logs claim analysis and confidence scores
- `app/agents/revisor.py`: Logs report improvements and feedback
- `app/agents/formatter.py`: Logs final report structure creation
- `app/core/graph.py`: Logs pipeline start/completion and statistics

### Exception Handling
All critical functions log exceptions with full traceback:
```python
try:
    result = some_operation()
except Exception as e:
    logger.error(f"Operation failed: {str(e)}", exc_info=True)
    raise
```

## Accessing Logs

### View Recent Logs
```bash
# On Windows PowerShell
Get-Content backend\logs\detective-L_*.log -Tail 100

# On Linux/Mac
tail -f backend/logs/detective-L_*.log
```

### Filter by Level
```bash
# Find all ERROR logs
Select-String "ERROR" backend\logs\detective-L_*.log

# Find all INFO logs from a specific agent
Select-String "critic_node|INFO" backend\logs\detective-L_*.log
```

### Search by Message
```bash
# Find all instances of failed operations
Select-String "Error|Failed" backend\logs\detective-L_*.log
```

## Configuration Options

To adjust logging behavior, edit `app/core/logging_config.py`:

```python
# Change console log level (affects what prints to terminal)
setup_logging(level=logging.DEBUG)  # Show more detail

# Disable console output
setup_logging(console=False)

# Change log file path
setup_logging(log_file="custom/path/logfile.log")
```

## Performance Considerations

- Logging is asynchronous for file I/O (minimal impact on graph execution)
- File rotation prevents logs from consuming excessive disk space
- DEBUG level is written to files but not console (reduces terminal clutter during normal operation)
- Each agent function logs start, completion, and errors

## Monitoring in Production

For production deployments:
1. Configure external log aggregation (e.g., ELK Stack, Datadog)
2. Set `level=logging.WARNING` in `setup_logging()` to reduce noise
3. Implement alerts for ERROR and CRITICAL level logs
4. Archive old log files regularly
