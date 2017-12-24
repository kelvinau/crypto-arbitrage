class RuleChecker:
    def __init__(self):
        pass

    '''
    data: a list of data that has the format {'price': 0.5}, sorted by time descending
    '''
    def check(self, rule, data):
        return getattr(self, rule)(data)

    def oldest_newest_single_larger_than_5per(self, tickerData):
        data = tickerData['data']
        print data
        return True
    
    def oldest_latest_avg_of_5_larger_than_5per(self, tickerData):
        data = tickerData['data']
        parsedData = list(map(lambda x: float(x['price']), data))

        if len(data) < 10:
            print "Failed for rule oldest_latest_avg_of_5_larger_than_5per: There are fewer than 10 data"
            return False

        latestAvg = sum(parsedData[:5]) / 5.0
        oldestAvg = sum(parsedData[-5:]) / 5.0
        
        percentageChange = 100 * (latestAvg - oldestAvg) / oldestAvg
        
        msg = '{0} - {1} - oldest_latest_avg_of_5_larger_than_5per: {2}%'.format(tickerData['exchange'], tickerData['ticker'], percentageChange)
        if (abs(percentageChange) > 5):
            print '!!!ALERT!!! ' + msg + ' !!!ALERT!!!'
            return True
        print msg
        return False
    
if __name__ == '__main__':

    data = [{'price': 4615}, {'price': 4615}, {'price': 4380}, {'price': 3935.1}, {'price': 4149.9}, {'price': 3918}, {'price': 3850}, {'price': 3720}, {'price': 3700}, {'price': 3579.7}, {'price': 3499.8}, {'price': 3499.1}, {'price': 3699.8}, {'price': 3577}, {'price': 3577.1}, {'price': 3644.6}, {'price': 3546.3}, {'price': 3480.2}, {'price': 3354.8}, {'price': 3310.6}, {'price': 3132.1}, {'price': 3152.1}, {'price': 2995.2}, {'price': 3167}, {'price': 3387}, {'price': 3374.3}, {'price': 3421.1}, {'price': 3091.8}, {'price': 2993}, {'price': 3092.7}, {'price': 2947.9}, {'price': 3254.4}, {'price': 3540}, {'price': 3514.3}, {'price': 3474.1}, {'price': 3601.6}, {'price': 3750}, {'price': 3947.4}, {'price': 3892.3}, {'price': 3653.6}, {'price': 3588.9}, {'price': 3774.7}, {'price': 3863.6}, {'price': 4051.2}, {'price': 3946.5}, {'price': 3827.9}, {'price': 3811.7}, {'price': 3619}, {'price': 3671.9}, {'price': 3661}, {'price': 3751.7}, {'price': 3592.3}, {'price': 3601.2}, {'price': 3396.9}, {'price': 3458.4}, {'price': 3508.4}, {'price': 3424.8}, {'price': 3670.5}, {'price': 3772.1}, {'price': 3674.8}, {'price': 3454.21}, {'price': 3602}, {'price': 3357.9}, {'price': 3283.7}, {'price': 3042.3}, {'price': 2927.9}, {'price': 2814.1}, {'price': 2900.7}, {'price': 2834.7}, {'price': 2729.5}, {'price': 2705.7}, {'price': 2438.5}, {'price': 2341}, {'price': 2279.4}, {'price': 2309}, {'price': 2321.1}, {'price': 2201.7}, {'price': 2287.2}, {'price': 2368.2}, {'price': 2172}, {'price': 2091}, {'price': 2196.7}, {'price': 2363.1}, {'price': 2361.3}, {'price': 2365.5}, {'price': 2358.3}, {'price': 2241.3}, {'price': 2050}, {'price': 2000}, {'price': 1888.52}, {'price': 1686.05}, {'price': 1851.1199}, {'price': 1999}, {'price': 2087.9999}, {'price': 2059.6}, {'price': 2137.94}, {'price': 2140}, {'price': 2247.81705}, {'price': 2235.185}, {'price': 2260.62005}]

    checker = RuleChecker('gatecoin')
    print checker.check('oldest_latest_avg_of_5_larger_than_5per', data)
    