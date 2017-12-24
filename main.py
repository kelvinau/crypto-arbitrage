import argparse
import json

configFile = 'arbitrage_config.json'

f = open(configFile)    
config = json.load(f)
f.close()

parser = argparse.ArgumentParser(description='Crypto Arbitrage')
parser.add_argument('-m', '--mode', help='Arbitrage mode: triangular or exchange', required=True)
parser.add_argument('-p', '--production', help='Production mode', action='store_true')
args = parser.parse_args()

engine = None
isMockMode = True if not args.production else False

if args.mode == 'triangular':
    from engines.triangular_arbitrage import CryptoEngineTriArbitrage
    engine = CryptoEngineTriArbitrage(config['triangular'], isMockMode)
elif args.mode == 'exchange':
    from engines.exchange_arbitrage import CryptoEngineExArbitrage
    engine = CryptoEngineExArbitrage(config['exchange'], isMockMode)
else:
    print 'Mode {0} is not recognized'.format(args.mode)

if engine:
    engine.run()
