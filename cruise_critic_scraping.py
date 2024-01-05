from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from datetime import datetime
import pandas as pd
import threading
import time
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchFrameException

# options = webdriver.ChromeOptions()
# options.add_experimental_option("detach", True)
# options.add_argument("--disable-popup-blocking")
# options.add_argument("--headless")
driver = webdriver.Firefox()
driver.fullscreen_window()


# This function serves as a helper function that scrapes the pricing/date combinations
def extract_date_and_room_options(date_and_room_div):
    try:
        print(date_and_room_div.get_property("innerHTML"))
        selector_tags = date_and_room_div.find_elements(By.TAG_NAME, "select")
        selectors = []
        for selector in selector_tags:
            selectors.append(Select(selector))
        # print(selectors)

        return selectors
    except Exception as e:
        print(e)
        return []


# This function  creates and returns a dataframe containing all relevant prices and other data for a single
# listing
def scrape_prices(price_divs,
                  room=None,
                  date=None,
                  number_of_nights=None,
                  cruise_type=None,
                  cruise_line=None,
                  ship=None,
                  url=None,
                  departure_port=None):
    try:
        print(len(price_divs))
        headers = {"Cabin_Type": [],
                   "Cruise_Name": [],
                   "Cruiseline": [],
                   "Departure_Date": [],
                   "Departure_Port": [],
                   "Destination": [],
                   "Pricing": [],
                   "Sailing_Length": [],
                   "ScrappingPage": [],
                   "Ship": [],
                   "TimeStamp": [],
                   "Vendor": []}
        cruise_type = cruise_type.replace("&amp;", "&")
        for price in price_divs:

            headers["Cabin_Type"].append(room)
            headers["Cruise_Name"].append(cruise_type)
            headers["Cruiseline"].append(cruise_line)
            headers["Ship"].append(ship)
            headers["Departure_Port"].append(departure_port)

            partner = price.find_element(By.TAG_NAME, "img").get_attribute('alt')
            value = price.find_element(By.CLASS_NAME, "css-13x77ht").get_property("innerHTML").replace("$", "") \
                .replace(",", "")
            parsed_date = datetime.strptime(date, "%b %d, %Y")
            departure_date = parsed_date.strftime("%-m/%-d/%Y")
            sailing_length = number_of_nights.split(" ")[0]
            timestamp_obj = datetime.today().date()
            timestamp = timestamp_obj.strftime("%-m/%-d/%Y")
            headers["Departure_Date"].append(departure_date)
            headers["Destination"].append(cruise_type)
            headers["Pricing"].append(value)
            headers["Sailing_Length"].append(sailing_length)
            headers["ScrappingPage"].append(url)
            headers["TimeStamp"].append(timestamp)
            headers["Vendor"].append(partner)

        df = pd.DataFrame(headers)

        return df
    except Exception as e:
        print(e)

        return False


