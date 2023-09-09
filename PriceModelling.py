import decimal

def storage_ebay_to_amazon(total_source_price):
    total_source_price = float(total_source_price)
    ebay_shipping_cost = 0
    selling_credit_received = 2.8
    storage_cost = 0
    delivery_fee_to_customer = 2.99
    variable_closing_fee = 1.2
    expected_refund_cost = 0

    # Amazon Referral Fee = 5.1% if TSP<£5
    total_selling_price_to_breakeven = (1/0.9388) * (total_source_price+ebay_shipping_cost-selling_credit_received+
                                                     storage_cost+delivery_fee_to_customer+variable_closing_fee+
                                                     expected_refund_cost+0.17136)
    if total_selling_price_to_breakeven < 5:
        amazon_referral_fee_excluding_VAT = 0.051 * total_selling_price_to_breakeven
    else:
        # Amazon Referral Fee = 15.3% if TSP>=£5
        total_selling_price_to_breakeven = (1 / 0.8164) * (
                    total_source_price + ebay_shipping_cost - selling_credit_received +
                    storage_cost + delivery_fee_to_customer + variable_closing_fee +
                    expected_refund_cost + 0.51408)
        amazon_referral_fee_excluding_VAT = 0.153 * total_selling_price_to_breakeven

    amazon_referral_fee_including_VAT = 1.2 * amazon_referral_fee_excluding_VAT

    total_selling_price_to_breakeven = decimal.Decimal(total_selling_price_to_breakeven)
    #print(type(total_selling_price_to_breakeven))

    return total_selling_price_to_breakeven


def storage_amazon_to_ebay(total_source_price):
    total_source_price = float(total_source_price)
    amazon_shipping_cost = 0
    storage_cost = 0
    delivery_fee_to_customer = 2.99
    listing_fee = 0
    final_value_fee = 1.2
    expected_refund_cost = 0

    # Amazon Referral Fee = 5.1% if TSP<£5
    total_selling_price_to_breakeven = (1 / 0.872) * (
                total_source_price + amazon_shipping_cost +
                storage_cost + delivery_fee_to_customer + listing_fee +
                expected_refund_cost + 0.3)
    final_value_fee = (0.128 * total_selling_price_to_breakeven) +0.3

    total_selling_price_to_breakeven = decimal.Decimal(total_selling_price_to_breakeven)

    return total_selling_price_to_breakeven


def main():
    #print("Price (storage_ebay_to_amazon): "+ str(storage_ebay_to_amazon(7)))

    for tsp in range(1, 101):
        print(str(tsp) + "|| Price (storage_ebay_to_amazon): " + str(storage_ebay_to_amazon(tsp)))

    # For intervals of 0.1:
    # xs = (x * 0.1 for x in range(1, 1010))
    # for tsp in xs:
    #     print(str(tsp) + "|| Price (storage_ebay_to_amazon): " + str(storage_ebay_to_amazon(tsp)))


if __name__ == "__main__":
    main()