import sys
import os
sys.path.append(os.path.dirname(__file__))

class EngineLoader(object):
    @staticmethod
    def getEngine(exchange, keyFile):
        mod = __import__(exchange)
        engine = mod.ExchangeEngine()
        engine.load_key(keyFile)
        return engine
    