# This function creates and returns a small dataframe with data from a listing div
def scrape_listing(listing_div, url=None):
    print(listing_div.get_property("innerHTML"))
    try:
        # FIND NUMBER OF NIGHT AND CRUISE NAME INFO
        h2_tags = listing_div.find_elements(By.TAG_NAME, "h2")
        cruise_line_div = listing_div.find_element(By.CLASS_NAME, "css-8h2eh6")
        cruise_line_button = cruise_line_div.find_element(By.TAG_NAME, "button")
        cruise_line = cruise_line_button.get_property("innerHTML")
        departure_port = listing_div.find_element(By.CLASS_NAME, "css-1avx2pl")
        port = departure_port.find_element(By.TAG_NAME, "button").get_property("innerHTML")

        def find_ship(div):
            buttons_div = div.find_element(By.TAG_NAME, "ul")
            buttons = buttons_div.find_elements(By.TAG_NAME, "li")
            ship_button = None
            for button in buttons:
                if "Ship" in button.get_property("innerHTML"):
                    ship_button = button
            if ship_button is not None:
                ship_button.click()
            else:
                return
            ship_div = div.find_element(By.CLASS_NAME, "css-ox9b8b")
            ship = ship_div.find_element(By.TAG_NAME, "h3").get_property("innerHTML")
            print(ship)
            return ship
        number_of_nights = ""
        cruise_type = ""
        for item in h2_tags:
            div_tags = item.find_elements(By.TAG_NAME, "div")
            number_of_nights = div_tags[0].get_property("innerHTML")
            cruise_type = div_tags[2].get_property("innerHTML").split("<")[0]

            print(number_of_nights)
            print(cruise_type)
            print()

        def find_all_prices(div):
            buttons_div = div.find_element(By.TAG_NAME, "ul")
            buttons = buttons_div.find_elements(By.TAG_NAME, "li")
            prices_button = None
            for button in buttons:
                print()
                if "View All Prices" in button.get_property("innerHTML"):
                    prices_button = button
            if prices_button is not None:
                print("About to click")

                prices_button.click()
                print("Button Clicked")
                return True
            else:
                return False

        cruise_ship = find_ship(listing_div)
        print(cruise_ship)
        if find_all_prices(listing_div):
            pricing_div = listing_div.find_element(By.CLASS_NAME, "css-1rgqn8m")
            prices = pricing_div.find_elements(By.CLASS_NAME, "css-1atdv2e")
            # this contains selectors (if available)
            # selectors will change and with each change scrape_prices will be called
            date_and_room_div = listing_div.find_element(By.CLASS_NAME, "css-1lthe3j")
            selectors = extract_date_and_room_options(date_and_room_div)
            if len(selectors) == 1:
                frames = []
                for selector in selectors:
                    for i in range(len(selector.options)):
                        selector.select_by_index(i)
                        if "," in selector.all_selected_options[0].get_property("innerHTML"):
                            date = selector.all_selected_options[0].get_property("innerHTML")
                            room = date_and_room_div.find_element(By.CLASS_NAME, "css-0").get_property("innerHTML")
                        else:
                            room = selector.all_selected_options[0].get_property("innerHTML")
                            print(room)
                            date = date_and_room_div.find_element(By.CLASS_NAME, "css-0").get_property("innerHTML")
                            print(date)
                        # re-evaluate prices on change before calling scrape_prices
                        pricing_div = listing_div.find_element(By.CLASS_NAME, "css-1rgqn8m")
                        prices = pricing_div.find_elements(By.CLASS_NAME, "css-1atdv2e")
                        df = scrape_prices(prices,
                                           date=date,
                                           room=room,
                                           number_of_nights=number_of_nights,
                                           cruise_type=cruise_type,
                                           cruise_line=cruise_line,
                                           ship=cruise_ship,
                                           url=url,
                                           departure_port=port)
                        frames.append(df)
                df = pd.concat(frames, ignore_index=True)
                print(df)
                return df
            elif len(selectors) == 2:
                frames = []
                print("there are two selectors")
                for i in range(len(selectors[0].options)):
                    selectors[0].select_by_index(i)
                    room = selectors[0].all_selected_options[0].get_property("innerHTML")
                    print(room)
                    for j in range(len(selectors[1].options)):
                        selectors[1].select_by_index(j)
                        date = selectors[1].all_selected_options[0].get_property("innerHTML")
                        print(date)
                        # re-evaluate prices on change before calling scrape_prices
                        pricing_div = listing_div.find_element(By.CLASS_NAME, "css-1rgqn8m")
                        prices = pricing_div.find_elements(By.CLASS_NAME, "css-1atdv2e")
                        df = scrape_prices(prices,
                                           date=date,
                                           room=room,
                                           number_of_nights=number_of_nights,
                                           cruise_type=cruise_type,
                                           cruise_line=cruise_line,
                                           ship=cruise_ship,
                                           url=url,
                                           departure_port=port)
                        frames.append(df)
                df = pd.concat(frames, ignore_index=True)
                print(df)
                return df
            else:
                room_and_date = date_and_room_div.find_elements(By.CLASS_NAME, "css-0")
                room = room_and_date[0].get_property("innerHTML")
                date = room_and_date[1].get_property("innerHTML")
                # print(f"{room} | {date}")
                df = scrape_prices(prices,
                                   date=date,
                                   room=room,
                                   number_of_nights=number_of_nights,
                                   cruise_type=cruise_type,
                                   cruise_line=cruise_line,
                                   ship=cruise_ship,
                                   url=url,
                                   departure_port=port)

                print(df)
                return df
        else:
            return False
    except ElementClickInterceptedException:
        # Handle specific case where click is intercepted
        print("Element is obscured. Handling popup.")
        time.sleep(2)
        try:

            driver.switch_to.frame("lightbox-iframe-5a6e2627-4470-403e-9c7b-52c4f7104bad")
            # iframe_html_source = driver.page_source
            # print(iframe_html_source)
            popup = driver.find_element(By.CLASS_NAME, "button5")
            popup.click()
            driver.switch_to.default_content()
            scrape_listing(listing_div, url=url)
        except NoSuchFrameException:
            print("Iframe not found.")
        except NoSuchElementException:
            print("Element inside iframe not found.")
        except Exception as e:
            print(e)
        time.sleep(1)

    except Exception as e:
        print("broke in here")
        print(e)
        print()


# this function facilitate passing each list div into the scrape listing function, which outputs a pandas
# dataframe for each listing. This function finally concatenates and returns a dataframe with a full page of data
def scrape_listings(listing_divs, url=None):
    try:
        frames = []
        for listing in listing_divs:
            try:
                df = scrape_listing(listing, url=url)
                if not isinstance(df, bool):


                    frames.append(df)

            except Exception as e:
                print(e)
                # modal_close = driver.find_element(By.CLASS_NAME, "sidebar-iframe-close")
                # modal_close.click()
                continue
        # print(frames)
        df = pd.concat(frames)

        print("listing data")
        return df
    except Exception as e:
        print(e)
        driver.quit()
        return False


# Function responsible for accessing cruise critic link with all cruises, and finding the listing Divs
# Function then takes a list of listing divs from each page and passes it into the scrape_listings function
def start_scraper():
    page = ""
    counter = 1
    frames = []
    # This number 5 can be changed to the total number of pages or code can be changed to run through pages until no more left
    while counter <= 5:
        url = f"https://www.cruisecritic.com/cruiseto/cruiseitineraries.cfm{page}"
        driver.get(url)
        # driver.fullscreen_window()

        # FIND ALL ELEMENTS THAT CONTAIN THIS DIV (LISTINGS)
        listings = driver.find_elements(by=By.CLASS_NAME, value="css-1ovjqqy")

        print(len(listings))

        df = scrape_listings(listings, url=url)
        if not isinstance(df, bool):
            print(df)
            frames.append(df)

        counter += 1
        page = f"?page={counter}"

        # scrape_listing(listings[0])
    df = pd.concat(frames, ignore_index=True)
    df.to_csv("test_scraping_2.csv", index=False)


start_scraper()

