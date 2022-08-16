import requests
import csv
import sys

def get_items(search_item, min_sold):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': f'https://shopee.ph/search?keyword={search_item}'
    }

    url = f'https://shopee.ph/api/v4/search/search_items?by=relevancy&keyword={search_item}&limit=60&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2'
    result = requests.get(url, headers=headers).json()

    # filtered_items = [item for item in result['items'] if item['item_basic']['historical_sold'] >= 50]

    with open('items2.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(('name', 'price', 'historical_sold'))

        for item in result['items']:
            item_details = item['item_basic']
            if item_details['historical_sold'] >= min_sold:
                print(f"{item_details['name']} -> {item_details['price']/100000} -> {item_details['historical_sold']}")
                writer.writerow((item_details['name'], item_details['price']/100000, item_details['historical_sold']))

if __name__ == "__main__":
    search_item = sys.argv[1]
    min_sold = int(sys.argv[2])
    get_items(search_item, min_sold)