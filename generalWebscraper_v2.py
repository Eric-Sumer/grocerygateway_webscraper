from selenium import webdriver
import math
import time
import csv

class GeneralWebscraper:
    def __init__(self, csvFileName):
        self.csvFileName = csvFileName
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_argument("--test-type")
        self.driver = webdriver.Chrome(executable_path="./chromedriver",options=self.options)

        self.fieldNames = ['UPC', 'Product Name', 'Category', 'Subcategory', 'In Stock', 'Price', 'Sale', 'Sale Price', 'Unit', 'Image Link', 'Description', 'Product Page Link']
        self.products = []


    def loadCategoryPage(self, url):
        #function loads the category page into the correct place and gets the list of product box elements
        self.driver.get(url)
        time.sleep(5)
        #get product boxes
        prodPerRefresh = 24
        showing_of_string_arr = self.driver.find_element_by_xpath("//div[@class='d-flex d-xl-none filters-items-counter']").text.split(" ")
        while not showing_of_string_arr:
            showing_of_string_arr = self.driver.find_element_by_xpath("//div[@class='d-flex d-xl-none filters-items-counter']").text.split(" ")
        totalProds = int(showing_of_string_arr[3])
        numPresses = math.ceil(max(0,totalProds-prodPerRefresh)/prodPerRefresh)
        for _ in range(numPresses):
            loadMoreBtn = self.driver.find_element_by_xpath("//button[@class='btn-black']")
            self.driver.execute_script("arguments[0].click()", loadMoreBtn)
            time.sleep(0.5)
        parentBoxes = self.driver.find_elements_by_xpath("//div[@class='product-list-item_img-holder text-center']")
        return [parentBox.find_element_by_tag_name("a").get_attribute("href") for parentBox in parentBoxes]
    
    def scrapeProductPage(self,url, category, parentCategory):
        self.driver.get(url)

        time.sleep(1)
        try : 
            productPageLink = url
            #title = self.driver.find_element_by_xpath("//h4[@class='font-weight-bold ng-star-inserted']").text
            title = self.driver.find_element_by_xpath("//img[@class='ng-tns-c404-0']").get_attribute("alt")
            upc = self.driver.find_element_by_xpath("//p[@class='product-code ng-star-inserted']").text #
            imageUrl = self.driver.find_element_by_xpath("//img[@class='ng-tns-c404-0']").get_attribute("src")
            unit = self.driver.find_element_by_xpath("//span[@class='measurement']").text.strip()[1:]

            #get product description
            prodDescriptionDropDownElement = self.driver.find_element_by_css_selector("[title*='Product information']")
            prodDescriptionTextElements = prodDescriptionDropDownElement.find_elements_by_xpath("//div[@class='ng-star-inserted']")
            description = " ".join([prodDesc.text for prodDesc in prodDescriptionTextElements if prodDesc.text!=""])

            #determine if out of stock
            inStock = self.driver.find_element_by_xpath("//button[@class='gg-btn primary']").text.lower()!="out of stock"

            #get price and sale
            saleElement = self.driver.find_elements_by_xpath("//p[@class='price actual with-discount ng-star-inserted']")
            if saleElement:
                sale = "True"
                originalPrice = self.driver.find_element_by_xpath("//p[@class='price regular ng-star-inserted']").text.strip()[1:]  
                salePrice = saleElement[0].find_element_by_xpath("//span[@class='font-weight-bold']").text[1:]+"."+\
                    saleElement[0].find_element_by_xpath("//span[@class='cents font-weight-bold']").text
            else:
                sale = "False"
                salePrice = "0"
                priceElement = self.driver.find_element_by_xpath("//p[@class='price actual ng-star-inserted']")
                originalPrice = priceElement.find_element_by_xpath("//span[@class='font-weight-bold']").text[1:]+"."+\
                    priceElement.find_element_by_xpath("//span[@class='cents font-weight-bold']").text

            return {
                'UPC':upc,
                'Product Name':title,
                "In Stock": inStock,
                "Price": originalPrice,
                "Sale": sale,
                "Sale Price": salePrice,
                "Unit": unit,
                "Image Link": imageUrl,
                "Description": description,
                "Product Page Link": productPageLink,
                "Category": parentCategory,
                "Subcategory": category
            }
        except Exception as e:
            print("Error occured for ", url)
            print("Continuing Run")
        

    def scapeCategoryPage(self, parentCat, subCat, url):
        productPageLinks = self.loadCategoryPage(url)

        for productPageLink in productPageLinks:
            listEle = self.scrapeProductPage(productPageLink, subCat, parentCat)
            if listEle != {}: self.products.append(listEle)

    def writeCSV(self):
        with open(self.csvFileName, mode='w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.fieldNames)

            writer.writeheader()
            for productDict in self.products:
                writer.writerow(productDict)

if __name__ == "__main__":
    csvFileName = "productList.csv"
    webScraper = GeneralWebscraper(csvFileName)
    lines = []
    with open('webscrapePages.txt') as f:
        lines = f.readlines()
    cnt = 0
    for line in lines:
        parentCat,subCat,url = line.split(",")
        print("Processing", url)
        webScraper.scapeCategoryPage(parentCat,subCat,url)
        if cnt >= 2: break
    webScraper.writeCSV()