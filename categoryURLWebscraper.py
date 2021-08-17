
from selenium import webdriver



def categoryURLWebscraper(url, textDoc): 
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--test-type")
    driver = webdriver.Chrome(executable_path="./chromedriver",options=options)
    driver.get(url)

    menuElements = driver.find_elements_by_class_name('link-page')
    menuElementLnks = set([element.get_attribute('href') for element in menuElements])

    with open (textDoc, 'w') as f:
        for line in menuElementLnks:
            f.write(line)
            f.write('\n')
    return
    

if __name__ == "__main__":
    homeURL = "https://www.grocerygateway.com/store/"
    textDoc='webscrapePages.txt'
    categoryURLWebscraper(homeURL, textDoc)
