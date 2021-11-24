from spot.prices.aws_price_retriever import AWSPriceRetriever

def main():
    retriever = AWSPriceRetriever()
    print(retriever.get_current_prices())

if __name__ == '__main__':
    main()
