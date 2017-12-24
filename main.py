import argparse
import json

configFile = 'arbitrage_config.json'

f = open(configFile)    
config = json.load(f)
f.close()

parser = argparse.ArgumentParser(description='Crypto Arbitrage')
parser.add_argument('-m', '--mode', help='Arbitrage mode: triangular or exchange', required=True)
args = parser.parse_args()

engine = None
if args.mode == 'triangular':
    from engines.triangular_arbitrage import CryptoEngineTriArbitrage
    engine = CryptoEngineTriArbitrage(config['triangular'], True)
elif args.mode == 'exchange':
    from engines.exchange_arbitrage import CryptoEngineExArbitrage
    engine = CryptoEngineExArbitrage(config['exchange'], True)
else:
    print 'Mode {0} is not recognized'.format(args.mode)

if engine:
    engine.run()
