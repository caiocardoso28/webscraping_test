import time
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
url = "https://cruisedirect.com/destination/"
locations = ["alaska",
             "bermuda",
             "hawaii",
             "world-cruise",
             "asia",
             "canada-new-england",
             "mediterranean",
             "australia-new-zealand",
             "caribbean",
             "mexico",
             "bahamas",
             "europe",
             "panama-canal"]


def extract_cell_data(idx, cell):
    if idx == 0:
        # print(f"{idx}.\n{cell.find('p').text}")
        return cell.find('p').text
    elif idx == 1:
        return "NA"
    elif 2 <= idx <= 5:
        # print(f"{idx}.\n{cell.text[1:].replace('USD', '')}")
        return cell.text[1:].replace('USD', '')
    elif idx == 6:
        return "NA"


def create_pricing_table(table, nights, destination, cruise_line=None):
    headers_html = table.findAll("tr")[0]
    headers = headers_html.findAll('th')
    headers = [header.text for header in headers]
    print()
    rows = table.findAll("tr")[1:]
    entries = []
    for row in rows:
        row_items = []
        for idx, cell in enumerate(row.findAll('td')):
            # print(extract_cell_data(idx, cell))
            row_items.append(extract_cell_data(idx, cell))

        entries.append(row_items)
    # print(entries)

    df = pd.DataFrame({
        headers[0]: [entry[0] for entry in entries],
        headers[1]: [entry[1] for entry in entries],
        headers[2]: [entry[2] for entry in entries],
        headers[3]: [entry[3] for entry in entries],
        headers[4]: [entry[4] for entry in entries],
        headers[5]: [entry[5] for entry in entries],
        "Destination": [destination for entry in entries],
        "Nights": [nights for entry in entries],
        "Cruise Line": [cruise_line for entry in entries]
    })
    print(df)
    return df


def get_category_prices(category, base_url):
    url_valid = True
    page = ""
    counter = 0
    frames = []
    while url_valid and counter <= 2:
        print(f"Page {counter}")
        response = requests.get(f"{base_url}{category}{page}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # GRAB LISTING DIV CONTAINER
            listings = soup.find_all('div', class_=re.compile('card-sec mt-3 mb-5 p-0'))
            count = 0
            for listing in listings:
                count += 1
                # GRAB CRUISE TYPE AND DESTINATION
                type_info_list = listing.find("h4", class_="fw-b").text.split(" ")[10:15]
                number_of_nights = type_info_list[0]
                img_section = listing.find("section",
                                           class_="d-flex justify-content-center align-items-center py-3 px-1"
                                           )
                img = img_section.find('img')
                img_url = img['data-src']
                img_name = img_url.split('/')[-1]
                img_name_array = img_name.split(".")[0].split("-")
                if len(img_name_array) > 2:
                    cruise_line_array = img_name_array[:len(img_name_array)-1]
                    cruise_line_name = ""
                    for name in cruise_line_array:
                        if len(cruise_line_name) < 1:
                            cruise_line_name += name
                        else:
                            cruise_line_name += " " + name
                else:
                    cruise_line_name = img_name_array[0]
                print(cruise_line_name)
                if type_info_list[3] != "CRUISE" and type_info_list[3] != "Cruise":
                    destination_location = type_info_list[2] + " " + type_info_list[3]
                else:
                    destination_location = type_info_list[2]

                # CREATE DATA TABLE FOR LISTING
                table = listing.find("table", class_="table_data table table-bordered sailing-result-table m-0 mob-0")
                frame_table = create_pricing_table(table, number_of_nights, destination_location, cruise_line_name )
                frames.append(frame_table)
                print()
                print()
            counter += 1
            page = f"?={count}"
            time.sleep(1)
        else:
            url_valid = False

    result = pd.concat(frames, ignore_index=True)
    # result.to_csv("test_doc")
    return result


def get_all_prices(categories):
    all_frames = []

    for category in categories:
        all_frames.append(get_category_prices(category, url))

    final = pd.concat(all_frames, ignore_index=True)
    final.to_csv('test_doc.csv')


get_all_prices(locations)

