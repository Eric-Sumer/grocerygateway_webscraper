from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
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
        self.timeout = 10
        self.fieldNames = ['UPC', 'Product Name', 'Category', 'Subcategory', 'In Stock', 'Price', 'Sale', 'Sale Price', 'Unit', 'Image Link', 'Description', 'Product Page Link']
        self.products = []
        self.csvPath = './CsvFiles/'


    def loadCategoryPage(self, url):
        #function loads the category page into the correct place and gets the list of product box elements
        try:
            self.driver.get(url)
            element_present = EC.presence_of_element_located((By.XPATH, "//div[@class='d-flex d-xl-none filters-items-counter']"))
            WebDriverWait(self.driver, self.timeout).until(element_present)
        except TimeoutException:
            print ("Timed out waiting for page to load")
            return []
        try: 
            #get product boxes
            prodPerRefresh = 24
            showing_of_string_arr = self.driver.find_element_by_xpath("//div[@class='d-flex d-xl-none filters-items-counter']").text.split(" ")
            totalProds = int(showing_of_string_arr[3])
            numPresses = math.ceil(max(0,totalProds-prodPerRefresh)/prodPerRefresh)
            for _ in range(numPresses):
                loadMoreBtn = self.driver.find_element_by_xpath("//button[@class='btn-black']")
                self.driver.execute_script("arguments[0].click()", loadMoreBtn)
                time.sleep(1)
            time.sleep(5)
            parentBoxes = self.driver.find_elements_by_xpath("//div[@class='product-list-item_img-holder text-center']")
            return [parentBox.find_element_by_tag_name("a").get_attribute("href") for parentBox in parentBoxes]
        except Exception as e:
            print("Error occured for category at url", url)
            print("Error is ", e)
            print("Continuing Run")
            return []
            

    def scrapeProductPage(self,url, category, parentCategory):
        try:
            self.driver.get(url)
            element_present = EC.presence_of_element_located((By.XPATH, "//img[@class='ng-tns-c404-0']"))
            WebDriverWait(self.driver, self.timeout).until(element_present)
        except Exception as e:
            print("Error occured when getting product page url", url)
            print("Error is ", e)
            print("Continuing Run")
            return {}
            
        try : 
            productPageLink = url
            title = self.driver.find_element_by_xpath("//img[@class='ng-tns-c404-0']").get_attribute("alt").strip()
            upc = self.driver.find_element_by_xpath("//p[@class='product-code ng-star-inserted']").get_attribute("textContent").split(":")[-1].strip()

            imageUrl = self.driver.find_element_by_xpath("//img[@class='ng-tns-c404-0']").get_attribute("src").strip()
            unit = self.driver.find_element_by_xpath("//span[@class='measurement']").get_attribute("textContent")[1:].strip()

            #get product description
            prodDescriptionDropDownElement = self.driver.find_element_by_css_selector("[title*='Product information']")
            prodDescriptionTextElements = prodDescriptionDropDownElement.find_elements_by_xpath("//div[@class='ng-star-inserted']")
            description = " ".join([prodDesc.get_attribute("textContent") for prodDesc in prodDescriptionTextElements if prodDesc.get_attribute("textContent")!=""])
            #clean description
            description = description.replace("\n", " ").strip()


            #determine if out of stock
            inStock = self.driver.find_element_by_xpath("//button[@class='gg-btn primary']").get_attribute("textContent").lower().strip()!="out of stock"

            #get price and sale
            saleElement = self.driver.find_elements_by_xpath("//p[@class='price actual with-discount ng-star-inserted']")
            if saleElement:
                sale = "True"
                originalPrice = self.driver.find_element_by_xpath("//p[@class='price regular ng-star-inserted']").get_attribute("textContent").strip()[1:]  
                salePrice = saleElement[0].find_element_by_xpath("//span[@class='font-weight-bold']").get_attribute("textContent")[1:]+"."+\
                    saleElement[0].find_element_by_xpath("//span[@class='cents font-weight-bold']").get_attribute("textContent")
            else:
                sale = "False"
                salePrice = "0"
                priceElement = self.driver.find_element_by_xpath("//p[@class='price actual ng-star-inserted']")
                originalPrice = priceElement.find_element_by_xpath("//span[@class='font-weight-bold']").get_attribute("textContent")[1:]+"."+\
                    priceElement.find_element_by_xpath("//span[@class='cents font-weight-bold']").get_attribute("textContent")

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
            print("Error occured for processing product page @", url)
            print("Error is ", e)
            print("Continuing Run")
            return {}
        
    def scrapeCategoryPage(self, parentCat, subCat, url):
        productPageLinks = self.loadCategoryPage(url)
        for productPageLink in productPageLinks:
            if type(productPageLink)!=str: continue
            listEle = self.scrapeProductPage(productPageLink, subCat, parentCat)
            if listEle != {} : self.products.append(listEle)
        self.writeCSV(parentCat,subCat)

    def writeCSV(self, parentCat, subCat):
        fileName = (self.csvPath+parentCat+"_"+subCat+".csv").replace(" ", "_")
        with open(fileName, 'w') as csvfile:
            filewriter = csv.DictWriter(csvfile, fieldnames=self.fieldNames)
            filewriter.writeheader()
            for productDict in self.products:
                if type(productDict)!= dict:
                    continue
                filewriter.writerow(productDict)

if __name__ == "__main__":
    csvFileName = "productList.csv"
    webScraper = GeneralWebscraper(csvFileName)
    lines = []
    with open('webscrapePages.txt') as f:
        lines = f.readlines()
    cnt = 0
    for line in lines:
        parentCat,subCat,url = line.split("|||")
        print("Processing", url)
        webScraper.scrapeCategoryPage(parentCat,subCat,url)
        break
    #webScraper.writeCSV()