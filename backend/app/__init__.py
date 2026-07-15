# Avoid importing app at package import time (keeps tests lightweight)
__all__ = ["main"]
