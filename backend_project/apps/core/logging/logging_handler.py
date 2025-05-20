import logging
import inspect
from ..models import LogEntry

class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        level = record.levelname
        message = log_entry
        module = record.module if hasattr(record, 'module') else None

        frame = inspect.currentframe().f_back
        filepath = inspect.getfile(frame)
        function_name = frame.f_code.co_name

        module_info = f"{function_name} -> {module} in {filepath}"

        LogEntry.objects.create(level=level, message=message, module=module_info)
