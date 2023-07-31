def main():
    amazon_link1 = "https://www.amazon.co.uk/Lost-Bookshop-charming-uplifting-perfect-ebook/dp/B0BMF2M8Z6/ref=sr_1_1?crid=ABRXSPSX7LF3&keywords=book&qid=1690835901&sprefix=bo%2Caps%2C245&sr=8-1"
    amazon_link = amazon_link1.split("www.",1)[1]
    print(amazon_link)



if __name__ == "__main__":
    main()