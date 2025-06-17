from scrape_data.scrape_discourse import scrape_discourse_forum
from scrape_data.scrape_sanand import scrape_sanand_net



def main():
    print("🔍 Starting scrapers...\n")

    scrape_sanand_net()
    scrape_discourse_forum()

    import json

    with open("data/discourse_forum.json", "r", encoding="utf-8") as f1:
        data1 = json.load(f1)
    with open("data/tds_content.json", "r", encoding="utf-8") as f2:
        data2 = json.load(f2)

    combined_data = data1 + data2

    with open("data/combined_data.json", "w", encoding="utf-8") as out_file:
        json.dump(combined_data, out_file, ensure_ascii=False, indent=2)

    print("✅ Combined data saved to 'combined_data.json'")
    print("\n✅ All scraping jobs complete!")
    print("\n➡️ Data (.json) saved in 'data/' directory.\n")

if __name__ == "__main__":
    main()
